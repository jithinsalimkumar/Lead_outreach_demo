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

# Create the FastAPI application
app = FastAPI(
    title="Lead Outreach System",
    description="Internal tool for managing the lead discovery → enrichment → outreach pipeline",
    version="1.0.0",
    docs_url="/api/docs",      # Swagger UI at /api/docs
    redoc_url="/api/redoc",    # ReDoc at /api/redoc
)

from fastapi.responses import JSONResponse, RedirectResponse

# --- Universal CORS Middleware ---
# Allows requests from ANY frontend origin (Render, Vercel, localhost, custom domains, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,        # Set to False when using wildcard "*" as required by CORS spec
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """
    Global exception handler to catch any unhandled server errors.
    Ensures CORS headers are ALWAYS returned even on internal 500 errors
    so the frontend receives the actual error message instead of a CORS block.
    """
    import logging
    logging.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers={"Access-Control-Allow-Origin": "*"},
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
