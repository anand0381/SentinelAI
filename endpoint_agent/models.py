"""Typed telemetry models for the SentinelAI endpoint agent."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ProcessTelemetry:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float


@dataclass(frozen=True)
class NetworkConnectionTelemetry:
    pid: int | None
    local_address: str
    remote_address: str | None
    status: str


@dataclass(frozen=True)
class EndpointTelemetry:
    agent_id: str
    backend_url: str
    hostname: str
    os_name: str
    os_version: str
    username: str
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    running_processes: list[ProcessTelemetry]
    active_tcp_connections: list[NetworkConnectionTelemetry]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

