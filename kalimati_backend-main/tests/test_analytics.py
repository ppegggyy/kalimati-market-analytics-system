# tests/test_analytics.py
# ─────────────────────────────────────────────────────────────────
# Unit tests for the core analytics functions.
# Run: pytest tests/ -v
# ─────────────────────────────────────────────────────────────────

import pandas as pd
import pytest

from app.core.analytics import (
    calculate_price_trend,
    calculate_volatility,
    detect_price_spikes,
    get_moving_average,
)


# ── Fixtures ───────────────────────────────────────────────────────

@pytest.fixture()
def sample_df() -> pd.DataFrame:
    """10-day price series for 'Tomato Big(Nepali)'."""
    return pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=10, freq="D"),
        "Product": "Tomato Big(Nepali)",
        "Unit": "KG",
        "Max Price": [80, 85, 90, 200, 88, 82, 79, 95, 91, 87],
        "Min Price": [60, 62, 65, 150, 66, 60, 58, 70, 68, 65],
        "Avg Price": [70, 73, 77, 175, 77, 71, 68, 82, 79, 76],
    })


# ── Volatility tests ───────────────────────────────────────────────

def test_volatility_returns_float(sample_df):
    result = calculate_volatility(sample_df)
    assert isinstance(result, float)
    assert result > 0


def test_volatility_empty_df():
    assert calculate_volatility(pd.DataFrame()) == 0.0


# ── Spike detection tests ──────────────────────────────────────────

def test_spike_detection_finds_spike(sample_df):
    """Day 4 (Avg Price = 175) should be flagged as a spike."""
    spikes = detect_price_spikes(sample_df, threshold=0.30, window=3)
    assert not spikes.empty, "Expected at least one spike to be detected"


def test_spike_detection_empty_df():
    spikes = detect_price_spikes(pd.DataFrame(), threshold=0.30, window=7)
    assert spikes.empty


# ── Trend tests ────────────────────────────────────────────────────

def test_price_trend_keys(sample_df):
    trend = calculate_price_trend(sample_df)
    expected_keys = {
        "overall_change_pct", "highest_price",
        "lowest_price", "mean_price", "volatility"
    }
    assert expected_keys.issubset(trend.keys())


def test_price_trend_empty_df():
    assert calculate_price_trend(pd.DataFrame()) == {}


# ── Moving average tests ───────────────────────────────────────────

def test_moving_average_column_added(sample_df):
    result = get_moving_average(sample_df, window=3)
    assert "moving_avg_3d" in result.columns
    assert len(result) == len(sample_df)
