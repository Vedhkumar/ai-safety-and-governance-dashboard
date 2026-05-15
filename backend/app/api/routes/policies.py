"""Policy CRUD routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db.database import get_db
from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicyResponse, PolicyTestRequest, PolicyTestResult
from app.api.dependencies import get_current_user
from app.models.user import User
from app.engine.pipeline import pipeline
from app.engine.policy import evaluate_condition

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.get("", response_model=list[PolicyResponse])
async def list_policies(db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(select(Policy).order_by(Policy.priority.desc()))
    return [PolicyResponse.model_validate(p) for p in result.scalars().all()]


@router.post("", response_model=PolicyResponse)
async def create_policy(data: PolicyCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    policy = Policy(**data.model_dump(), created_by=user.id)
    db.add(policy)
    await db.flush()
    await db.refresh(policy)
    return PolicyResponse.model_validate(policy)


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(policy_id: UUID, data: PolicyUpdate, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(policy, key, val)
    await db.flush()
    await db.refresh(policy)
    return PolicyResponse.model_validate(policy)


@router.delete("/{policy_id}")
async def delete_policy(policy_id: UUID, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    await db.delete(policy)
    return {"detail": "Policy deleted"}


@router.post("/test", response_model=list[PolicyTestResult])
async def test_policies(data: PolicyTestRequest, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    """Test a prompt against all active policies."""
    scan_results = await pipeline.scan_input(data.prompt)
    result = await db.execute(select(Policy).where(Policy.is_active == True))
    policies = result.scalars().all()

    results = []
    for p in policies:
        triggered = evaluate_condition(p.condition, scan_results)
        score = None
        if "injection" in p.condition:
            score = scan_results.get("injection", type("", (), {"score": 0})).score
        elif "toxicity" in p.condition:
            score = scan_results.get("toxicity", type("", (), {"score": 0})).score
        results.append(PolicyTestResult(policy_name=p.name, condition=p.condition,
            action=p.action, triggered=triggered, score=float(score) if score else None))
    return results
