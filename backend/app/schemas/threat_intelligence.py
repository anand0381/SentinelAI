from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ThreatIntelligenceStatus(BaseModel):
    last_sync_at: datetime | None = None
    last_status: str = "NOT_STARTED"
    last_message: str | None = None
    imported_total: int = 0


class ThreatIntelligenceSyncResult(BaseModel):
    fetched: int = 0
    imported: int = 0
    updated: int = 0
    skipped_duplicates: int = 0
    analyzed: int = 0
    failed: int = 0
    duration_seconds: float = 0


class ImportedThreatResponse(BaseModel):
    id: int
    cve_id: str | None
    title: str
    severity: str
    cvss_score: float | None
    source_feed: str | None
    published_date: datetime | None
    modified_date: datetime | None
    vendor_product: str | None
    reference_url: str | None
    last_analyzed: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ThreatIntelligenceLatestResponse(BaseModel):
    items: list[ImportedThreatResponse]
    total: int
    page: int
    page_size: int
    pages: int
