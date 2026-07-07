from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.services.authentication_service import AuthenticationService
from app.utils.security import get_current_user

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    return AuthenticationService(db).register(payload)


@router.post(
    "/login",
    response_model=Token,
    summary="Login and receive a JWT access token",
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    credentials = UserLogin(
        email=form_data.username,
        password=form_data.password,
    )
    return AuthenticationService(db).login(credentials)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user",
)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return current_user


@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Get the current user's profile",
)
def profile(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return current_user
