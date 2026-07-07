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
    cve_id: str | None = None
    cvss_score: float | None = None
    published_date: datetime | None = None
    modified_date: datetime | None = None
    vendor_product: str | None = None
    source_feed: str | None = None
    reference_url: str | None = None
    tags: list[str] | None = None
    status: ThreatStatus
    confidence_score: float
    risk_score: float | None = None
    ai_summary: str | None = None
    attack_vector: str | None = None
    business_impact: str | None = None
    mitre_attack: list[str] | None = None
    recommendations: list[str] | None = None
    last_analyzed: datetime | None = None
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


class ThreatAnalysisResponse(BaseModel):
    threat_id: int
    ai_summary: str
    attack_vector: str
    business_impact: str
    mitre_attack: list[str]
    recommendations: list[str]
    confidence_score: float
    risk_score: float
    last_analyzed: datetime
