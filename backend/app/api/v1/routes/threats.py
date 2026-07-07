from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.threat import ThreatCategory, ThreatSeverity, ThreatStatus
from app.models.user import User
from app.schemas.threat import (
    ThreatCreate,
    ThreatFilter,
    ThreatListResponse,
    ThreatResponse,
    ThreatUpdate,
)
from app.services.threat_service import ThreatService
from app.utils.security import get_current_user

router = APIRouter()


@router.post(
    "",
    response_model=ThreatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a threat",
)
def create_threat(
    payload: ThreatCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ThreatResponse:
    return ThreatService(db).create_threat(payload, current_user)


@router.get(
    "",
    response_model=ThreatListResponse,
    summary="List threats with pagination",
)
def list_threats(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> ThreatListResponse:
    return ThreatService(db).list_threats(page, page_size)


@router.get(
    "/search",
    response_model=ThreatListResponse,
    summary="Search threats",
)
def search_threats(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    q: str = Query(..., min_length=2, description="Search title, description, source"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> ThreatListResponse:
    return ThreatService(db).search(q, page, page_size)


@router.get(
    "/filter",
    response_model=ThreatListResponse,
    summary="Filter threats",
)
def filter_threats(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    category: ThreatCategory | None = None,
    severity: ThreatSeverity | None = None,
    threat_status: ThreatStatus | None = Query(default=None, alias="status"),
    source: str | None = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> ThreatListResponse:
    filters = ThreatFilter(
        category=category,
        severity=severity,
        status=threat_status,
        source=source,
    )
    return ThreatService(db).filter_threats(filters, page, page_size)


@router.get(
    "/{threat_id}",
    response_model=ThreatResponse,
    summary="Get a threat by ID",
)
def get_threat(
    threat_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ThreatResponse:
    return ThreatService(db).get_threat(threat_id)


@router.put(
    "/{threat_id}",
    response_model=ThreatResponse,
    summary="Update a threat",
)
def update_threat(
    threat_id: int,
    payload: ThreatUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ThreatResponse:
    return ThreatService(db).update_threat(threat_id, payload, current_user)


@router.delete(
    "/{threat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a threat",
)
def delete_threat(
    threat_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    ThreatService(db).delete_threat(threat_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
