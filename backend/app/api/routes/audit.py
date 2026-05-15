"""Audit log routes — paginated listing, detail, search."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from typing import Optional
from datetime import datetime
from uuid import UUID
import math

from app.db.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse, AuditLogListResponse
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs", response_model=AuditLogListResponse)
async def list_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    model: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    min_injection: Optional[float] = None,
    min_hallucination: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    # Filters
    if model:
        query = query.where(AuditLog.model == model)
        count_query = count_query.where(AuditLog.model == model)
    if status:
        query = query.where(AuditLog.final_status == status)
        count_query = count_query.where(AuditLog.final_status == status)
    if date_from:
        query = query.where(AuditLog.timestamp >= date_from)
        count_query = count_query.where(AuditLog.timestamp >= date_from)
    if date_to:
        query = query.where(AuditLog.timestamp <= date_to)
        count_query = count_query.where(AuditLog.timestamp <= date_to)
    if search:
        search_filter = or_(AuditLog.input_prompt.ilike(f"%{search}%"), AuditLog.output_response.ilike(f"%{search}%"))
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    if min_injection is not None:
        query = query.where(AuditLog.injection_score >= min_injection)
        count_query = count_query.where(AuditLog.injection_score >= min_injection)
    if min_hallucination is not None:
        query = query.where(AuditLog.hallucination_score >= min_hallucination)
        count_query = count_query.where(AuditLog.hallucination_score >= min_hallucination)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(desc(AuditLog.timestamp)).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    logs = result.scalars().all()

    return AuditLogListResponse(
        logs=[AuditLogResponse.model_validate(log) for log in logs],
        total=total, page=page, per_page=per_page, pages=math.ceil(total / per_page) if total > 0 else 0)


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_log(log_id: UUID, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Log not found")
    return AuditLogResponse.model_validate(log)
