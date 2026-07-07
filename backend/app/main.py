from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config.settings import get_settings
from app.db.init_db import initialize_database
from app.utils.logging import configure_logging, get_logger

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    initialize_database()
    logger.info("SentinelAI backend started")
    yield
    logger.info("SentinelAI backend stopped")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-Powered Cybersecurity Threat Intelligence Platform",
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["Root"])
def read_root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "message": "SentinelAI API is running",
        "docs": "/docs",
    }
