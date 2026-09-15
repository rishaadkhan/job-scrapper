"""Authentication endpoints: Login, Current User, and User Management"""
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.database import get_db
from backend.models import User
from backend.schemas import TokenResponse, LoginRequest, UserResponse, UserCreate
from backend.auth import (
    verify_password, create_access_token, get_current_user, require_admin
)
from backend.crud import get_user_by_email, create_user, update_user_last_login
from backend.exceptions import AuthError, ConflictError

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def _authenticate_and_create_token(email: str, password: str, db: AsyncSession) -> TokenResponse:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise AuthError(message="Incorrect email or password")

    if not user.is_active:
        raise AuthError(message="Account is inactive")

    await update_user_last_login(db, user.id)

    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        email=user.email
    )


@router.post("/login", response_model=TokenResponse)
async def login_json(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate via JSON payload (email & password) and return signed JWT."""
    return await _authenticate_and_create_token(credentials.email, credentials.password, db)


@router.post("/token", response_model=TokenResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """OAuth2 compatible token login for Swagger UI and form-encoded clients."""
    return await _authenticate_and_create_token(form_data.username, form_data.password, db)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile and role information for currently authenticated user."""
    return current_user


@router.post("/users", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Admin-only endpoint to create new users with designated roles."""
    return await create_user(db, user_in)
