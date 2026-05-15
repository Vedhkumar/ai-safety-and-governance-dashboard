"""Model comparison routes — A/B testing for LLM models."""

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db.database import get_db
from app.models.comparison import Comparison
from app.schemas.auth import CompareRequest, CompareResponse, ModelResult
from app.api.dependencies import get_current_user
from app.models.user import User
from app.proxy.providers import get_provider
from app.engine.pipeline import pipeline

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.post("", response_model=CompareResponse)
async def run_comparison(data: CompareRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    messages = [{"role": "user", "content": data.prompt}]
    context = {"source_documents": data.source_documents or []}

    async def run_model(model_name: str) -> ModelResult:
        provider = get_provider(model_name)
        llm_resp = await provider.complete(messages, model_name)
        input_results = await pipeline.scan_input(data.prompt)
        output_results = await pipeline.scan_output(llm_resp.content, context)
        inj = input_results.get("injection")
        tox = input_results.get("toxicity") or output_results.get("toxicity")
        hall = output_results.get("hallucination")
        bias = input_results.get("bias") or output_results.get("bias")

        return ModelResult(model=model_name, response=llm_resp.content,
            latency_ms=llm_resp.latency_ms, input_tokens=llm_resp.input_tokens,
            output_tokens=llm_resp.output_tokens, total_cost=llm_resp.total_cost,
            injection_score=float(inj.score) if inj else 0,
            toxicity_scores=tox.details.get("category_scores", {}) if tox else {},
            hallucination_score=float(hall.score) if hall else 0,
            bias_score=float(bias.score) if bias else 0,
            final_status="passed")

    results = await asyncio.gather(*[run_model(m) for m in data.models], return_exceptions=True)
    valid_results = []
    for r in results:
        if isinstance(r, Exception):
            continue
        valid_results.append(r)

    comp = Comparison(prompt=data.prompt, results=[r.model_dump() for r in valid_results], created_by=user.id)
    db.add(comp)
    await db.flush()
    await db.refresh(comp)

    return CompareResponse(id=comp.id, prompt=comp.prompt,
        results=valid_results, created_at=comp.created_at)


@router.get("/{comparison_id}", response_model=CompareResponse)
async def get_comparison(comparison_id: UUID, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(select(Comparison).where(Comparison.id == comparison_id))
    comp = result.scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return CompareResponse(id=comp.id, prompt=comp.prompt,
        results=[ModelResult(**r) for r in comp.results], created_at=comp.created_at)
