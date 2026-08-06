from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.incident import Incident, IncidentPriority, IncidentStatus
from app.models.threat import Threat, ThreatSeverity
from app.repositories.incident_repository import IncidentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.schemas.telemetry import EndpointTelemetryRequest
from app.services.endpoint_activity_service import EndpointActivityService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class IncidentCorrelationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.incident_repository = IncidentRepository(db)
        self.user_repository = UserRepository(db)
        self.endpoint_activity_service = EndpointActivityService(db)

    def correlate_threat(
        self,
        threat: Threat,
        telemetry: EndpointTelemetryRequest,
    ) -> Incident:
        event_time = self._as_utc(telemetry.timestamp)
        incident = self._find_matching_incident(threat, telemetry, event_time)

        if incident is None:
            incident = self._create_incident(threat, telemetry, event_time)
            logger.info("Incident created | incident_id=%s threat_id=%s", incident.id, threat.id)
        else:
            incident = self._attach_threat(incident, threat, telemetry, event_time)
            logger.info(
                "Threat correlated | incident_id=%s threat_id=%s",
                incident.id,
                threat.id,
            )

        self.endpoint_activity_service.update_activity(
            telemetry.hostname,
            telemetry.username,
            threat,
            incident,
            event_time,
        )
        return incident

    def record_ai_completed(
        self,
        threat: Threat,
        telemetry: EndpointTelemetryRequest,
    ) -> None:
        event_time = self._as_utc(datetime.now(timezone.utc))
        incident = self._find_incident_by_threat_id(threat.id, telemetry) or (
            self._find_matching_incident(threat, telemetry, event_time)
        )
        if incident is None:
            return

        self.add_timeline_event(
            incident,
            "AI analysis completed",
            f"AI analysis completed for threat {threat.id}.",
            event_time,
        )
        self.endpoint_activity_service.update_activity(
            telemetry.hostname,
            telemetry.username,
            threat,
            incident,
            event_time,
        )

    def _find_incident_by_threat_id(
        self,
        threat_id: int,
        telemetry: EndpointTelemetryRequest,
    ) -> Incident | None:
        statement = (
            select(Incident)
            .where(Incident.status != IncidentStatus.CLOSED)
            .where(Incident.affected_endpoint == telemetry.hostname)
            .where(Incident.affected_username == telemetry.username)
            .order_by(Incident.last_detected.desc())
        )
        for incident in self.db.scalars(statement).all():
            if threat_id in (incident.related_threat_ids or []):
                return incident
        return None

    def add_timeline_event(
        self,
        incident: Incident,
        event: str,
        details: str,
        event_time: datetime | None = None,
    ) -> Incident:
        timestamp = self._as_utc(event_time or datetime.now(timezone.utc)).isoformat()
        timeline = list(incident.timeline or [])
        timeline.append({"timestamp": timestamp, "event": event, "details": details})
        incident.timeline = sorted(timeline, key=lambda item: item["timestamp"])
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        logger.info("Timeline updated | incident_id=%s event=%s", incident.id, event)
        return incident

    def _find_matching_incident(
        self,
        threat: Threat,
        telemetry: EndpointTelemetryRequest,
        event_time: datetime,
    ) -> Incident | None:
        cutoff = event_time - timedelta(
            minutes=self.settings.incident_correlation_window_minutes
        )
        statement = (
            select(Incident)
            .where(Incident.status != IncidentStatus.CLOSED)
            .where(Incident.affected_endpoint == telemetry.hostname)
            .where(Incident.affected_username == telemetry.username)
            .where(Incident.last_detected >= cutoff)
            .order_by(Incident.last_detected.desc())
        )

        for incident in self.db.scalars(statement).all():
            if self._matches_category(threat, incident) and self._matches_severity(
                threat,
                incident,
            ):
                return incident
        return None

    def _create_incident(
        self,
        threat: Threat,
        telemetry: EndpointTelemetryRequest,
        event_time: datetime,
    ) -> Incident:
        admin = self.user_repository.get_user_by_email(self.settings.default_admin_email)
        if admin is None:
            raise HTTPException(
                status_code=500,
                detail="Default administrator account was not found.",
            )

        payload = IncidentCreate(
            title=f"Endpoint Incident - {telemetry.hostname}",
            description=self._summary_description(threat, telemetry, [threat.id]),
            status=IncidentStatus.OPEN,
            priority=self._priority_from_severity(threat.severity),
            assigned_to=None,
            related_threat_id=threat.id,
        )
        incident = self.incident_repository.create_incident(payload, admin.id)
        incident.related_threat_ids = [threat.id]
        incident.affected_endpoint = telemetry.hostname
        incident.affected_username = telemetry.username
        incident.correlation_key = self._correlation_key(threat, telemetry)
        incident.first_detected = event_time
        incident.last_detected = event_time
        incident.timeline = self._initial_timeline(threat, telemetry, event_time)
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        logger.info("Timeline updated | incident_id=%s event=Incident created", incident.id)
        return incident

    def _attach_threat(
        self,
        incident: Incident,
        threat: Threat,
        telemetry: EndpointTelemetryRequest,
        event_time: datetime,
    ) -> Incident:
        threat_ids = list(incident.related_threat_ids or [])
        if threat.id not in threat_ids:
            threat_ids.append(threat.id)

        previous_priority = incident.priority
        next_priority = self._highest_priority(
            incident.priority,
            self._priority_from_severity(threat.severity),
            self._escalated_priority(incident, threat, event_time),
        )

        payload = IncidentUpdate(
            description=self._summary_description(threat, telemetry, threat_ids),
            priority=next_priority,
            related_threat_id=incident.related_threat_id or threat.id,
        )
        incident = self.incident_repository.update_incident(incident, payload)
        incident.related_threat_ids = threat_ids
        incident.last_detected = event_time
        incident.correlation_key = self._correlation_key(threat, telemetry)
        incident = self.add_timeline_event(
            incident,
            "Threat correlated into incident",
            f"Threat {threat.id} correlated with severity {threat.severity.value}.",
            event_time,
        )

        if next_priority != previous_priority:
            incident = self.add_timeline_event(
                incident,
                "Incident severity escalated",
                f"Incident priority changed from {previous_priority.value} to {next_priority.value}.",
                event_time,
            )
            logger.info(
                "Severity escalated | incident_id=%s from=%s to=%s",
                incident.id,
                previous_priority.value,
                next_priority.value,
            )

        logger.info("Incident updated | incident_id=%s", incident.id)
        return incident

    def _initial_timeline(
        self,
        threat: Threat,
        telemetry: EndpointTelemetryRequest,
        event_time: datetime,
    ) -> list[dict[str, str]]:
        timestamp = event_time.isoformat()
        return [
            {
                "timestamp": timestamp,
                "event": "Endpoint telemetry received",
                "details": f"Telemetry received from {telemetry.hostname}.",
            },
            {
                "timestamp": timestamp,
                "event": "Threat created",
                "details": f"Threat {threat.id} created with severity {threat.severity.value}.",
            },
            {
                "timestamp": timestamp,
                "event": "Threat correlated into incident",
                "details": f"Threat {threat.id} opened this incident.",
            },
        ]

    def _summary_description(
        self,
        threat: Threat,
        telemetry: EndpointTelemetryRequest,
        threat_ids: list[int],
    ) -> str:
        highest = threat.severity.value
        ai_available = "Yes" if threat.last_analyzed and threat.ai_summary else "No"
        first_detected = telemetry.timestamp.isoformat()
        return (
            "Automatically correlated endpoint incident.\n\n"
            f"Affected Endpoint: {telemetry.hostname}\n"
            f"Username: {telemetry.username}\n"
            f"Related Threat Count: {len(threat_ids)}\n"
            f"Related Threat IDs: {', '.join(str(item) for item in threat_ids)}\n"
            f"Highest Severity: {highest}\n"
            f"Current Status: {IncidentStatus.OPEN.value}\n"
            f"First Detected: {first_detected}\n"
            f"Last Updated: {datetime.now(timezone.utc).isoformat()}\n"
            f"AI Analysis Available: {ai_available}\n"
        )

    def _matches_category(self, threat: Threat, incident: Incident) -> bool:
        if not incident.correlation_key:
            return True
        return f"category={threat.category.value}" in incident.correlation_key

    def _matches_severity(self, threat: Threat, incident: Incident) -> bool:
        return self._severity_rank(threat.severity) >= self._priority_rank(incident.priority)

    def _escalated_priority(
        self,
        incident: Incident,
        threat: Threat,
        event_time: datetime,
    ) -> IncidentPriority:
        if threat.severity != ThreatSeverity.HIGH:
            return incident.priority

        cutoff = event_time - timedelta(
            minutes=self.settings.incident_correlation_window_minutes
        )
        high_count = 1
        threat_ids = incident.related_threat_ids or []
        if threat_ids:
            high_count += (
                self.db.scalar(
                    select(func.count(Threat.id))
                    .where(Threat.id.in_(threat_ids))
                    .where(Threat.severity == ThreatSeverity.HIGH)
                    .where(Threat.created_at >= cutoff)
                )
                or 0
            )
        return IncidentPriority.CRITICAL if high_count >= 2 else incident.priority

    def _priority_from_severity(self, severity: ThreatSeverity) -> IncidentPriority:
        return IncidentPriority(severity.value)

    def _highest_priority(
        self,
        *priorities: IncidentPriority,
    ) -> IncidentPriority:
        return max(priorities, key=self._priority_rank)

    def _severity_rank(self, severity: ThreatSeverity) -> int:
        return {
            ThreatSeverity.LOW: 1,
            ThreatSeverity.MEDIUM: 2,
            ThreatSeverity.HIGH: 3,
            ThreatSeverity.CRITICAL: 4,
        }[severity]

    def _priority_rank(self, priority: IncidentPriority) -> int:
        return {
            IncidentPriority.LOW: 1,
            IncidentPriority.MEDIUM: 2,
            IncidentPriority.HIGH: 3,
            IncidentPriority.CRITICAL: 4,
        }[priority]

    def _correlation_key(
        self,
        threat: Threat,
        telemetry: EndpointTelemetryRequest,
    ) -> str:
        return (
            f"hostname={telemetry.hostname}|username={telemetry.username}|"
            f"category={threat.category.value}"
        )

    def _as_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
