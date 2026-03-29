import uuid

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User


async def register_user(db: AsyncSession, email: str, password: str, full_name: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise ConflictError("A user with this email already exists")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise AppError(status_code=401, message="Invalid email or password")

    if not user.is_active:
        raise AppError(status_code=401, message="Account is inactive")

    return user


def generate_tokens(user: User) -> dict:
    user_id = str(user.id)
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
    }


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> tuple[User, dict]:
    """Decode refresh token, verify type, look up user, return new token pair."""
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise AppError(status_code=401, message="Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise AppError(status_code=401, message="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AppError(status_code=401, message="Invalid token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise AppError(status_code=401, message="User not found or inactive")

    return user, generate_tokens(user)


async def update_profile(db: AsyncSession, user: User, full_name: str) -> User:
    user.full_name = full_name
    await db.flush()
    return user


async def change_password(
    db: AsyncSession, user: User, current_password: str, new_password: str
) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise AppError(status_code=400, message="Current password is incorrect")
    user.hashed_password = hash_password(new_password)
    await db.flush()
