import json
import time
import uuid
from dataclasses import dataclass
from urllib import error, parse, request

from fastapi import HTTPException, status

from app.ai.gemini_model_manager import GeminiModelManager
from app.ai.metrics import AIMetrics
from app.config.settings import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

FRIENDLY_TEMPORARY_ERROR = (
    "AI service is temporarily unavailable. Please try again shortly."
)
FRIENDLY_BUSY_ERROR = "AI service is temporarily busy."


@dataclass(frozen=True)
class GeminiRequestResult:
    body: str
    model: str
    retry_count: int
    request_id: str
    duration_ms: int


class GeminiProvider:
    retryable_statuses = {
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        status.HTTP_502_BAD_GATEWAY,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    permanent_model_failure_statuses = {
        status.HTTP_404_NOT_FOUND,
    }
    retry_delays_seconds = (1, 2, 4)

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.gemini_api_key
        self.timeout_seconds = settings.gemini_timeout_seconds
        self.model_manager = GeminiModelManager()

    def generate_json(self, prompt: str, threat_id: int | None = None) -> str:
        result = self.generate_json_result(prompt, threat_id)
        return result.body

    def generate_json_result(
        self,
        prompt: str,
        threat_id: int | None = None,
    ) -> GeminiRequestResult:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis is temporarily unavailable.",
            )

        payload = self._build_payload(prompt)
        request_id = str(uuid.uuid4())
        attempted_models: set[str] = set()
        model = self.model_manager.get_model()
        total_retry_count = 0
        started = time.perf_counter()
        AIMetrics.record_request_start()

        logger.info(
            "AI request start | request_id=%s threat_id=%s model=%s",
            request_id,
            threat_id,
            model,
        )

        while model:
            attempted_models.add(model)
            try:
                body, retry_count = self._generate_with_retries(
                    request_id,
                    threat_id,
                    model,
                    payload,
                )
                total_retry_count += retry_count
                duration_ms = self._elapsed_ms(started)
                logger.info(
                    "AI request success | request_id=%s threat_id=%s model=%s "
                    "retry_count=%s duration_ms=%s",
                    request_id,
                    threat_id,
                    model,
                    total_retry_count,
                    duration_ms,
                )
                AIMetrics.record_success(model, duration_ms)
                return GeminiRequestResult(
                    body=body,
                    model=model,
                    retry_count=total_retry_count,
                    request_id=request_id,
                    duration_ms=duration_ms,
                )
            except _GeminiQuotaExhausted:
                AIMetrics.record_failure(quota_exhausted=True)
                logger.warning(
                    "AI request failed due to quota exhaustion | request_id=%s "
                    "threat_id=%s model=%s retry_count=%s duration_ms=%s",
                    request_id,
                    threat_id,
                    model,
                    total_retry_count,
                    self._elapsed_ms(started),
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=FRIENDLY_TEMPORARY_ERROR,
                ) from None
            except _GeminiPermanentModelError:
                self.model_manager.invalidate_model(model)
                model = self.model_manager.switch_model(attempted_models)
                if model:
                    logger.warning(
                        "AI model switch | request_id=%s threat_id=%s next_model=%s",
                        request_id,
                        threat_id,
                        model,
                    )
            except _GeminiRetryableFailure as exc:
                total_retry_count += exc.retry_count
                model = self.model_manager.switch_model(attempted_models)
                if model:
                    logger.warning(
                        "AI fallback model selected | request_id=%s threat_id=%s "
                        "next_model=%s reason=%s",
                        request_id,
                        threat_id,
                        model,
                        exc.reason,
                    )

        AIMetrics.record_failure()
        logger.warning(
            "AI request failed | request_id=%s threat_id=%s retry_count=%s duration_ms=%s",
            request_id,
            threat_id,
            total_retry_count,
            self._elapsed_ms(started),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=FRIENDLY_BUSY_ERROR,
        )

    def _generate_with_retries(
        self,
        request_id: str,
        threat_id: int | None,
        model: str,
        payload: dict[str, object],
    ) -> tuple[str, int]:
        retry_count = 0

        for attempt_number in range(1, len(self.retry_delays_seconds) + 2):
            try:
                logger.info(
                    "Calling Gemini | request_id=%s threat_id=%s model=%s attempt=%s",
                    request_id,
                    threat_id,
                    model,
                    attempt_number,
                )
                return self._post_generate_content(
                    request_id,
                    threat_id,
                    model,
                    payload,
                ), retry_count
            except _GeminiRetryAfter as exc:
                retry_count += 1
                AIMetrics.record_retry()
                if attempt_number > len(self.retry_delays_seconds):
                    raise _GeminiRetryableFailure(
                        retry_count=retry_count,
                        reason="retry-after exhausted",
                    ) from exc
                logger.warning(
                    "RetryInfo honored | request_id=%s threat_id=%s model=%s "
                    "retry_delay_seconds=%s attempt=%s",
                    request_id,
                    threat_id,
                    model,
                    exc.delay_seconds,
                    attempt_number,
                )
                time.sleep(exc.delay_seconds)
            except _GeminiTimeoutError as exc:
                retry_count += 1
                if attempt_number > len(self.retry_delays_seconds):
                    raise _GeminiRetryableFailure(
                        retry_count=retry_count,
                        reason="timeout retries exhausted",
                    ) from exc
                self._sleep_fixed_backoff(
                    request_id,
                    threat_id,
                    model,
                    attempt_number,
                    "timeout",
                )
            except _GeminiRetryableFailure as exc:
                retry_count += 1
                if attempt_number > len(self.retry_delays_seconds):
                    raise _GeminiRetryableFailure(
                        retry_count=retry_count,
                        reason=exc.reason,
                    ) from exc
                self._sleep_fixed_backoff(
                    request_id,
                    threat_id,
                    model,
                    attempt_number,
                    exc.reason,
                )
            except _GeminiInvalidResponse as exc:
                retry_count += 1
                AIMetrics.record_retry()
                if attempt_number >= 2:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="AI analysis is temporarily unavailable.",
                    ) from exc
                logger.warning(
                    "Gemini response validation failed; retrying once | "
                    "request_id=%s threat_id=%s model=%s",
                    request_id,
                    threat_id,
                    model,
                )

        raise _GeminiRetryableFailure(retry_count=retry_count, reason="unknown")

    def _post_generate_content(
        self,
        request_id: str,
        threat_id: int | None,
        model: str,
        payload: dict[str, object],
    ) -> str:
        api_request = self._build_request(self._model_url(model), payload)
        request_started = time.perf_counter()
        logger.info(
            "Gemini request start | request_id=%s threat_id=%s model=%s",
            request_id,
            threat_id,
            model,
        )

        try:
            with request.urlopen(api_request, timeout=self.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
                if not response_body.strip():
                    logger.error(
                        "Gemini returned empty HTTP body | request_id=%s threat_id=%s "
                        "model=%s duration_ms=%s",
                        request_id,
                        threat_id,
                        model,
                        self._elapsed_ms(request_started),
                    )
                    raise _GeminiInvalidResponse
                logger.info(
                    "Gemini response received | request_id=%s threat_id=%s model=%s "
                    "duration_ms=%s",
                    request_id,
                    threat_id,
                    model,
                    self._elapsed_ms(request_started),
                )
                return self._extract_text(response_body)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            retry_delay_seconds = self._extract_retry_delay_seconds(detail)
            logger.exception(
                "Gemini API failed | request_id=%s threat_id=%s model=%s "
                "status=%s duration_ms=%s retry_delay_seconds=%s detail=%s",
                request_id,
                threat_id,
                model,
                exc.code,
                self._elapsed_ms(request_started),
                retry_delay_seconds,
                detail,
            )

            if self._is_quota_exhausted(exc.code, detail):
                raise _GeminiQuotaExhausted from exc
            if exc.code == status.HTTP_429_TOO_MANY_REQUESTS and retry_delay_seconds:
                raise _GeminiRetryAfter(retry_delay_seconds) from exc
            if self._is_permanent_model_failure(exc.code, detail):
                raise _GeminiPermanentModelError from exc
            if exc.code in self.retryable_statuses:
                raise _GeminiRetryableFailure(
                    retry_count=0,
                    reason=f"http_{exc.code}",
                ) from exc

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI analysis is temporarily unavailable.",
            ) from exc
        except TimeoutError as exc:
            logger.exception(
                "Gemini request failed | request_id=%s threat_id=%s model=%s "
                "duration_ms=%s reason=%s",
                request_id,
                threat_id,
                model,
                self._elapsed_ms(request_started),
                exc.__class__.__name__,
            )
            raise _GeminiTimeoutError from exc
        except _GeminiInvalidResponse:
            logger.exception(
                "Gemini response validation failed | request_id=%s threat_id=%s "
                "model=%s duration_ms=%s",
                request_id,
                threat_id,
                model,
                self._elapsed_ms(request_started),
            )
            raise
        except error.URLError as exc:
            logger.exception(
                "Gemini network failure | request_id=%s threat_id=%s model=%s "
                "duration_ms=%s reason=%s",
                request_id,
                threat_id,
                model,
                self._elapsed_ms(request_started),
                exc.reason,
            )
            raise _GeminiRetryableFailure(
                retry_count=0,
                reason="temporary network error",
            ) from exc

    def _extract_text(self, response_body: str) -> str:
        try:
            payload = json.loads(response_body)
            candidates = payload.get("candidates", [])
            first_candidate = candidates[0]
            parts = first_candidate["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            logger.exception("Gemini returned an unexpected response format")
            raise _GeminiInvalidResponse from exc

        if not text.strip():
            logger.error("Gemini returned an empty analysis")
            raise _GeminiInvalidResponse

        return text

    def _build_payload(self, prompt: str) -> dict[str, object]:
        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "responseMimeType": "application/json",
            },
        }

    def _model_url(self, model: str) -> str:
        clean_model = model.removeprefix("models/")
        return (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{clean_model}:generateContent?{parse.urlencode({'key': self.api_key})}"
        )

    def _build_request(self, url: str, payload: dict[str, object]) -> request.Request:
        return request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

    def _sleep_fixed_backoff(
        self,
        request_id: str,
        threat_id: int | None,
        model: str,
        attempt_number: int,
        reason: str,
    ) -> None:
        delay_seconds = self.retry_delays_seconds[attempt_number - 1]
        AIMetrics.record_retry()
        logger.warning(
            "Gemini retry scheduled | request_id=%s threat_id=%s model=%s "
            "retry_reason=%s retry_delay_seconds=%s attempt=%s",
            request_id,
            threat_id,
            model,
            reason,
            delay_seconds,
            attempt_number,
        )
        time.sleep(delay_seconds)

    def _extract_retry_delay_seconds(self, detail: str) -> float | None:
        try:
            payload = json.loads(detail)
        except json.JSONDecodeError:
            return None

        for item in payload.get("error", {}).get("details", []):
            if item.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                retry_delay = str(item.get("retryDelay") or "").strip()
                if retry_delay.endswith("s"):
                    try:
                        return float(retry_delay[:-1])
                    except ValueError:
                        return None
        return None

    def _is_quota_exhausted(self, status_code: int, detail: str) -> bool:
        if status_code != status.HTTP_429_TOO_MANY_REQUESTS:
            return False

        lowered_detail = detail.lower()
        quota_terms = (
            "resource_exhausted",
            "quota exceeded",
            "daily quota",
            "minute quota",
            "input token quota",
            "rate limit",
        )
        return any(term in lowered_detail for term in quota_terms)

    def _is_permanent_model_failure(self, status_code: int, detail: str) -> bool:
        if status_code in self.permanent_model_failure_statuses:
            return True

        lowered_detail = detail.lower()
        return status_code == status.HTTP_400_BAD_REQUEST and (
            "not supported for generatecontent" in lowered_detail
            or "model is not found" in lowered_detail
            or "models/" in lowered_detail and "generatecontent" in lowered_detail
        )

    def _elapsed_ms(self, started: float) -> int:
        return int((time.perf_counter() - started) * 1000)


class _GeminiPermanentModelError(Exception):
    """Raised when a Gemini model is incompatible or unavailable permanently."""


class _GeminiQuotaExhausted(Exception):
    """Raised when Gemini quota is exhausted and retries should stop."""


class _GeminiRetryAfter(Exception):
    """Raised when Gemini provides an explicit retry delay."""

    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = delay_seconds
        super().__init__(f"Retry after {delay_seconds} seconds")


class _GeminiRetryableFailure(Exception):
    """Raised when a Gemini request can be retried or switched to another model."""

    def __init__(self, retry_count: int, reason: str) -> None:
        self.retry_count = retry_count
        self.reason = reason
        super().__init__(reason)


class _GeminiTimeoutError(Exception):
    """Raised when a Gemini request times out."""


class _GeminiInvalidResponse(Exception):
    """Raised when Gemini returns an empty or malformed response envelope."""
