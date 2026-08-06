from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.endpoint_activity import EndpointActivityListResponse
from app.services.endpoint_activity_service import EndpointActivityService
from app.utils.security import get_current_user

router = APIRouter()


@router.get(
    "",
    response_model=EndpointActivityListResponse,
    summary="List endpoint activity history",
)
def list_endpoint_activity(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> EndpointActivityListResponse:
    return EndpointActivityService(db).list_activity(page, page_size)
