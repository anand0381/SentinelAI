from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.threat import ThreatCategory, ThreatSeverity, ThreatStatus


class ThreatBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=180)
    description: str = Field(..., min_length=10, max_length=5000)
    category: ThreatCategory
    severity: ThreatSeverity
    source: str = Field(..., min_length=2, max_length=120)
    status: ThreatStatus = ThreatStatus.NEW
    confidence_score: float = Field(..., ge=0, le=100)
    detected_at: datetime

    @field_validator("title", "description", "source")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class ThreatCreate(ThreatBase):
    """Payload required to create a threat record."""


class ThreatUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=180)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    category: ThreatCategory | None = None
    severity: ThreatSeverity | None = None
    source: str | None = Field(default=None, min_length=2, max_length=120)
    status: ThreatStatus | None = None
    confidence_score: float | None = Field(default=None, ge=0, le=100)
    detected_at: datetime | None = None

    @field_validator("title", "description", "source")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class ThreatResponse(BaseModel):
    id: int
    title: str
    description: str
    category: ThreatCategory
    severity: ThreatSeverity
    source: str
    status: ThreatStatus
    confidence_score: float
    detected_at: datetime
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ThreatFilter(BaseModel):
    category: ThreatCategory | None = None
    severity: ThreatSeverity | None = None
    status: ThreatStatus | None = None
    source: str | None = Field(default=None, max_length=120)


class ThreatListResponse(BaseModel):
    items: list[ThreatResponse]
    total: int
    page: int
    page_size: int
    pages: int
