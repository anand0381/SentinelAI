from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate


class IncidentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_incident(
        self,
        incident_data: IncidentCreate,
        created_by: int,
    ) -> Incident:
        incident = Incident(**incident_data.model_dump(), created_by=created_by)
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def get_incident_by_id(self, incident_id: int) -> Incident | None:
        return self.db.get(Incident, incident_id)

    def get_all_incidents(self) -> Select[tuple[Incident]]:
        return select(Incident).order_by(Incident.created_at.desc(), Incident.id.desc())

    def update_incident(
        self,
        incident: Incident,
        incident_data: IncidentUpdate,
    ) -> Incident:
        updates = incident_data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(incident, field, value)

        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def delete_incident(self, incident: Incident) -> None:
        self.db.delete(incident)
        self.db.commit()

    def paginate_results(
        self,
        statement: Select[tuple[Incident]],
        page: int,
        page_size: int,
    ) -> tuple[list[Incident], int]:
        count_statement = select(func.count()).select_from(statement.subquery())
        total = self.db.scalar(count_statement) or 0
        items = self.db.scalars(
            statement.offset((page - 1) * page_size).limit(page_size)
        ).all()
        return list(items), total
