from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.endpoint_activity import EndpointActivity


class EndpointActivityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_hostname_username(
        self,
        hostname: str,
        username: str,
    ) -> EndpointActivity | None:
        return self.db.scalar(
            select(EndpointActivity).where(
                EndpointActivity.hostname == hostname,
                EndpointActivity.username == username,
            )
        )

    def get_all(self) -> Select[tuple[EndpointActivity]]:
        return select(EndpointActivity).order_by(EndpointActivity.last_activity_at.desc())

    def save(self, activity: EndpointActivity) -> EndpointActivity:
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def paginate_results(
        self,
        statement: Select[tuple[EndpointActivity]],
        page: int,
        page_size: int,
    ) -> tuple[list[EndpointActivity], int]:
        count_statement = select(func.count()).select_from(statement.subquery())
        total = self.db.scalar(count_statement) or 0
        items = self.db.scalars(
            statement.offset((page - 1) * page_size).limit(page_size)
        ).all()
        return list(items), total

