"""Pydantic schemas for audit log endpoints."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class AuditLogResponse(BaseModel):
    id: UUID
    api_key_id: Optional[UUID] = None
    timestamp: datetime
    model: str
    input_prompt: str
    output_response: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_cost: Optional[float] = None
    latency_ms: Optional[int] = None
    injection_score: Optional[float] = None
    injection_method: Optional[str] = None
    toxicity_scores: Optional[dict] = None
    hallucination_score: Optional[float] = None
    hallucination_claims: Optional[dict] = None
    pii_detected: bool = False
    pii_entities: Optional[dict] = None
    bias_score: Optional[float] = None
    policies_triggered: Optional[dict] = None
    final_status: str

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogResponse]
    total: int
    page: int
    per_page: int
    pages: int


class AuditLogFilter(BaseModel):
    model: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_injection_score: Optional[float] = None
    max_injection_score: Optional[float] = None
    min_toxicity: Optional[float] = None
    min_hallucination: Optional[float] = None
    search: Optional[str] = None
    api_key_id: Optional[UUID] = None
