"""Pydantic schemas for policy endpoints."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class PolicyCreate(BaseModel):
    name: str = Field(..., max_length=100)
    condition: str = Field(..., description="Parseable condition, e.g. 'injection.confidence > 0.85'")
    action: str = Field(..., pattern="^(block|flag|mask|log)$")
    message: Optional[str] = None
    priority: int = Field(default=0)
    is_active: bool = True


class PolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    condition: Optional[str] = None
    action: Optional[str] = Field(None, pattern="^(block|flag|mask|log)$")
    message: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class PolicyResponse(BaseModel):
    id: UUID
    name: str
    condition: str
    action: str
    message: Optional[str] = None
    is_active: bool
    priority: int
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PolicyTestRequest(BaseModel):
    prompt: str = Field(..., description="Test prompt to evaluate against policies")


class PolicyTestResult(BaseModel):
    policy_name: str
    condition: str
    action: str
    triggered: bool
    score: Optional[float] = None
