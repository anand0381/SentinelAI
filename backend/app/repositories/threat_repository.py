from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.threat import Threat
from app.schemas.threat import ThreatCreate, ThreatFilter, ThreatUpdate


class ThreatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_threat(self, threat_data: ThreatCreate, created_by: int) -> Threat:
        threat = Threat(**threat_data.model_dump(), created_by=created_by)
        self.db.add(threat)
        self.db.commit()
        self.db.refresh(threat)
        return threat

    def get_threat_by_id(self, threat_id: int) -> Threat | None:
        return self.db.get(Threat, threat_id)

    def get_threat_by_cve_id(self, cve_id: str) -> Threat | None:
        return self.db.scalar(select(Threat).where(Threat.cve_id == cve_id))

    def get_all_threats(self) -> Select[tuple[Threat]]:
        return select(Threat).order_by(Threat.detected_at.desc(), Threat.id.desc())

    def update_threat(self, threat: Threat, threat_data: ThreatUpdate) -> Threat:
        updates = threat_data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(threat, field, value)

        self.db.add(threat)
        self.db.commit()
        self.db.refresh(threat)
        return threat

    def delete_threat(self, threat: Threat) -> None:
        self.db.delete(threat)
        self.db.commit()

    def save_analysis(self, threat: Threat) -> Threat:
        self.db.add(threat)
        self.db.commit()
        self.db.refresh(threat)
        return threat

    def create_imported_threat(self, payload: dict[str, object], created_by: int) -> Threat:
        threat = Threat(**payload, created_by=created_by)
        self.db.add(threat)
        self.db.commit()
        self.db.refresh(threat)
        return threat

    def update_imported_threat(
        self,
        threat: Threat,
        payload: dict[str, object],
    ) -> Threat:
        for field, value in payload.items():
            setattr(threat, field, value)

        self.db.add(threat)
        self.db.commit()
        self.db.refresh(threat)
        return threat

    def search_threats(self, query: str) -> Select[tuple[Threat]]:
        search_term = f"%{query.strip()}%"
        return (
            select(Threat)
            .where(
                or_(
                    Threat.title.ilike(search_term),
                    Threat.description.ilike(search_term),
                    Threat.source.ilike(search_term),
                )
            )
            .order_by(Threat.detected_at.desc(), Threat.id.desc())
        )

    def filter_threats(self, filters: ThreatFilter) -> Select[tuple[Threat]]:
        statement = self.get_all_threats()

        if filters.category:
            statement = statement.where(Threat.category == filters.category)
        if filters.severity:
            statement = statement.where(Threat.severity == filters.severity)
        if filters.status:
            statement = statement.where(Threat.status == filters.status)
        if filters.source:
            statement = statement.where(Threat.source.ilike(f"%{filters.source.strip()}%"))

        return statement

    def paginate_results(
        self,
        statement: Select[tuple[Threat]],
        page: int,
        page_size: int,
    ) -> tuple[list[Threat], int]:
        count_statement = select(func.count()).select_from(statement.subquery())
        total = self.db.scalar(count_statement) or 0
        items = self.db.scalars(
            statement.offset((page - 1) * page_size).limit(page_size)
        ).all()
        return list(items), total
