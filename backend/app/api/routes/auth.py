"""Auth routes — login, register, token management."""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from passlib.context import CryptContext

from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(user_id: str, expires_delta: timedelta) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + expires_delta
    return jwt.encode({"sub": user_id, "exp": expire}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=data.email, password_hash=pwd_context.hash(data.password), role=data.role)
    db.add(user)
    await db.flush()
    await db.refresh(user)

    settings = get_settings()
    access = create_token(str(user.id), timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh = create_token(str(user.id), timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS))

    return TokenResponse(access_token=access, refresh_token=refresh,
        user=UserResponse(id=user.id, email=user.email, role=user.role, created_at=user.created_at))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    settings = get_settings()
    access = create_token(str(user.id), timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh = create_token(str(user.id), timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS))

    return TokenResponse(access_token=access, refresh_token=refresh,
        user=UserResponse(id=user.id, email=user.email, role=user.role, created_at=user.created_at))
