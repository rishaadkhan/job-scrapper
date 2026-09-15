"""Authentication service: JWT creation, verification, direct bcrypt password hashing, and RBAC guards"""
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, utc_now
from backend.database import get_db
from backend.models import User
from backend.exceptions import AuthError, ForbiddenError, NotFoundError

# OAuth2 scheme for Swagger UI & token header extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate direct bcrypt hash of a password."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT token with claims and expiry."""
    to_encode = data.copy()
    expire = utc_now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": utc_now()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency that decodes Bearer JWT, validates signature, and returns the DB User."""
    credentials_exception = AuthError(
        message="Could not validate credentials or token expired",
        details={"header": "WWW-Authenticate: Bearer"}
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthError(message="User not found")
    if not user.is_active:
        raise ForbiddenError(message="Inactive user account")

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """RBAC guard ensuring the current user possesses the 'admin' role."""
    if current_user.role != "admin":
        raise ForbiddenError(
            message="Administrator privileges required for this operation",
            details={"current_role": current_user.role}
        )
    return current_user
