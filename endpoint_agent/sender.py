"""Telemetry sender for SentinelAI endpoint agent."""

from __future__ import annotations

import logging
import time
import json
from http.client import HTTPConnection, HTTPSConnection, HTTPException
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class TelemetrySender:
    def __init__(
        self,
        backend_url: str,
        max_retries: int = 3,
        timeout_seconds: int = 15,
    ) -> None:
        self.backend_url = backend_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

    def emit(self, telemetry: dict[str, Any]) -> None:
        endpoint = f"{self.backend_url}/api/v1/telemetry"
        payload = json.dumps(telemetry).encode("utf-8")

        for attempt in range(1, self.max_retries + 1):
            try:
                status_code, response_body = self._post_json(endpoint, payload)

                if 200 <= status_code < 300:
                    logger.info(
                        "Telemetry sent successfully status=%s response=%s",
                        status_code,
                        response_body,
                    )
                    return

                if status_code >= 500 and attempt < self.max_retries:
                    self._sleep_before_retry(
                        attempt,
                        RuntimeError(f"Backend returned HTTP {status_code}"),
                    )
                    continue

                logger.warning(
                    "Telemetry rejected status=%s response=%s",
                    status_code,
                    response_body,
                )
                return
            except (TimeoutError, OSError, HTTPException, ValueError) as exc:
                if attempt < self.max_retries:
                    self._sleep_before_retry(attempt, exc)
                    continue

                logger.error(
                    "Telemetry backend unreachable after %s attempts: %s",
                    self.max_retries,
                    exc,
                )
                return

    def _post_json(self, endpoint: str, payload: bytes) -> tuple[int, str]:
        parsed_url = urlparse(endpoint)
        if parsed_url.scheme not in {"http", "https"}:
            raise ValueError(f"Unsupported backend URL scheme: {parsed_url.scheme}")

        connection_class = HTTPSConnection if parsed_url.scheme == "https" else HTTPConnection
        port = parsed_url.port
        connection = connection_class(
            parsed_url.hostname,
            port,
            timeout=self.timeout_seconds,
        )
        path = parsed_url.path or "/"
        if parsed_url.query:
            path = f"{path}?{parsed_url.query}"

        try:
            connection.request(
                "POST",
                path,
                body=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            response = connection.getresponse()
            response_body = response.read().decode("utf-8", errors="replace")
            return response.status, response_body
        finally:
            connection.close()

    @staticmethod
    def _sleep_before_retry(attempt: int, exc: Exception) -> None:
        delay_seconds = 2 ** (attempt - 1)
        logger.warning(
            "Telemetry send attempt %s failed: %s. Retrying in %ss",
            attempt,
            exc,
            delay_seconds,
        )
        time.sleep(delay_seconds)
