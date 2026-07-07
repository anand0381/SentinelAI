from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import ChartData, DashboardSummary
from app.services.dashboard_service import DashboardService
from app.utils.security import get_current_user

router = APIRouter()


def get_dashboard_service(db: Session) -> DashboardService:
    return DashboardService(DashboardRepository(db))


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get dashboard summary metrics",
)
def summary(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> DashboardSummary:
    return get_dashboard_service(db).get_summary()


@router.get(
    "/threat-severity",
    response_model=ChartData,
    summary="Get threat severity chart data",
)
def threat_severity(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ChartData:
    return get_dashboard_service(db).get_threat_severity()


@router.get(
    "/threat-category",
    response_model=ChartData,
    summary="Get threat category chart data",
)
def threat_category(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ChartData:
    return get_dashboard_service(db).get_threat_category()


@router.get(
    "/incident-status",
    response_model=ChartData,
    summary="Get incident status chart data",
)
def incident_status(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ChartData:
    return get_dashboard_service(db).get_incident_status()


@router.get(
    "/monthly-trends",
    response_model=ChartData,
    summary="Get monthly trend chart data",
)
def monthly_trends(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ChartData:
    return get_dashboard_service(db).get_monthly_trends()
