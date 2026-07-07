from dataclasses import dataclass, field
from datetime import datetime

from app.models.threat import ThreatCategory, ThreatSeverity, ThreatStatus


@dataclass(slots=True)
class NormalizedThreat:
    cve_id: str
    title: str
    description: str
    severity: ThreatSeverity
    source: str
    source_feed: str
    detected_at: datetime
    published_date: datetime | None = None
    modified_date: datetime | None = None
    cvss_score: float | None = None
    vendor_product: str | None = None
    reference_url: str | None = None
    tags: list[str] = field(default_factory=list)
    category: ThreatCategory = ThreatCategory.VULNERABILITY
    status: ThreatStatus = ThreatStatus.NEW
    confidence_score: float = 80

    def to_threat_payload(self) -> dict[str, object]:
        return {
            "title": self.title[:180],
            "description": self.description,
            "category": self.category,
            "severity": self.severity,
            "source": self.source[:120],
            "status": self.status,
            "confidence_score": self.confidence_score,
            "detected_at": self.detected_at,
            "cve_id": self.cve_id,
            "cvss_score": self.cvss_score,
            "published_date": self.published_date,
            "modified_date": self.modified_date,
            "vendor_product": self.vendor_product[:240] if self.vendor_product else None,
            "source_feed": self.source_feed,
            "reference_url": self.reference_url,
            "tags": self.tags,
        }
