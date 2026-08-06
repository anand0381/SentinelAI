from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EndpointActivity(Base):
    __tablename__ = "endpoint_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    recent_threat_ids: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    related_incident_ids: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    detection_timestamps: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    ai_analysis_status: Mapped[str] = mapped_column(String(40), default="AI Pending", nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
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
