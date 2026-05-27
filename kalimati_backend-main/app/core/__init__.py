# app/core/__init__.py
from .config import settings
from .analytics import (
    calculate_volatility,
    detect_price_spikes,
    calculate_price_trend,
    get_moving_average,
)

__all__ = [
    "settings",
    "calculate_volatility",
    "detect_price_spikes",
    "calculate_price_trend",
    "get_moving_average",
]
