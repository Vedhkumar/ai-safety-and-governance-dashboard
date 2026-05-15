"""Pydantic schemas for auth and API key management."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


# ─── Auth Schemas ───

class UserRegister(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6)
    role: str = Field(default="viewer", pattern="^(admin|editor|viewer)$")


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── API Key Schemas ───

class ApiKeyCreate(BaseModel):
    name: str = Field(..., max_length=100)
    rate_limit: int = Field(default=100, ge=1, le=10000)


class ApiKeyResponse(BaseModel):
    id: UUID
    key_prefix: str
    name: str
    rate_limit: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned only on creation — includes the full key (shown once)."""
    full_key: str


# ─── Compare Schemas ───

class CompareRequest(BaseModel):
    prompt: str
    models: list[str] = Field(..., min_length=2, max_length=4)
    source_documents: Optional[list[str]] = None


class ModelResult(BaseModel):
    model: str
    response: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    total_cost: float
    injection_score: float
    toxicity_scores: dict
    hallucination_score: float
    bias_score: float
    final_status: str


class CompareResponse(BaseModel):
    id: UUID
    prompt: str
    results: list[ModelResult]
    created_at: datetime

    class Config:
        from_attributes = True
