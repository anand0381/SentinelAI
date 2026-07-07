from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.incident import (
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdate,
)
from app.services.incident_service import IncidentService
from app.utils.security import get_current_user

router = APIRouter()


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an incident",
)
def create_incident(
    payload: IncidentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> IncidentResponse:
    return IncidentService(db).create_incident(payload, current_user)


@router.get(
    "",
    response_model=IncidentListResponse,
    summary="List incidents with pagination",
)
def list_incidents(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> IncidentListResponse:
    return IncidentService(db).list_incidents(page, page_size)


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get an incident by ID",
)
def get_incident(
    incident_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> IncidentResponse:
    return IncidentService(db).get_incident(incident_id)


@router.put(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Update an incident",
)
def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> IncidentResponse:
    return IncidentService(db).update_incident(incident_id, payload)


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an incident",
)
def delete_incident(
    incident_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Response:
    IncidentService(db).delete_incident(incident_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
