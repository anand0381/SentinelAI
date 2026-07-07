"""Configuration helpers for the SentinelAI endpoint agent."""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass


DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
DEFAULT_POLLING_INTERVAL_SECONDS = 30


@dataclass(frozen=True)
class AgentConfig:
    backend_url: str
    agent_id: str
    polling_interval_seconds: int


def _read_positive_int(value: str | None, default: int) -> int:
    if value is None:
        return default

    try:
        parsed_value = int(value)
    except ValueError:
        return default

    return parsed_value if parsed_value > 0 else default


def load_config() -> AgentConfig:
    hostname = socket.gethostname()
    backend_url = os.getenv("BACKEND_URL") or os.getenv(
        "SENTINEL_AGENT_BACKEND_URL",
        DEFAULT_BACKEND_URL,
    )
    return AgentConfig(
        backend_url=backend_url.rstrip("/"),
        agent_id=os.getenv("SENTINEL_AGENT_ID", hostname),
        polling_interval_seconds=_read_positive_int(
            os.getenv("SENTINEL_AGENT_POLLING_INTERVAL"),
            DEFAULT_POLLING_INTERVAL_SECONDS,
        ),
    )
