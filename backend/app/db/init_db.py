from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config.settings import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.incident import Incident
from app.models.threat import Threat, ThreatCategory, ThreatSeverity, ThreatStatus
from app.models.user import UserRole
from app.repositories.threat_repository import ThreatRepository
from app.repositories.user_repository import UserRepository
from app.schemas.threat import ThreatCreate
from app.schemas.user import UserCreate
from app.utils.logging import get_logger
from app.utils.security import hash_password

logger = get_logger(__name__)

DEFAULT_ADMIN_EMAIL = "admin@sentinelai.local"
DEFAULT_ADMIN_PASSWORD = "Admin@123"


def initialize_database() -> None:
    settings = get_settings()

    if settings.database_url.startswith("sqlite:///"):
        database_path = Path(settings.database_url.replace("sqlite:///", "", 1))
        database_path.parent.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)
    admin_id = create_default_admin()
    create_sample_threats(admin_id)
    logger.info("Database initialized")


def create_default_admin() -> int:
    db = SessionLocal()

    try:
        user_repository = UserRepository(db)
        existing_admin = user_repository.get_user_by_email(DEFAULT_ADMIN_EMAIL)

        if existing_admin:
            return existing_admin.id

        admin_data = UserCreate(
            full_name="SentinelAI Administrator",
            email=DEFAULT_ADMIN_EMAIL,
            password=DEFAULT_ADMIN_PASSWORD,
            role=UserRole.ADMIN,
        )
        user_repository.create_user(
            user_data=admin_data,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
        )
        admin = user_repository.get_user_by_email(DEFAULT_ADMIN_EMAIL)
        logger.info("Default administrator account created")
        return admin.id if admin else 1
    finally:
        db.close()


def create_sample_threats(admin_id: int) -> None:
    db = SessionLocal()

    try:
        has_threats = db.query(Threat.id).first()

        if has_threats:
            return

        repository = ThreatRepository(db)
        now = datetime.now(timezone.utc)
        samples = [
            ThreatCreate(
                title="Suspicious phishing campaign targeting staff",
                description=(
                    "Multiple users reported credential harvesting emails with "
                    "lookalike login pages and urgent password reset language."
                ),
                category=ThreatCategory.PHISHING,
                severity=ThreatSeverity.HIGH,
                source="Email Gateway",
                status=ThreatStatus.INVESTIGATING,
                confidence_score=87.5,
                detected_at=now - timedelta(hours=5),
            ),
            ThreatCreate(
                title="Ransomware indicator observed on endpoint",
                description=(
                    "Endpoint telemetry identified file rename patterns, suspicious "
                    "process spawning, and blocked encryption behavior."
                ),
                category=ThreatCategory.RANSOMWARE,
                severity=ThreatSeverity.CRITICAL,
                source="EDR",
                status=ThreatStatus.NEW,
                confidence_score=94.0,
                detected_at=now - timedelta(days=1),
            ),
            ThreatCreate(
                title="Public application vulnerability scan spike",
                description=(
                    "Web application firewall detected repeated probes for known "
                    "framework vulnerabilities from several external IP addresses."
                ),
                category=ThreatCategory.VULNERABILITY,
                severity=ThreatSeverity.MEDIUM,
                source="WAF",
                status=ThreatStatus.MITIGATED,
                confidence_score=76.0,
                detected_at=now - timedelta(days=2),
            ),
        ]

        for sample in samples:
            repository.create_threat(sample, admin_id)

        logger.info("Sample threat records created")
    finally:
        db.close()
