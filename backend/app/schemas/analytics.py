"""Pydantic schemas for analytics endpoints."""

from pydantic import BaseModel
from typing import Optional


class OverviewStats(BaseModel):
    total_requests_24h: int = 0
    total_requests_7d: int = 0
    total_requests_30d: int = 0
    block_rate: float = 0.0
    flag_rate: float = 0.0
    avg_injection_score: float = 0.0
    avg_toxicity_score: float = 0.0
    avg_hallucination_score: float = 0.0
    total_cost_24h: float = 0.0
    total_cost_7d: float = 0.0
    total_cost_30d: float = 0.0
    avg_latency_ms: float = 0.0


class SafetyTrendPoint(BaseModel):
    timestamp: str
    injection_avg: float = 0.0
    toxicity_avg: float = 0.0
    hallucination_avg: float = 0.0
    bias_avg: float = 0.0
    request_count: int = 0


class CostBreakdownItem(BaseModel):
    model: str
    total_cost: float = 0.0
    total_tokens: int = 0
    request_count: int = 0


class ModelStats(BaseModel):
    model: str
    request_count: int = 0
    avg_latency_ms: float = 0.0
    avg_injection_score: float = 0.0
    avg_hallucination_score: float = 0.0
    block_rate: float = 0.0
    total_cost: float = 0.0


class HeatmapPoint(BaseModel):
    day: int  # 0-6 (Mon-Sun)
    hour: int  # 0-23
    count: int = 0


class TopPolicy(BaseModel):
    name: str
    trigger_count: int
    action: str


class AnalyticsResponse(BaseModel):
    overview: OverviewStats
    safety_trends: list[SafetyTrendPoint] = []
    cost_breakdown: list[CostBreakdownItem] = []
    model_stats: list[ModelStats] = []
    heatmap: list[HeatmapPoint] = []
    top_policies: list[TopPolicy] = []
