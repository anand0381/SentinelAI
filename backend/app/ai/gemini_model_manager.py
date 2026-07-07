import json
from threading import Lock
from urllib import error, parse, request

from fastapi import HTTPException, status

from app.config.settings import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class GeminiModelManager:
    blocked_name_terms = (
        "tts",
        "audio",
        "embedding",
        "image",
        "vision",
        "live",
        "preview",
        "preview-tts",
        "speech",
    )
    gemma_name_terms = ("gemma",)
    preferred_models = (
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-flash-latest",
    )

    _cached_model: str | None = None
    _compatible_models: list[str] = []
    _lock = Lock()

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.gemini_api_key
        self.timeout_seconds = settings.gemini_timeout_seconds
        self.allow_gemma_models = settings.gemini_allow_gemma_models

    @classmethod
    def initialize_cache(cls) -> None:
        manager = cls()
        if not manager.api_key:
            logger.warning("Gemini model cache was not initialized because API key is missing")
            return

        try:
            manager.get_model()
        except HTTPException:
            logger.exception("Gemini model cache initialization failed")

    def get_model(self) -> str:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis is temporarily unavailable.",
            )

        with self._lock:
            if self.__class__._cached_model:
                logger.info("Using cached Gemini model: %s", self.__class__._cached_model)
                return self.__class__._cached_model

            return self._discover_and_cache_model(exclude=set())

    def invalidate_model(self, model: str) -> None:
        clean_model = self._clean_model_name(model)

        with self._lock:
            if self.__class__._cached_model == clean_model:
                logger.warning("Invalidating cached Gemini model: %s", clean_model)
                self.__class__._cached_model = None

            self.__class__._compatible_models = [
                item for item in self.__class__._compatible_models if item != clean_model
            ]

    def switch_model(self, failed_models: set[str]) -> str | None:
        clean_failed_models = {self._clean_model_name(model) for model in failed_models}

        with self._lock:
            for model in self.__class__._compatible_models:
                if model not in clean_failed_models:
                    self.__class__._cached_model = model
                    logger.warning("Switched Gemini model to cached compatible model: %s", model)
                    return model

            try:
                return self._discover_and_cache_model(exclude=clean_failed_models)
            except HTTPException:
                return None

    def _discover_and_cache_model(self, exclude: set[str]) -> str:
        logger.info("Discovering compatible Gemini text models")
        models = self._list_models()
        compatible_models = [
            model
            for model in models
            if self._is_compatible_text_model(model)
            and self._clean_model_name(str(model.get("name", ""))) not in exclude
        ]
        ordered_models = self._order_models(compatible_models)

        if not ordered_models:
            logger.error("No compatible Gemini text model was found")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis is temporarily unavailable.",
            )

        self.__class__._compatible_models = ordered_models
        self.__class__._cached_model = ordered_models[0]
        logger.info("Selected Gemini model: %s", self.__class__._cached_model)
        return self.__class__._cached_model

    def _list_models(self) -> list[dict[str, object]]:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models?"
            f"{parse.urlencode({'key': self.api_key})}"
        )
        api_request = request.Request(url=url, method="GET")

        try:
            with request.urlopen(api_request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            logger.exception("Gemini models.list failed: %s", detail)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis is temporarily unavailable.",
            ) from exc
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.exception("Gemini models.list could not be completed")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis is temporarily unavailable.",
            ) from exc

        models = payload.get("models", [])
        return models if isinstance(models, list) else []

    def _is_compatible_text_model(self, model: dict[str, object]) -> bool:
        name = self._clean_model_name(str(model.get("name", ""))).lower()
        methods = model.get("supportedGenerationMethods", [])
        output_modalities = model.get("supportedOutputModalities") or model.get(
            "outputModalities"
        )

        if not name:
            return False
        if any(term in name for term in self.blocked_name_terms):
            return False
        if not self.allow_gemma_models and any(
            term in name for term in self.gemma_name_terms
        ):
            return False
        if "generateContent" not in methods:
            return False
        if output_modalities and "TEXT" not in output_modalities:
            return False

        return True

    def _order_models(self, models: list[dict[str, object]]) -> list[str]:
        available = [self._clean_model_name(str(model.get("name", ""))) for model in models]
        ordered = [model for model in self.preferred_models if model in available]
        ordered.extend(model for model in available if model not in ordered)
        return ordered

    def _clean_model_name(self, model_name: str) -> str:
        return model_name.removeprefix("models/")
