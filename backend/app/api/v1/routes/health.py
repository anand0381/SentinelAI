from fastapi import APIRouter

from app.config.settings import get_settings

router = APIRouter()


@router.get("")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.app_env,
    }
