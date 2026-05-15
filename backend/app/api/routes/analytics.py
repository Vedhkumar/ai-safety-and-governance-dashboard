"""Analytics routes — overview stats, safety trends, cost breakdown, model stats."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, extract
from datetime import datetime, timedelta, timezone

from app.db.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.analytics import (OverviewStats, SafetyTrendPoint, CostBreakdownItem,
    ModelStats, HeatmapPoint, TopPolicy, AnalyticsResponse)
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewStats)
async def get_overview(db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)

    async def count_since(delta):
        r = await db.execute(select(func.count(AuditLog.id)).where(AuditLog.timestamp >= now - delta))
        return r.scalar() or 0

    async def blocked_rate(delta):
        total = await count_since(delta)
        if total == 0:
            return 0.0
        r = await db.execute(select(func.count(AuditLog.id)).where(
            AuditLog.timestamp >= now - delta, AuditLog.final_status == "blocked"))
        return round((r.scalar() or 0) / total * 100, 1)

    async def avg_score(column, delta):
        r = await db.execute(select(func.avg(column)).where(AuditLog.timestamp >= now - delta))
        return round(float(r.scalar() or 0), 3)

    async def total_cost(delta):
        r = await db.execute(select(func.sum(AuditLog.total_cost)).where(AuditLog.timestamp >= now - delta))
        return round(float(r.scalar() or 0), 4)

    async def avg_latency(delta):
        r = await db.execute(select(func.avg(AuditLog.latency_ms)).where(AuditLog.timestamp >= now - delta))
        return round(float(r.scalar() or 0), 0)

    d24h, d7d, d30d = timedelta(hours=24), timedelta(days=7), timedelta(days=30)

    return OverviewStats(
        total_requests_24h=await count_since(d24h), total_requests_7d=await count_since(d7d),
        total_requests_30d=await count_since(d30d), block_rate=await blocked_rate(d7d),
        avg_injection_score=await avg_score(AuditLog.injection_score, d7d),
        avg_hallucination_score=await avg_score(AuditLog.hallucination_score, d7d),
        total_cost_24h=await total_cost(d24h), total_cost_7d=await total_cost(d7d),
        total_cost_30d=await total_cost(d30d), avg_latency_ms=await avg_latency(d7d))


@router.get("/safety", response_model=list[SafetyTrendPoint])
async def get_safety_trends(
    hours: int = Query(168, ge=1, le=720),
    db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)
    bucket = max(hours // 24, 1)

    result = await db.execute(
        select(
            func.date_trunc('hour', AuditLog.timestamp).label('bucket'),
            func.avg(AuditLog.injection_score).label('inj'),
            func.avg(AuditLog.hallucination_score).label('hall'),
            func.avg(AuditLog.bias_score).label('bias_avg'),
            func.count(AuditLog.id).label('cnt')
        ).where(AuditLog.timestamp >= since)
        .group_by('bucket').order_by('bucket'))

    return [SafetyTrendPoint(timestamp=str(row.bucket), injection_avg=round(float(row.inj or 0), 3),
        hallucination_avg=round(float(row.hall or 0), 3), bias_avg=round(float(row.bias_avg or 0), 3),
        request_count=row.cnt) for row in result.all()]


@router.get("/costs", response_model=list[CostBreakdownItem])
async def get_cost_breakdown(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(AuditLog.model, func.sum(AuditLog.total_cost).label('cost'),
            func.sum(AuditLog.input_tokens + AuditLog.output_tokens).label('tokens'),
            func.count(AuditLog.id).label('cnt'))
        .where(AuditLog.timestamp >= since).group_by(AuditLog.model))

    return [CostBreakdownItem(model=row.model, total_cost=round(float(row.cost or 0), 4),
        total_tokens=int(row.tokens or 0), request_count=row.cnt) for row in result.all()]


@router.get("/models", response_model=list[ModelStats])
async def get_model_stats(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(AuditLog.model, func.count(AuditLog.id).label('cnt'),
            func.avg(AuditLog.latency_ms).label('lat'),
            func.avg(AuditLog.injection_score).label('inj'),
            func.avg(AuditLog.hallucination_score).label('hall'),
            func.sum(AuditLog.total_cost).label('cost'))
        .where(AuditLog.timestamp >= since).group_by(AuditLog.model))

    return [ModelStats(model=row.model, request_count=row.cnt,
        avg_latency_ms=round(float(row.lat or 0)), avg_injection_score=round(float(row.inj or 0), 3),
        avg_hallucination_score=round(float(row.hall or 0), 3),
        total_cost=round(float(row.cost or 0), 4)) for row in result.all()]


@router.get("/heatmap", response_model=list[HeatmapPoint])
async def get_heatmap(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(extract('dow', AuditLog.timestamp).label('dow'),
            extract('hour', AuditLog.timestamp).label('hr'),
            func.count(AuditLog.id).label('cnt'))
        .where(AuditLog.timestamp >= since)
        .group_by('dow', 'hr').order_by('dow', 'hr'))

    return [HeatmapPoint(day=int(row.dow), hour=int(row.hr), count=row.cnt) for row in result.all()]
