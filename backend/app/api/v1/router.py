from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    dashboard,
    endpoint_activity,
    health,
    incidents,
    telemetry,
    threat_intelligence,
    threats,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(
    endpoint_activity.router,
    prefix="/endpoints/activity",
    tags=["Endpoint Activity"],
)
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incident Management"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
api_router.include_router(
    threat_intelligence.router,
    prefix="/threat-intelligence",
    tags=["Threat Intelligence"],
)
api_router.include_router(threats.router, prefix="/threats", tags=["Threat Management"])
