# app/schemas/price.py
# ─────────────────────────────────────────────────────────────────
# Pydantic schemas for request/response validation.
#
# PriceRecordBase        – shared fields (Optional for reads, required for creates)
# PriceRecordCreate      – strict: all prices required for inserts
# PriceRecordRead        – relaxed: handles NULL prices from database
# ─────────────────────────────────────────────────────────────────

from datetime import date as date_type
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Read-side base (nullable fields — database has ~14,500 rows with NULL prices) ──

class PriceRecordRead(BaseModel):
    """Schema for reading price records FROM the database.

    Fields are Optional because the dataset contains rows where prices
    are NULL (seasonal products, market holidays).
    """
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: int = Field(..., description="Primary key")
    record_date: date_type = Field(..., alias="Date")
    product: str = Field(..., alias="Product")
    unit: Optional[str] = Field(None, alias="Unit")
    max_price: Optional[float] = Field(None, alias="Max Price")
    min_price: Optional[float] = Field(None, alias="Min Price")
    avg_price: Optional[float] = Field(None, alias="Avg Price")

    @field_validator("max_price", "min_price", "avg_price", mode="before")
    @classmethod
    def coerce_price(cls, v):
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Price must be numeric, got: {v!r}") from exc


# ── Write-side base (all prices required for inserts) ────────────────────────

class PriceRecordCreate(BaseModel):
    """Schema for creating new price records — all prices required."""
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    record_date: date_type = Field(..., alias="Date")
    product: str = Field(..., alias="Product")
    unit: str = Field(..., alias="Unit")
    max_price: float = Field(..., alias="Max Price", ge=0)
    min_price: float = Field(..., alias="Min Price", ge=0)
    avg_price: float = Field(..., alias="Avg Price", ge=0)

    @field_validator("max_price", "min_price", "avg_price", mode="before")
    @classmethod
    def coerce_price(cls, v):
        try:
            return float(v)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Price must be numeric, got: {v!r}") from exc


# ── Analytics response schemas ───────────────────────────────────────────────

class VolatilityResponse(BaseModel):
    product: str
    unit: str
    start_date: date_type
    end_date: date_type
    std_dev_avg_price: float
    record_count: int


class PriceSpikeRecord(BaseModel):
    record_date: date_type
    product: str
    avg_price: float
    rolling_avg: float
    spike_pct: float


class SpikeDetectionResponse(BaseModel):
    product: str
    threshold_pct: float
    window_days: int
    spikes: List[PriceSpikeRecord]


class TrendResponse(BaseModel):
    """Type-safe response for the /analytics/trend endpoint."""
    overall_change_pct: float
    highest_price: dict
    lowest_price: dict
    mean_price: float
    volatility: float


class ForecastRequest(BaseModel):
    product: str
    steps: int = Field(7, ge=1, le=90)


class ForecastPoint(BaseModel):
    record_date: date_type
    predicted_avg_price: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class ForecastResponse(BaseModel):
    product: str
    model_used: str = "ARIMA"
    forecast: List[ForecastPoint]
