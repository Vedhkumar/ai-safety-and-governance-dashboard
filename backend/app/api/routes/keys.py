"""API key management routes."""

import secrets
import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db.database import get_db
from app.models.api_key import ApiKey
from app.schemas.auth import ApiKeyCreate, ApiKeyResponse, ApiKeyCreatedResponse
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/keys", tags=["keys"])


def generate_api_key() -> str:
    return f"sk-{secrets.token_hex(24)}"


@router.get("", response_model=list[ApiKeyResponse])
async def list_keys(db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(select(ApiKey).order_by(ApiKey.created_at.desc()))
    return [ApiKeyResponse.model_validate(k) for k in result.scalars().all()]


@router.post("", response_model=ApiKeyCreatedResponse)
async def create_key(data: ApiKeyCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    raw_key = generate_api_key()
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key = ApiKey(key_hash=key_hash, key_prefix=raw_key[:10], name=data.name,
        rate_limit=data.rate_limit, created_by=user.id)
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)

    resp = ApiKeyCreatedResponse.model_validate(api_key)
    resp.full_key = raw_key
    return resp


@router.delete("/{key_id}")
async def revoke_key(key_id: UUID, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.is_active = False
    await db.flush()
    return {"detail": "API key revoked"}
