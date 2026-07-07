from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.threat_intelligence import (
    ThreatIntelligenceLatestResponse,
    ThreatIntelligenceStatus,
    ThreatIntelligenceSyncResult,
)
from app.services.threat_intelligence_service import ThreatIntelligenceService
from app.utils.security import get_current_user

router = APIRouter()


@router.get(
    "/latest",
    response_model=ThreatIntelligenceLatestResponse,
    summary="List latest imported threat intelligence",
)
def latest_threat_intelligence(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> ThreatIntelligenceLatestResponse:
    return ThreatIntelligenceService(db).latest(page, page_size)


@router.post(
    "/sync",
    response_model=ThreatIntelligenceSyncResult,
    summary="Sync public threat intelligence feeds",
)
async def sync_threat_intelligence(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int | None = Query(default=None, ge=1, le=100),
) -> ThreatIntelligenceSyncResult:
    return await ThreatIntelligenceService(db).sync(current_user, limit)


@router.get(
    "/status",
    response_model=ThreatIntelligenceStatus,
    summary="Get threat intelligence sync status",
)
def threat_intelligence_status(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ThreatIntelligenceStatus:
    return ThreatIntelligenceService(db).status()
