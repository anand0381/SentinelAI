from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.user import User
from app.repositories.incident_repository import IncidentRepository
from app.repositories.threat_repository import ThreatRepository
from app.schemas.incident import (
    IncidentCreate,
    IncidentListResponse,
    IncidentTimelineResponse,
    IncidentUpdate,
)


class IncidentService:
    def __init__(self, db: Session) -> None:
        self.incident_repository = IncidentRepository(db)
        self.threat_repository = ThreatRepository(db)

    def create_incident(
        self,
        payload: IncidentCreate,
        current_user: User,
    ) -> Incident:
        self._validate_related_threat(payload.related_threat_id)
        return self.incident_repository.create_incident(payload, current_user.id)

    def get_incident(self, incident_id: int) -> Incident:
        incident = self.incident_repository.get_incident_by_id(incident_id)

        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident was not found",
            )

        return incident

    def list_incidents(self, page: int, page_size: int) -> IncidentListResponse:
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

        items, total = self.incident_repository.paginate_results(
            self.incident_repository.get_all_incidents(),
            page,
            page_size,
        )
        pages = ceil(total / page_size) if total else 0
        return IncidentListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_timeline(self, incident_id: int) -> IncidentTimelineResponse:
        incident = self.get_incident(incident_id)
        timeline = sorted(incident.timeline or [], key=lambda item: item.get("timestamp", ""))
        return IncidentTimelineResponse(incident_id=incident.id, timeline=timeline)

    def update_incident(
        self,
        incident_id: int,
        payload: IncidentUpdate,
    ) -> Incident:
        incident = self.get_incident(incident_id)
        updates = payload.model_dump(exclude_unset=True)

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update",
            )

        if "related_threat_id" in updates:
            self._validate_related_threat(payload.related_threat_id)

        return self.incident_repository.update_incident(incident, payload)

    def delete_incident(self, incident_id: int) -> None:
        incident = self.get_incident(incident_id)
        self.incident_repository.delete_incident(incident)

    def _validate_related_threat(self, threat_id: int | None) -> None:
        if threat_id is None:
            return

        if self.threat_repository.get_threat_by_id(threat_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Related threat was not found",
            )
