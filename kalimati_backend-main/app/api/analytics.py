# app/api/analytics.py
# ─────────────────────────────────────────────────────────────────
# Analytics & forecasting endpoints.
# ─────────────────────────────────────────────────────────────────

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import crud
from app.core.analytics import (
    calculate_price_trend,
    calculate_volatility,
    detect_price_spikes,
    get_moving_average,
)
from app.schemas.price import (
    ForecastRequest,
    ForecastResponse,
    PriceSpikeRecord,
    SpikeDetectionResponse,
    TrendResponse,
    VolatilityResponse,
)
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Singleton per worker process — ML Expert can swap this with a pre-trained loader.
_forecast_service = ForecastService()


# ── GET /analytics/volatility ────────────────────────────────────────────────

@router.get(
    "/volatility",
    response_model=VolatilityResponse,
    summary="Price volatility for a product",
    description=(
        "Returns the standard deviation of Avg Price over the requested "
        "date window. Higher values indicate a more volatile market."
    ),
)
def get_volatility(
    product: str = Query(..., description="Product name to analyse"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    as_of = end_date or crud.get_latest_date_for_product(db, product)
    if not as_of:
        raise HTTPException(status_code=404, detail=f"No price data found for product '{product}'.")
        
    metric_key = f"volatility_{start_date.isoformat()}" if start_date else "volatility"
    cached = crud.get_cached_analytics(db, product, metric_key, as_of)
    if cached:
        return VolatilityResponse(**cached)

    df = crud.get_records_as_dataframe(db, product, start_date, end_date)

    # Drop rows with null avg_price — can't compute volatility on NaN
    df = df.dropna(subset=["Avg Price"])

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No valid price data found for product '{product}'.",
        )

    std_dev = calculate_volatility(df)
    resp = VolatilityResponse(
        product=product,
        unit=df["Unit"].iloc[0] if not df.empty else "N/A",
        start_date=start_date or df["Date"].min(),
        end_date=end_date or df["Date"].max(),
        std_dev_avg_price=round(std_dev, 4),
        record_count=len(df),
    )
    crud.set_cached_analytics(db, product, metric_key, as_of, jsonable_encoder(resp))
    return resp


# ── GET /analytics/spikes ────────────────────────────────────────────────────

@router.get(
    "/spikes",
    response_model=SpikeDetectionResponse,
    summary="Detect price spikes",
    description=(
        "Flags days where Avg Price exceeded the rolling N-day average "
        "by more than the configured threshold (default 30 %)."
    ),
)
def get_spikes(
    product: str = Query(..., description="Product name to check"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    threshold: float = Query(0.30, ge=0.01, le=5.0),
    window: int = Query(7, ge=2, le=90),
    db: Session = Depends(get_db),
):
    as_of = end_date or crud.get_latest_date_for_product(db, product)
    if not as_of:
        raise HTTPException(status_code=404, detail=f"No price data found for product '{product}'.")
        
    metric_key = f"spikes_{start_date.isoformat()}_{threshold}" if start_date else f"spikes_{threshold}"
    cached = crud.get_cached_analytics(db, product, metric_key, as_of, window)
    if cached:
        return SpikeDetectionResponse(**cached)

    df = crud.get_records_as_dataframe(db, product, start_date, end_date)

    # Drop rows with null avg_price — spike detection needs actual values
    df = df.dropna(subset=["Avg Price"])

    spikes_df = detect_price_spikes(df, threshold=threshold, window=window)

    spike_records = [
        PriceSpikeRecord(
            record_date=row["Date"],
            product=row["Product"],
            avg_price=row["Avg Price"],
            rolling_avg=round(row["rolling_avg"], 2),
            spike_pct=round(row["spike_pct"], 2),
        )
        for _, row in spikes_df.iterrows()
    ]

    resp = SpikeDetectionResponse(
        product=product,
        threshold_pct=threshold * 100,
        window_days=window,
        spikes=spike_records,
    )
    crud.set_cached_analytics(db, product, metric_key, as_of, jsonable_encoder(resp), window)
    return resp


# ── GET /analytics/trend ─────────────────────────────────────────────────────

@router.get(
    "/trend",
    response_model=TrendResponse,
    summary="Price trend summary",
    description="Returns overall % change, highest/lowest price, mean, and volatility.",
)
def get_trend(
    product: str = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    as_of = end_date or crud.get_latest_date_for_product(db, product)
    if not as_of:
        raise HTTPException(status_code=404, detail=f"No price data found for product '{product}'.")
        
    metric_key = f"trend_{start_date.isoformat()}" if start_date else "trend"
    cached = crud.get_cached_analytics(db, product, metric_key, as_of)
    if cached:
        return TrendResponse(**cached)

    df = crud.get_records_as_dataframe(db, product, start_date, end_date)

    # Drop rows with null avg_price — trend needs actual values
    df = df.dropna(subset=["Avg Price"])

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No valid price data found for product '{product}'.",
        )

    result = calculate_price_trend(df)
    resp = TrendResponse(**result)
    crud.set_cached_analytics(db, product, metric_key, as_of, jsonable_encoder(resp))
    return resp


# ── GET /analytics/moving-average ────────────────────────────────────────────

@router.get(
    "/moving-average",
    summary="Moving average time series",
    description="Return the daily Avg Price enriched with a rolling moving average.",
)
def get_moving_avg(
    product: str = Query(...),
    window: int = Query(7, ge=2, le=90),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    as_of = end_date or crud.get_latest_date_for_product(db, product)
    if not as_of:
        return []

    metric_key = f"moving_average_{start_date.isoformat()}" if start_date else "moving_average"
    cached = crud.get_cached_analytics(db, product, metric_key, as_of, window)
    if cached:
        return cached

    df = crud.get_records_as_dataframe(db, product, start_date, end_date)

    # Drop rows with null avg_price — can't compute moving average on NaN
    df = df.dropna(subset=["Avg Price"])

    if df.empty:
        return []

    enriched = get_moving_average(df, window=window)

    # Serialize Date to ISO string for clean JSON output
    enriched["Date"] = enriched["Date"].astype(str)

    result = enriched.to_dict(orient="records")
    crud.set_cached_analytics(db, product, metric_key, as_of, jsonable_encoder(result), window)
    return result


# ── POST /analytics/forecast ─────────────────────────────────────────────────

@router.post(
    "/forecast",
    response_model=ForecastResponse,
    summary="ARIMA price forecast",
    description="Generate a multi-day ARIMA price forecast with 95% confidence intervals.",
)
def forecast_prices(
    payload: ForecastRequest,
    db: Session = Depends(get_db),
):
    as_of = crud.get_latest_date_for_product(db, payload.product)
    if not as_of:
        raise HTTPException(status_code=404, detail=f"No price data found for product '{payload.product}'.")
        
    cached = crud.get_cached_analytics(db, payload.product, "forecast", as_of, payload.steps)
    if cached:
        return ForecastResponse(**cached)

    df = crud.get_records_as_dataframe(db, payload.product)

    # Drop rows with null avg_price — ARIMA needs continuous numeric data
    df = df.dropna(subset=["Avg Price"])

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No valid price data found for product '{payload.product}'.",
        )

    forecast_points = _forecast_service.predict(df, steps=payload.steps)

    resp = ForecastResponse(
        product=payload.product,
        model_used=f"ARIMA{_forecast_service.model_order}",
        forecast=forecast_points,
    )
    crud.set_cached_analytics(db, payload.product, "forecast", as_of, jsonable_encoder(resp), payload.steps)
    return resp