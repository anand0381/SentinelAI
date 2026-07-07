"""System telemetry collectors for the SentinelAI endpoint agent."""

from __future__ import annotations

import getpass
import logging
import platform
import socket
from datetime import datetime, timezone

import psutil

from endpoint_agent.config import AgentConfig
from endpoint_agent.models import (
    EndpointTelemetry,
    NetworkConnectionTelemetry,
    ProcessTelemetry,
)

logger = logging.getLogger(__name__)


def collect_endpoint_telemetry(config: AgentConfig) -> EndpointTelemetry:
    return EndpointTelemetry(
        agent_id=config.agent_id,
        backend_url=config.backend_url,
        hostname=socket.gethostname(),
        os_name=platform.system(),
        os_version=platform.version(),
        username=getpass.getuser(),
        cpu_usage_percent=_safe_cpu_usage(),
        memory_usage_percent=_safe_memory_usage(),
        disk_usage_percent=_safe_disk_usage(),
        running_processes=_collect_running_processes(),
        active_tcp_connections=_collect_active_tcp_connections(),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _safe_cpu_usage() -> float:
    try:
        return float(psutil.cpu_percent(interval=1))
    except Exception:
        logger.exception("Failed to collect CPU usage")
        return 0.0


def _safe_memory_usage() -> float:
    try:
        return float(psutil.virtual_memory().percent)
    except Exception:
        logger.exception("Failed to collect memory usage")
        return 0.0


def _safe_disk_usage() -> float:
    try:
        return float(psutil.disk_usage("/").percent)
    except Exception:
        logger.exception("Failed to collect disk usage")
        return 0.0


def _collect_running_processes() -> list[ProcessTelemetry]:
    processes: list[ProcessTelemetry] = []
    for process in psutil.process_iter(
        attrs=["pid", "name", "cpu_percent", "memory_percent"]
    ):
        try:
            info = process.info
            processes.append(
                ProcessTelemetry(
                    pid=int(info.get("pid") or 0),
                    name=str(info.get("name") or "unknown"),
                    cpu_percent=round(float(info.get("cpu_percent") or 0.0), 2),
                    memory_percent=round(float(info.get("memory_percent") or 0.0), 2),
                )
            )
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
        except Exception:
            logger.exception("Failed to collect process telemetry")
    return processes


def _collect_active_tcp_connections() -> list[NetworkConnectionTelemetry]:
    connections: list[NetworkConnectionTelemetry] = []
    try:
        raw_connections = psutil.net_connections(kind="tcp")
    except Exception:
        logger.exception("Failed to collect TCP network connections")
        return connections

    for connection in raw_connections:
        try:
            local_address = _format_address(connection.laddr)
            remote_address = (
                _format_address(connection.raddr) if connection.raddr else None
            )
            connections.append(
                NetworkConnectionTelemetry(
                    pid=connection.pid,
                    local_address=local_address,
                    remote_address=remote_address,
                    status=connection.status,
                )
            )
        except Exception:
            logger.exception("Failed to normalize TCP connection telemetry")
    return connections


def _format_address(address: object) -> str:
    if not address:
        return ""

    ip_address = getattr(address, "ip", None)
    port = getattr(address, "port", None)
    if ip_address is not None and port is not None:
        return f"{ip_address}:{port}"

    if isinstance(address, tuple) and len(address) >= 2:
        return f"{address[0]}:{address[1]}"

    return str(address)

