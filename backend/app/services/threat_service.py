from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import Select
from sqlalchemy.orm import Session

from app.ai.ai_service import AIService
from app.models.threat import Threat
from app.models.user import User, UserRole
from app.repositories.threat_repository import ThreatRepository
from app.schemas.threat import (
    ThreatCreate,
    ThreatFilter,
    ThreatListResponse,
    ThreatUpdate,
)


class ThreatService:
    def __init__(self, db: Session) -> None:
        self.threat_repository = ThreatRepository(db)

    def create_threat(self, payload: ThreatCreate, current_user: User) -> Threat:
        return self.threat_repository.create_threat(payload, current_user.id)

    def get_threat(self, threat_id: int) -> Threat:
        threat = self.threat_repository.get_threat_by_id(threat_id)

        if threat is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Threat was not found",
            )

        return threat

    def list_threats(self, page: int, page_size: int) -> ThreatListResponse:
        return self._paginate(self.threat_repository.get_all_threats(), page, page_size)

    def search(self, query: str, page: int, page_size: int) -> ThreatListResponse:
        clean_query = query.strip()

        if len(clean_query) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must contain at least 2 characters",
            )

        return self._paginate(
            self.threat_repository.search_threats(clean_query),
            page,
            page_size,
        )

    def filter_threats(
        self,
        filters: ThreatFilter,
        page: int,
        page_size: int,
    ) -> ThreatListResponse:
        return self._paginate(
            self.threat_repository.filter_threats(filters),
            page,
            page_size,
        )

    def update_threat(
        self,
        threat_id: int,
        payload: ThreatUpdate,
        current_user: User,
    ) -> Threat:
        threat = self.get_threat(threat_id)
        self._ensure_can_modify(threat, current_user)

        if not payload.model_dump(exclude_unset=True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update",
            )

        return self.threat_repository.update_threat(threat, payload)

    def delete_threat(self, threat_id: int, current_user: User) -> None:
        threat = self.get_threat(threat_id)
        self._ensure_can_modify(threat, current_user)
        self.threat_repository.delete_threat(threat)

    def analyze_threat(self, threat_id: int) -> Threat:
        threat = self.get_threat(threat_id)
        ai_service = AIService()
        analysis = ai_service.analyze_threat(threat)
        ai_service.apply_analysis(threat, analysis)
        return self.threat_repository.save_analysis(threat)

    def _paginate(
        self,
        statement: Select[tuple[Threat]],
        page: int,
        page_size: int,
    ) -> ThreatListResponse:
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

        items, total = self.threat_repository.paginate_results(statement, page, page_size)
        pages = ceil(total / page_size) if total else 0

        return ThreatListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def _ensure_can_modify(self, threat: Threat, current_user: User) -> None:
        if current_user.role == UserRole.ADMIN:
            return

        if current_user.role == UserRole.ANALYST and threat.created_by == current_user.id:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this threat",
        )
