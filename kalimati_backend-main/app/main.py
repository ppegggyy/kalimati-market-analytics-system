# app/main.py
# ─────────────────────────────────────────────────────────────────
# Application entry-point.
#
# Run in development:
#   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
#
# Interactive docs:
#   http://127.0.0.1:8000/docs   ← Swagger UI
#   http://127.0.0.1:8000/redoc  ← ReDoc
# ─────────────────────────────────────────────────────────────────

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.db.bootstrap import ensure_db_objects
from app.db.session import Base, engine
from app.services.scheduler import start_scheduler, stop_scheduler

# ── Logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Create DB tables on startup (dev convenience) ──────────────────
# The prices table already exists in PostgreSQL.  create_all() uses
# IF NOT EXISTS so this is safe — it only creates missing tables.
def _create_tables() -> None:
    logger.info("Creating database tables (if they do not exist)…")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")


# ── Lifespan (replaces deprecated on_event) ────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan handler — runs startup code before yield,
    shutdown code after yield."""
    logger.info("Starting %s v%s …", settings.app_name, settings.app_version)
    ensure_db_objects()
    _create_tables()
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Shutting down %s.", settings.app_name)


# ── FastAPI application ────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    description=(
        "REST API for monitoring and forecasting vegetable prices "
        "at Kalimati Market, Nepal.\n\n"
        "**Dataset columns:** Date · Product · Unit · "
        "Max Price · Min Price · Avg Price"
    ),
    contact={
        "name": "Capstone Team",
        "email": "team@example.com",
    },
    license_info={"name": "MIT"},
)

# ── CORS (adjust origins for production) ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register all routes ────────────────────────────────────────────
app.include_router(api_router)


# ── Health-check ───────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health_check():
    """Quick liveness probe — returns 200 when the server is running."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }
