from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ProcessTelemetryRequest(BaseModel):
    pid: int = Field(..., ge=0)
    name: str = Field(..., min_length=1, max_length=255)
    cpu_percent: float = Field(..., ge=0)
    memory_percent: float = Field(..., ge=0, le=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()


class NetworkConnectionTelemetryRequest(BaseModel):
    pid: int | None = Field(default=None, ge=0)
    local_address: str = Field(..., min_length=1, max_length=255)
    remote_address: str | None = Field(default=None, max_length=255)
    status: str = Field(..., min_length=1, max_length=64)

    @field_validator("local_address", "remote_address", "status")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class EndpointTelemetryRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=120)
    backend_url: str = Field(..., min_length=1, max_length=500)
    hostname: str = Field(..., min_length=1, max_length=255)
    os_name: str = Field(..., min_length=1, max_length=120)
    os_version: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=1, max_length=255)
    cpu_usage_percent: float = Field(..., ge=0, le=100)
    memory_usage_percent: float = Field(..., ge=0, le=100)
    disk_usage_percent: float = Field(..., ge=0, le=100)
    running_processes: list[ProcessTelemetryRequest]
    active_tcp_connections: list[NetworkConnectionTelemetryRequest]
    timestamp: datetime

    @field_validator(
        "agent_id",
        "backend_url",
        "hostname",
        "os_name",
        "os_version",
        "username",
    )
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return value.strip()


class TelemetryAcceptedResponse(BaseModel):
    status: str = "received"
    message: str = "Telemetry accepted"

