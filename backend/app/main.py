"""FastAPI application — AI Safety & Governance Gateway."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize database tables and seed data."""
    await init_db()
    # Seed demo data on first run
    try:
        from app.db.seed import seed_database
        await seed_database()
    except Exception as e:
        print(f"Seeding skipped or failed: {e}")
    yield


app = FastAPI(
    title="AI Safety & Governance Gateway",
    description="A security gateway between applications and LLMs with real-time monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
from app.proxy.gateway import router as proxy_router
from app.api.routes.auth import router as auth_router
from app.api.routes.audit import router as audit_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.policies import router as policies_router
from app.api.routes.keys import router as keys_router
from app.api.routes.compare import router as compare_router
from app.api.routes.health import router as health_router
from app.api.websockets import router as ws_router

app.include_router(proxy_router)
app.include_router(auth_router)
app.include_router(audit_router)
app.include_router(analytics_router)
app.include_router(policies_router)
app.include_router(keys_router)
app.include_router(compare_router)
app.include_router(health_router)
app.include_router(ws_router)
