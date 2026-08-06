from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class IncidentPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[IncidentStatus] = mapped_column(
        SQLAlchemyEnum(IncidentStatus, name="incident_status"),
        default=IncidentStatus.OPEN,
        nullable=False,
        index=True,
    )
    priority: Mapped[IncidentPriority] = mapped_column(
        SQLAlchemyEnum(IncidentPriority, name="incident_priority"),
        default=IncidentPriority.MEDIUM,
        nullable=False,
        index=True,
    )
    assigned_to: Mapped[str | None] = mapped_column(String(120), nullable=True)
    related_threat_id: Mapped[int | None] = mapped_column(
        ForeignKey("threats.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    related_threat_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    affected_endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    affected_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    correlation_key: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    first_detected: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_detected: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timeline: Mapped[list[dict[str, str]] | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    creator = relationship("User")
    related_threat = relationship("Threat")

    @property
    def related_threat_count(self) -> int:
        return len(self.related_threat_ids or ([] if self.related_threat_id is None else [self.related_threat_id]))

    @property
    def ai_analysis_available(self) -> bool:
        if self.timeline:
            return any(item.get("event") == "AI analysis completed" for item in self.timeline)
        return False
