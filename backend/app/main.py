"""
FastAPI application entry point.

This module creates the FastAPI app, configures CORS, and registers
all API routers. The app is started by Uvicorn (see docker-compose.yml).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

from app.routers import (
    auth,
    campaigns,
    companies,
    dashboard,
    enrichment,
    leads,
    settings as settings_router,
    suppression,
    users,
    webhooks,
    scraped_jobs,
)

from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-seed database on startup if empty
    try:
        from app.seed import seed
        await seed(auto_confirm=True)
    except Exception as e:
        logger.warning(f"Auto-seed check failed or skipped: {e}")
    yield

# Create the FastAPI application
app = FastAPI(
    title="Lead Outreach System",
    description="Internal tool for managing the lead discovery → enrichment → outreach pipeline",
    version="1.0.0",
    docs_url="/api/docs",      # Swagger UI at /api/docs
    redoc_url="/api/redoc",    # ReDoc at /api/redoc
    lifespan=lifespan,
)

# --- CORS Middleware ---
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],           # Allow all HTTP methods
    allow_headers=["*"],           # Allow all headers (including Authorization)
)

# --- Register API Routers ---
# Each router is a group of related endpoints (see routers/ directory)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(companies.router)
app.include_router(leads.router)
app.include_router(enrichment.router)
app.include_router(campaigns.router)
app.include_router(suppression.router)
app.include_router(webhooks.router)
app.include_router(dashboard.router)
app.include_router(settings_router.router)
app.include_router(scraped_jobs.router)


from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root path to the Swagger UI."""
    return RedirectResponse(url="/api/docs")

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint — useful for Docker health checks."""
    return {"status": "healthy", "service": "lead-outreach-backend"}

@app.all("/api/seed")
async def trigger_seed():
    """Endpoint to trigger database seeding if database is empty."""
    from app.seed import seed
    try:
        await seed(auto_confirm=True)
        return {"status": "success", "message": "Database seed completed or already seeded."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

