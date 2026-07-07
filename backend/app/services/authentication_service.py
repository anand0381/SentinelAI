from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import Token, UserCreate, UserLogin
from app.utils.security import create_access_token, hash_password, verify_password


class AuthenticationService:
    def __init__(self, db: Session) -> None:
        self.user_repository = UserRepository(db)

    def register(self, user_data: UserCreate) -> User:
        if user_data.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator accounts cannot be created through registration",
            )

        existing_user = self.user_repository.get_user_by_email(str(user_data.email))

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

        password_hash = hash_password(user_data.password)
        return self.user_repository.create_user(user_data, password_hash)

    def authenticate(self, email: str, password: str) -> User:
        user = self.user_repository.get_user_by_email(email)

        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        return user

    def login(self, credentials: UserLogin) -> Token:
        user = self.authenticate(str(credentials.email), credentials.password)
        access_token, expires_in = create_access_token(str(user.id), user.role)

        return Token(
            access_token=access_token,
            expires_in=expires_in,
            user=user,
        )

    def get_current_user(self, user: User) -> User:
        return user
