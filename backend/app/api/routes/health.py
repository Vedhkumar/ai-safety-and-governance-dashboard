"""Health check route."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "ai-safety-gateway"}
