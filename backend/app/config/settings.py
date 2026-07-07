from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SentinelAI"
    app_env: str = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./database/sentinel.db"

    secret_key: str = "CHANGE_ME_SECRET_KEY"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_seconds: int = 60
    gemini_allow_gemma_models: bool = False
    default_admin_email: str = "admin@sentinelai.local"
    default_admin_password: str = "CHANGE_ME_ADMIN_PASSWORD"
    threat_intel_sync_limit: int = 20
    threat_intel_timeout_seconds: int = 30
    nvd_api_url: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    cisa_kev_url: str = (
        "https://www.cisa.gov/sites/default/files/feeds/"
        "known_exploited_vulnerabilities.json"
    )

    backend_cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173"
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
