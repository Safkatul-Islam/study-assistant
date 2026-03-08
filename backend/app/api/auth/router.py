from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.schemas import AuthResponse, LoginRequest, RefreshRequest, RegisterRequest, UserOut, UserResponse
from app.api.auth.service import authenticate_user, generate_tokens, refresh_tokens, register_user
from app.db.models.user import User
from app.db.session import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, body.email, body.password, body.full_name)
    tokens = generate_tokens(user)
    return AuthResponse(
        **tokens,
        user=UserOut(id=str(user.id), email=user.email, full_name=user.full_name),
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    user, tokens = await refresh_tokens(db, body.refresh_token)
    return AuthResponse(
        **tokens,
        user=UserOut(id=str(user.id), email=user.email, full_name=user.full_name),
    )


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse(
        user=UserOut(id=str(user.id), email=user.email, full_name=user.full_name),
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    tokens = generate_tokens(user)
    return AuthResponse(
        **tokens,
        user=UserOut(id=str(user.id), email=user.email, full_name=user.full_name),
    )
