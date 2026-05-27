# app/db/session.py
# ─────────────────────────────────────────────────────────────────
# SQLAlchemy engine + session factory.
#
# INSTRUCTIONS FOR DB EXPERT:
#   • Change DATABASE_URL in .env to point at your target DB.
#   • For async support (recommended with FastAPI), swap to:
#       from sqlalchemy.ext.asyncio import (
#           AsyncSession, create_async_engine, async_sessionmaker
#       )
#     and update the get_db() generator accordingly.
# ─────────────────────────────────────────────────────────────────

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# Create the engine.  connect_args is only needed for SQLite.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
    echo=settings.debug,   # logs all SQL when DEBUG=True
)

# Session factory — do NOT use Session directly in route handlers;
# always go through the get_db() dependency instead.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Declarative base — all ORM models inherit from this.
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ─────────────────────────────────────────────

def get_db():
    """Yield a database session and guarantee it is closed afterward.

    Usage in route handlers:
        @router.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
