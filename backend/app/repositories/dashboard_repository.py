from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.incident import Incident, IncidentPriority, IncidentStatus
from app.models.threat import Threat, ThreatSeverity


class DashboardRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def count_threats(self) -> int:
        return self.db.scalar(select(func.count()).select_from(Threat)) or 0

    def count_incidents(self) -> int:
        return self.db.scalar(select(func.count()).select_from(Incident)) or 0

    def count_critical_threats(self) -> int:
        return (
            self.db.scalar(
                select(func.count()).where(Threat.severity == ThreatSeverity.CRITICAL)
            )
            or 0
        )

    def count_open_incidents(self) -> int:
        return (
            self.db.scalar(
                select(func.count()).where(Incident.status == IncidentStatus.OPEN)
            )
            or 0
        )

    def count_high_priority_incidents(self) -> int:
        return (
            self.db.scalar(
                select(func.count()).where(
                    Incident.priority.in_(
                        [IncidentPriority.HIGH, IncidentPriority.CRITICAL]
                    )
                )
            )
            or 0
        )

    def count_active_incidents(self) -> int:
        return (
            self.db.scalar(
                select(func.count()).where(
                    Incident.status.in_(
                        [IncidentStatus.OPEN, IncidentStatus.INVESTIGATING]
                    )
                )
            )
            or 0
        )

    def count_correlated_incidents(self) -> int:
        return (
            self.db.scalar(
                select(func.count()).where(Incident.related_threat_ids.is_not(None))
            )
            or 0
        )

    def average_threats_per_incident(self) -> float:
        incidents = self.db.scalars(
            select(Incident).where(Incident.related_threat_ids.is_not(None))
        ).all()
        if not incidents:
            return 0.0

        total = sum(len(incident.related_threat_ids or []) for incident in incidents)
        return round(total / len(incidents), 2)

    def most_affected_endpoint(self) -> str | None:
        row = self.db.execute(
            select(Incident.affected_endpoint, func.count(Incident.id))
            .where(Incident.affected_endpoint.is_not(None))
            .group_by(Incident.affected_endpoint)
            .order_by(func.count(Incident.id).desc())
            .limit(1)
        ).first()
        return str(row[0]) if row else None

    def threat_counts_by_severity(self) -> list[tuple[str, int]]:
        return list(
            self.db.execute(
                select(Threat.severity, func.count(Threat.id))
                .group_by(Threat.severity)
                .order_by(Threat.severity)
            ).all()
        )

    def threat_counts_by_category(self) -> list[tuple[str, int]]:
        return list(
            self.db.execute(
                select(Threat.category, func.count(Threat.id))
                .group_by(Threat.category)
                .order_by(Threat.category)
            ).all()
        )

    def incident_counts_by_status(self) -> list[tuple[str, int]]:
        return list(
            self.db.execute(
                select(Incident.status, func.count(Incident.id))
                .group_by(Incident.status)
                .order_by(Incident.status)
            ).all()
        )

    def monthly_threat_counts(self) -> list[tuple[str, int]]:
        return list(
            self.db.execute(
                select(func.strftime("%Y-%m", Threat.created_at), func.count(Threat.id))
                .group_by(func.strftime("%Y-%m", Threat.created_at))
                .order_by(func.strftime("%Y-%m", Threat.created_at))
            ).all()
        )

    def monthly_incident_counts(self) -> list[tuple[str, int]]:
        return list(
            self.db.execute(
                select(
                    func.strftime("%Y-%m", Incident.created_at),
                    func.count(Incident.id),
                )
                .group_by(func.strftime("%Y-%m", Incident.created_at))
                .order_by(func.strftime("%Y-%m", Incident.created_at))
            ).all()
        )
