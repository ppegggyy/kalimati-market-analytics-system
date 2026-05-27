# app/api/prices.py

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import crud
from app.schemas.price import PriceRecordCreate, PriceRecordRead

router = APIRouter(prefix="/prices", tags=["Prices"])


# ── GET /prices ──────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[PriceRecordRead],
    summary="List price records",
    description=(
        "Fetch paginated price records. Filter by product name and/or "
        "a date range (YYYY-MM-DD). Results are ordered by Date ascending."
    ),
)
def list_prices(
    product: Optional[str] = Query(None, description="Filter by exact product name"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return crud.get_price_records(
        db,
        product=product,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )


# ── GET /prices/products ─────────────────────────────────────────────────────

@router.get(
    "/products",
    response_model=list[str],
    summary="List distinct products",
    description="Return a sorted list of all unique product names in the database.",
)
def list_products(db: Session = Depends(get_db)):
    return crud.get_unique_products(db)


# ── GET /prices/latest ───────────────────────────────────────────────────────
# This route MUST come before /{record_id} — otherwise FastAPI
# tries to parse the string "latest" as an integer and returns 422.

@router.get(
    "/latest",
    response_model=list[PriceRecordRead],
    summary="Latest price for every product",
    description=(
        "Returns the single most recent price record for each product. "
        "Used by the Dashboard page for a 'today's market' snapshot."
    ),
)
def get_latest_prices(db: Session = Depends(get_db)):
    return crud.get_latest_prices(db)


# ── GET /prices/{record_id} ──────────────────────────────────────────────────

@router.get(
    "/{record_id}",
    response_model=PriceRecordRead,
    summary="Get a single price record by ID",
)
def get_price(record_id: int, db: Session = Depends(get_db)):
    record = crud.get_price_by_id(db, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Price record with id={record_id} not found.",
        )
    return record


# ── POST /prices ─────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=PriceRecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Insert a new price record",
)
def create_price(payload: PriceRecordCreate, db: Session = Depends(get_db)):
    return crud.create_price_record(db, payload)