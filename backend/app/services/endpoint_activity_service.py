from datetime import datetime, timezone
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.endpoint_activity import EndpointActivity
from app.models.incident import Incident
from app.models.threat import Threat
from app.repositories.endpoint_activity_repository import EndpointActivityRepository
from app.schemas.endpoint_activity import EndpointActivityListResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)


class EndpointActivityService:
    def __init__(self, db: Session) -> None:
        self.repository = EndpointActivityRepository(db)

    def list_activity(self, page: int, page_size: int) -> EndpointActivityListResponse:
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than or equal to 1",
            )
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100",
            )

        items, total = self.repository.paginate_results(
            self.repository.get_all(),
            page,
            page_size,
        )
        pages = ceil(total / page_size) if total else 0
        return EndpointActivityListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def update_activity(
        self,
        hostname: str,
        username: str,
        threat: Threat,
        incident: Incident,
        event_time: datetime,
    ) -> EndpointActivity:
        activity = self.repository.get_by_hostname_username(hostname, username)
        if activity is None:
            activity = EndpointActivity(
                hostname=hostname,
                username=username,
                recent_threat_ids=[],
                related_incident_ids=[],
                detection_timestamps=[],
                ai_analysis_status="AI Pending",
                last_activity_at=event_time,
            )

        activity.recent_threat_ids = self._append_unique(activity.recent_threat_ids, threat.id)
        activity.related_incident_ids = self._append_unique(
            activity.related_incident_ids,
            incident.id,
        )
        activity.detection_timestamps = self._append_unique(
            activity.detection_timestamps,
            event_time.isoformat(),
            limit=50,
        )
        activity.ai_analysis_status = self._ai_status(threat)
        activity.last_activity_at = event_time

        saved = self.repository.save(activity)
        logger.info(
            "Endpoint history updated | hostname=%s username=%s threat_id=%s incident_id=%s",
            hostname,
            username,
            threat.id,
            incident.id,
        )
        return saved

    def _append_unique(
        self,
        values: list[int] | list[str] | None,
        value: int | str,
        limit: int = 20,
    ) -> list[int] | list[str]:
        next_values = list(values or [])
        if value in next_values:
            next_values.remove(value)
        next_values.insert(0, value)
        return next_values[:limit]

    def _ai_status(self, threat: Threat) -> str:
        if threat.last_analyzed and threat.ai_summary:
            return "AI Completed"
        if threat.source == "Endpoint Agent":
            return "AI Pending"
        return "AI Unavailable"

