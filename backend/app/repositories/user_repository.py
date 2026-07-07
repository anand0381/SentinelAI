from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(self, user_data: UserCreate, password_hash: str) -> User:
        user = User(
            full_name=user_data.full_name,
            email=str(user_data.email).lower(),
            password_hash=password_hash,
            role=user_data.role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return self.db.scalar(statement)

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def update_user(self, user: User, updates: dict[str, object]) -> User:
        for field, value in updates.items():
            if hasattr(user, field):
                setattr(user, field, value)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
