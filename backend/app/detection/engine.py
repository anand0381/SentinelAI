import time
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.ai_service import AIService
from app.config.settings import get_settings
from app.detection.evaluator import DetectionEvaluator
from app.detection.models import DetectionResult
from app.detection.rules import DetectionRules
from app.models.threat import Threat, ThreatCategory, ThreatSeverity, ThreatStatus
from app.repositories.threat_repository import ThreatRepository
from app.repositories.user_repository import UserRepository
from app.schemas.telemetry import EndpointTelemetryRequest
from app.schemas.threat import ThreatCreate, ThreatUpdate
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DetectionEngine:
    source = "Endpoint Agent"

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.rules = DetectionRules(self.settings)
        self.evaluator = DetectionEvaluator()
        self.threat_repository = ThreatRepository(db)
        self.user_repository = UserRepository(db)

    def process(self, telemetry: EndpointTelemetryRequest) -> DetectionResult:
        started = time.perf_counter()
        logger.info("Detection started | hostname=%s", telemetry.hostname)

        matches = self.rules.evaluate(telemetry)
        result = self.evaluator.evaluate(telemetry, matches)
        logger.info(
            "Rules triggered | hostname=%s rules=%s severity=%s",
            telemetry.hostname,
            [match.rule_id for match in matches],
            result.severity.value if result.severity else "NONE",
        )

        if result.should_create_threat:
            existing_threat = self._find_duplicate(telemetry, result)
            if existing_threat:
                self._update_existing_threat(existing_threat, telemetry, result)
                logger.info(
                    "Duplicate suppressed; existing threat updated | threat_id=%s",
                    existing_threat.id,
                )
            else:
                threat = self._create_threat(telemetry, result)
                logger.info("Threat created | threat_id=%s", threat.id)
                self._analyze_new_threat(threat)

        logger.info(
            "Detection completed | hostname=%s duration_ms=%s",
            telemetry.hostname,
            int((time.perf_counter() - started) * 1000),
        )
        return result

    def _create_threat(
        self,
        telemetry: EndpointTelemetryRequest,
        result: DetectionResult,
    ) -> Threat:
        admin_user = self.user_repository.get_user_by_email(
            self.settings.default_admin_email
        )
        if admin_user is None:
            raise HTTPException(
                status_code=500,
                detail="Default administrator account was not found.",
            )

        payload = ThreatCreate(
            title=result.title or "Suspicious Endpoint Activity Detected",
            description=result.description or "Endpoint activity requires review.",
            category=ThreatCategory.OTHER,
            severity=result.severity or ThreatSeverity.HIGH,
            source=self.source,
            status=ThreatStatus.NEW,
            confidence_score=self._confidence_score(result),
            detected_at=telemetry.timestamp,
        )
        return self.threat_repository.create_threat(payload, admin_user.id)

    def _update_existing_threat(
        self,
        threat: Threat,
        telemetry: EndpointTelemetryRequest,
        result: DetectionResult,
    ) -> Threat:
        payload = ThreatUpdate(
            description=result.description,
            severity=result.severity,
            confidence_score=max(threat.confidence_score, self._confidence_score(result)),
            detected_at=telemetry.timestamp,
        )
        updated_threat = self.threat_repository.update_threat(threat, payload)
        logger.info(
            "Threat updated | threat_id=%s hostname=%s",
            updated_threat.id,
            telemetry.hostname,
        )
        return updated_threat

    def _find_duplicate(
        self,
        telemetry: EndpointTelemetryRequest,
        result: DetectionResult,
    ) -> Threat | None:
        if result.severity is None:
            return None

        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=self.settings.detection_duplicate_window_minutes
        )
        statement = (
            select(Threat)
            .where(Threat.source == self.source)
            .where(Threat.severity == result.severity)
            .where(Threat.status != ThreatStatus.CLOSED)
            .where(Threat.updated_at >= cutoff)
            .where(Threat.description.contains(f"Detection Hostname: {telemetry.hostname}"))
            .where(Threat.description.contains(f"Detection Rule Set: {result.rule_set_key}"))
            .order_by(Threat.updated_at.desc())
        )
        return self.db.scalars(statement).first()

    def _analyze_new_threat(self, threat: Threat) -> None:
        logger.info("AI analysis started | threat_id=%s", threat.id)
        try:
            ai_service = AIService()
            analysis = ai_service.analyze_threat(threat)
            ai_service.apply_analysis(threat, analysis)
            self.threat_repository.save_analysis(threat)
            logger.info("AI analysis completed | threat_id=%s", threat.id)
        except HTTPException:
            logger.exception("AI analysis failed | threat_id=%s", threat.id)
        except Exception:
            logger.exception("Unexpected AI analysis failure | threat_id=%s", threat.id)

    def _confidence_score(self, result: DetectionResult) -> float:
        if result.severity == ThreatSeverity.CRITICAL:
            return 95.0
        if result.severity == ThreatSeverity.HIGH:
            return 85.0
        if result.severity == ThreatSeverity.MEDIUM:
            return 70.0
        return 60.0

