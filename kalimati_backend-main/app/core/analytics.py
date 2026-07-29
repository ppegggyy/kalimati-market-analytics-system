# app/core/analytics.py
# ─────────────────────────────────────────────────────────────────
# Core business-logic for price analytics.
#
# All functions accept a Pandas DataFrame whose columns match the
# original Kalimati CSV headers (with spaces):
#   Date | Product | Unit | Max Price | Min Price | Avg Price
# ─────────────────────────────────────────────────────────────────

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from app.core.config import settings


# ── Public API ─────────────────────────────────────────────────────

def calculate_volatility(df: pd.DataFrame) -> float:
    """Calculate price volatility as the standard deviation of Avg Price.

    Args:
        df: DataFrame filtered to a single product & date range.
            Must contain columns: ["Date", "Avg Price"].

    Returns:
        Standard deviation (float). Returns 0.0 for < 2 valid records.
    """
    if df.empty:
        return 0.0
    # Guard against NaN values: np.std() propagates NaN across the whole
    # result if ANY element is NaN (unlike pandas' NaN-skipping .std()).
    # All current API routes already dropna() before calling this, but
    # this function is also used directly (e.g. test_accuracy.py) and
    # may gain new callers, so it should be safe on its own.
    prices = df["Avg Price"].dropna().values
    if len(prices) < 2:
        return 0.0
    return float(np.std(prices))


def detect_price_spikes(
    df: pd.DataFrame,
    threshold: Optional[float] = None,
    window: Optional[int] = None,
) -> pd.DataFrame:
    """Flag daily records where Avg Price exceeds the rolling mean by
    more than `threshold` fraction.

    Algorithm:
        rolling_avg(t) = mean(Avg Price[t-window : t-1])
        spike if: Avg Price(t) > rolling_avg(t) * (1 + threshold)

    Args:
        df:         DataFrame for ONE product, sorted by Date.
                    Must contain ["Date", "Avg Price"].
        threshold:  Fractional spike threshold (default from config).
                    E.g. 0.30 means 30 % above rolling average.
        window:     Rolling window in days (default from config).

    Returns:
        DataFrame containing only spiked rows with extra columns:
            rolling_avg  — the N-day rolling average
            spike_pct    — % deviation from rolling average
    """
    threshold = threshold if threshold is not None else settings.price_spike_threshold
    window = window if window is not None else settings.spike_window_days

    if df.empty:
        return pd.DataFrame()

    # Work on a copy to avoid mutating the caller's DataFrame
    work = df.copy().sort_values("Date").reset_index(drop=True)

    # Rolling average uses PAST `window` rows (min_periods=1 avoids NaNs
    # for rows 1..window-1, which still have at least one prior observation).
    work["rolling_avg"] = (
        work["Avg Price"]
        .rolling(window=window, min_periods=1)
        .mean()
        .shift(1)           # shift so today's price is not in its own average
    )

    # The very first row has no prior observation at all, so its
    # rolling_avg is genuinely undefined — NOT "the mean of the whole
    # series" (which would include the row's own price and could
    # spuriously mask or manufacture a spike on day one). Drop it from
    # spike consideration rather than back-filling with a contaminated
    # baseline.
    work = work.dropna(subset=["rolling_avg"]).reset_index(drop=True)

    if work.empty:
        return pd.DataFrame(columns=["Date", "Product", "Avg Price", "rolling_avg", "spike_pct"])

    # Compute deviation as a fraction
    work["spike_pct"] = (
        (work["Avg Price"] - work["rolling_avg"]) / work["rolling_avg"]
    ) * 100

    # Filter to spikes only
    spikes = work[work["spike_pct"] / 100 > threshold].copy()
    return spikes[["Date", "Product", "Avg Price", "rolling_avg", "spike_pct"]]


def calculate_price_trend(df: pd.DataFrame) -> dict:
    """Compute summary trend statistics for a product over a period.

    Returns a dictionary with:
        - overall_change_pct : % change from first to last record
        - highest_price      : max Avg Price and its date
        - lowest_price       : min Avg Price and its date
        - mean_price         : simple arithmetic mean
        - volatility         : std-dev of Avg Price

    Args:
        df: DataFrame for ONE product sorted by Date.
    """
    if df.empty:
        return {}

    work = df.sort_values("Date")
    first_price = float(work.iloc[0]["Avg Price"])
    last_price = float(work.iloc[-1]["Avg Price"])

    overall_change_pct = (
        ((last_price - first_price) / first_price) * 100
        if first_price != 0 else 0.0
    )

    max_idx = work["Avg Price"].idxmax()
    min_idx = work["Avg Price"].idxmin()

    return {
        "overall_change_pct": round(overall_change_pct, 2),
        "highest_price": {
            "value": float(work.loc[max_idx, "Avg Price"]),
            "date": str(work.loc[max_idx, "Date"]),
        },
        "lowest_price": {
            "value": float(work.loc[min_idx, "Avg Price"]),
            "date": str(work.loc[min_idx, "Date"]),
        },
        "mean_price": round(float(work["Avg Price"].mean()), 2),
        "volatility": round(calculate_volatility(work), 2),
    }


def get_moving_average(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    """Add a moving-average column to the DataFrame.

    Useful for chart overlays in the frontend.

    Args:
        df:     DataFrame with ["Date", "Avg Price"] columns.
        window: Rolling window size in days.

    Returns:
        Copy of df with an additional column "moving_avg_{window}d".
    """
    work = df.copy().sort_values("Date")
    col_name = f"moving_avg_{window}d"
    work[col_name] = (
        work["Avg Price"].rolling(window=window, min_periods=1).mean()
    )
    return work
