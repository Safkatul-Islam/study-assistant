import uuid

from fastapi import Cookie, Depends, Header
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import decode_token
from app.db.models.user import User
from app.db.session import get_db


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
    access_token: str | None = Cookie(None),
) -> User:
    """Extract and validate the current user from JWT (header or cookie)."""
    token = None

    # Try Authorization header first, then cookie
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif access_token:
        token = access_token

    if not token:
        raise AppError(status_code=401, message="Not authenticated")

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise AppError(status_code=401, message="Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            raise AppError(status_code=401, message="Invalid token")
    except JWTError:
        raise AppError(status_code=401, message="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise AppError(status_code=401, message="User not found or inactive")

    return user
