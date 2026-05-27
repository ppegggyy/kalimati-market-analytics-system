# app/db/crud.py
# ─────────────────────────────────────────────────────────────────
# Database CRUD operations.
#
# All functions receive a SQLAlchemy Session and return ORM objects
# or Pandas DataFrames (for analytics consumption).
# ─────────────────────────────────────────────────────────────────

from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from .models import PriceRecord, AnalyticsCache
from app.schemas.price import PriceRecordCreate


# ── Create ──────────────────────────────────────────────────────────────────

def create_price_record(db: Session, record: PriceRecordCreate) -> PriceRecord:
    """Insert a single price record and return the persisted object."""
    db_record = PriceRecord(
        date=record.record_date,
        product=record.product,
        unit=record.unit,
        max_price=record.max_price,
        min_price=record.min_price,
        avg_price=record.avg_price,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


# ── Read — single record by ID ───────────────────────────────────────────────

def get_price_by_id(db: Session, record_id: int) -> Optional[PriceRecord]:
    """Fetch a single price record by its primary key.

    Returns None if the record does not exist.
    """
    return db.query(PriceRecord).filter(PriceRecord.id == record_id).first()


# ── Read — filtered list ─────────────────────────────────────────────────────

def get_price_records(
    db: Session,
    product: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[PriceRecord]:
    """Fetch price records with optional product and date filters.
    Results are ordered by date ascending.
    """
    query = db.query(PriceRecord)
    if product:
        query = query.filter(PriceRecord.product == product)
    if start_date:
        query = query.filter(PriceRecord.date >= start_date)
    if end_date:
        query = query.filter(PriceRecord.date <= end_date)
    return query.order_by(PriceRecord.date.asc()).offset(skip).limit(limit).all()


# ── Read — as DataFrame (used by all analytics endpoints) ────────────────────

def get_records_as_dataframe(
    db: Session,
    product: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:
    """Return filtered records as a Pandas DataFrame.

    CRITICAL: The analytics layer (app/core/analytics.py) expects columns
    named exactly as the original CSV headers — with spaces and capitals:
        "Date", "Product", "Unit", "Max Price", "Min Price", "Avg Price"
    Do NOT rename these columns.
    """
    query = db.query(PriceRecord).filter(PriceRecord.product == product)
    if start_date:
        query = query.filter(PriceRecord.date >= start_date)
    if end_date:
        query = query.filter(PriceRecord.date <= end_date)
    records = query.order_by(PriceRecord.date.asc()).all()

    if not records:
        return pd.DataFrame(
            columns=["Date", "Product", "Unit", "Max Price", "Min Price", "Avg Price"]
        )

    return pd.DataFrame([
        {
            "Date":      r.date,
            "Product":   r.product,
            "Unit":      r.unit,
            "Max Price": r.max_price,
            "Min Price": r.min_price,
            "Avg Price": r.avg_price,
        }
        for r in records
    ])


# ── Read — distinct products ─────────────────────────────────────────────────

def get_unique_products(db: Session) -> list[str]:
    """Return a sorted list of all distinct product names."""
    results = (
        db.query(PriceRecord.product)
        .distinct()
        .order_by(PriceRecord.product)
        .all()
    )
    return [r[0] for r in results]


# ── Read — latest price per product ─────────────────────────────────────────

def get_latest_prices(db: Session) -> list[PriceRecord]:
    """Return the single most recent price record for each product.

    Uses a subquery to find max(date) per product, then fetches those
    exact rows — gives the 'today's market' snapshot across all products.
    """
    subquery = (
        db.query(
            PriceRecord.product,
            func.max(PriceRecord.date).label("max_date"),
        )
        .group_by(PriceRecord.product)
        .subquery()
    )
    return (
        db.query(PriceRecord)
        .join(
            subquery,
            (PriceRecord.product == subquery.c.product)
            & (PriceRecord.date == subquery.c.max_date),
        )
        .order_by(PriceRecord.product)
        .all()
    )


def get_latest_date_for_product(db: Session, product: str) -> Optional[date]:
    """Fast lookup for the most recent data point of a product."""
    record = (
        db.query(PriceRecord.date)
        .filter(PriceRecord.product == product)
        .order_by(PriceRecord.date.desc())
        .first()
    )
    return record[0] if record else None


# ── Analytics Cache ─────────────────────────────────────────────────────────

def get_cached_analytics(
    db: Session,
    product: str,
    metric_type: str,
    as_of_date: date,
    window_days: Optional[int] = None,
) -> Optional[dict]:
    """Retrieve precomputed analytics from cache for a given date."""
    query = db.query(AnalyticsCache).filter(
        AnalyticsCache.product == product,
        AnalyticsCache.metric_type == metric_type,
        AnalyticsCache.as_of_date == as_of_date,
    )
    if window_days is not None:
        query = query.filter(AnalyticsCache.window_days == window_days)
    else:
        query = query.filter(AnalyticsCache.window_days.is_(None))
    
    record = query.first()
    return record.payload if record else None


def set_cached_analytics(
    db: Session,
    product: str,
    metric_type: str,
    as_of_date: date,
    payload: dict,
    window_days: Optional[int] = None,
) -> None:
    """Upsert the computed analytics payload into the cache table."""
    stmt = insert(AnalyticsCache).values(
        product=product,
        metric_type=metric_type,
        window_days=window_days,
        as_of_date=as_of_date,
        payload=payload,
        created_at=func.now(),
        updated_at=func.now(),
    )
    
    # On conflict, update payload and updated_at
    stmt = stmt.on_conflict_do_update(
        index_elements=["product", "metric_type", "window_days", "as_of_date"],
        set_={
            "payload": stmt.excluded.payload,
            "updated_at": func.now(),
        }
    )
    
    db.execute(stmt)
    db.commit()