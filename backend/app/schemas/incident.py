from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.incident import IncidentPriority, IncidentStatus


class IncidentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=180)
    description: str = Field(..., min_length=10, max_length=5000)
    status: IncidentStatus = IncidentStatus.OPEN
    priority: IncidentPriority = IncidentPriority.MEDIUM
    assigned_to: str | None = Field(default=None, max_length=120)
    related_threat_id: int | None = Field(default=None, ge=1)

    @field_validator("title", "description", "assigned_to")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class IncidentCreate(IncidentBase):
    """Payload required to create an incident record."""


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=180)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    status: IncidentStatus | None = None
    priority: IncidentPriority | None = None
    assigned_to: str | None = Field(default=None, max_length=120)
    related_threat_id: int | None = Field(default=None, ge=1)

    @field_validator("title", "description", "assigned_to")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str
    status: IncidentStatus
    priority: IncidentPriority
    assigned_to: str | None
    related_threat_id: int | None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    total: int
    page: int
    page_size: int
    pages: int
