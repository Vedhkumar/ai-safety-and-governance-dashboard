"""AI Safety Proxy Gateway — OpenAI-compatible endpoint with safety guardrails."""

import uuid
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.audit_log import AuditLog
from app.models.policy import Policy
from app.schemas.proxy import ChatCompletionRequest, ChatCompletionResponse, ChatChoice, ChatMessage, TokenUsage, SafetyMetadata
from app.engine.pipeline import pipeline
from app.engine.policy import evaluate_policies
from app.proxy.providers import get_provider
from app.api.websockets import broadcast_event

router = APIRouter()


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest, raw_request: Request, db: AsyncSession = Depends(get_db)):
    """OpenAI-compatible chat completions endpoint with safety guardrails."""
    start_time = time.time()

    # Extract the full prompt text
    input_text = " ".join(m.content for m in request.messages if m.role != "system")

    # ── STEP 1: Input Guardrails (parallel) ──
    input_results = await pipeline.scan_input(input_text)

    # ── STEP 2: Check PII and mask if needed ──
    masked_text = input_text
    pii_entities = []
    if input_results.get("pii") and input_results["pii"].is_flagged:
        masked_text, pii_entities = pipeline.mask_pii(input_text)

    # ── STEP 3: Load policies and evaluate input ──
    from sqlalchemy import select
    policy_rows = await db.execute(select(Policy).where(Policy.is_active == True))
    policies = [{"name": p.name, "condition": p.condition, "action": p.action,
                 "message": p.message, "is_active": p.is_active} for p in policy_rows.scalars().all()]

    input_status, input_triggered = evaluate_policies(policies, input_results)

    # If blocked by input guardrails, return immediately
    if input_status == "blocked":
        block_msg = input_triggered[0].message if input_triggered else "Request blocked by safety policy"
        latency = int((time.time() - start_time) * 1000)

        audit_log = AuditLog(
            model=request.model, input_prompt=input_text, output_response=None,
            input_tokens=0, output_tokens=0, total_cost=0, latency_ms=latency,
            injection_score=float(input_results.get("injection", type("", (), {"score": 0})).score),
            injection_method=input_results.get("injection", type("", (), {"details": {}})).details.get("method", "none"),
            toxicity_scores=input_results.get("toxicity", type("", (), {"details": {}})).details.get("category_scores", {}),
            hallucination_score=0, pii_detected=bool(pii_entities),
            pii_entities={"entities": [e["type"] for e in pii_entities]} if pii_entities else None,
            bias_score=float(input_results.get("bias", type("", (), {"score": 0})).score),
            policies_triggered=[a.to_dict() for a in input_triggered],
            final_status="blocked")
        db.add(audit_log)
        await db.flush()

        await broadcast_event({"type": "request", "id": str(audit_log.id), "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": request.model, "status": "blocked", "latency_ms": latency,
            "injection_score": float(input_results.get("injection", type("", (), {"score": 0})).score)})

        raise HTTPException(status_code=403, detail={"error": block_msg, "safety": {"policies_triggered": [a.to_dict() for a in input_triggered], "status": "blocked"}})

    # ── STEP 4: Forward to LLM ──
    provider = get_provider(request.model)
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    try:
        llm_response = await provider.complete(messages, request.model,
            temperature=request.temperature, max_tokens=request.max_tokens)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM provider error: {str(e)}")

    # ── STEP 5: Output Guardrails ──
    context = {"source_documents": request.source_documents or [], "original_prompt": input_text}
    output_results = await pipeline.scan_output(llm_response.content, context)

    # Merge input + output results for policy evaluation
    all_results = {**input_results, **output_results}
    final_status, all_triggered = evaluate_policies(policies, all_results)

    # If output blocked, still log but return error
    total_latency = int((time.time() - start_time) * 1000)
    response_text = llm_response.content if final_status != "blocked" else None

    # ── STEP 6: Log to audit trail ──
    inj = input_results.get("injection")
    tox = all_results.get("toxicity")
    hall = output_results.get("hallucination")
    bias = all_results.get("bias")

    audit_log = AuditLog(
        model=request.model, input_prompt=input_text, output_response=response_text,
        input_tokens=llm_response.input_tokens, output_tokens=llm_response.output_tokens,
        total_cost=llm_response.total_cost, latency_ms=total_latency,
        injection_score=float(inj.score) if inj else 0,
        injection_method=inj.details.get("method", "none") if inj else "none",
        toxicity_scores=tox.details.get("category_scores", {}) if tox else {},
        hallucination_score=float(hall.score) if hall else 0,
        hallucination_claims=hall.details if hall else None,
        pii_detected=bool(pii_entities),
        pii_entities={"entities": [e["type"] for e in pii_entities]} if pii_entities else None,
        bias_score=float(bias.score) if bias else 0,
        policies_triggered=[a.to_dict() for a in all_triggered],
        final_status=final_status)
    db.add(audit_log)
    await db.flush()

    # Broadcast to WebSocket
    await broadcast_event({"type": "request", "id": str(audit_log.id), "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": request.model, "status": final_status, "latency_ms": total_latency,
        "injection_score": float(inj.score) if inj else 0,
        "hallucination_score": float(hall.score) if hall else 0,
        "cost": llm_response.total_cost})

    if final_status == "blocked":
        raise HTTPException(status_code=403, detail={"error": "Response blocked by safety policy",
            "safety": {"policies_triggered": [a.to_dict() for a in all_triggered], "status": "blocked"}})

    # ── STEP 7: Return response ──
    safety = SafetyMetadata(
        injection_score=float(inj.score) if inj else 0,
        injection_method=inj.details.get("method", "none") if inj else "none",
        toxicity_scores=tox.details.get("category_scores", {}) if tox else {},
        hallucination_score=float(hall.score) if hall else 0,
        pii_detected=bool(pii_entities),
        pii_entities=[e["type"] for e in pii_entities],
        bias_score=float(bias.score) if bias else 0,
        policies_triggered=[a.to_dict() for a in all_triggered],
        final_status=final_status)

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:12]}", created=int(time.time()),
        model=request.model,
        choices=[ChatChoice(index=0, message=ChatMessage(role="assistant", content=llm_response.content))],
        usage=TokenUsage(prompt_tokens=llm_response.input_tokens, completion_tokens=llm_response.output_tokens,
            total_tokens=llm_response.input_tokens + llm_response.output_tokens),
        safety=safety)
