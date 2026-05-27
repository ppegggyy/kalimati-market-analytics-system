# app/db/models.py

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from .session import Base


class PriceRecord(Base):
    """ORM model mapping to the existing 'prices' table in the kalimati database.

    The table already exists and is fully populated — do NOT run
    create_all() in a way that would drop or recreate it.
    """

    __tablename__ = "prices"   # Fix 3: was "price_records"

    # Primary key
    id             = Column(Integer, primary_key=True, index=True)

    # Core columns — Fix 5: nullable=True to match real schema
    date           = Column(Date,        nullable=False, index=True)
    product        = Column(String(100), nullable=False, index=True)
    unit           = Column(String(20),  nullable=True)   # was nullable=False
    max_price      = Column(Float,       nullable=True)   # was nullable=False
    min_price      = Column(Float,       nullable=True)   # was nullable=False
    avg_price      = Column(Float,       nullable=True)   # was nullable=False

    # Fix 4: missing computed columns now added
    price_spread   = Column(Float,                  nullable=True)
    price_midpoint = Column(Float,                  nullable=True)
    year           = Column(Integer,                nullable=True)
    month          = Column(Integer,                nullable=True)
    week_of_year   = Column(Integer,                nullable=True)
    day_of_week    = Column(Integer,                nullable=True)
    is_weekend     = Column(Boolean,                nullable=True)
    source_url     = Column(Text,                   nullable=True)
    ingested_at    = Column(DateTime(timezone=True), nullable=True)
    transformed_at = Column(DateTime(timezone=True), nullable=True)

    # Fix 6: Pydantic schema uses field name 'record_date'; ORM column is 'date'.
    # This property bridges the gap so from_attributes=True serialisation works.
    @property
    def record_date(self):
        return self.date

    def __repr__(self) -> str:
        return (
            f"<PriceRecord(id={self.id}, date={self.date}, "
            f"product={self.product!r}, avg={self.avg_price})>"
        )

class AnalyticsCache(Base):
    __tablename__ = "analytics_cache"

    id = Column(Integer, primary_key=True, index=True)
    product = Column(String(100), nullable=False)
    metric_type = Column(Text, nullable=False)
    window_days = Column(Integer, nullable=True)
    as_of_date = Column(Date, nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<AnalyticsCache(product={self.product!r}, "
            f"metric={self.metric_type}, as_of={self.as_of_date})>"
        )