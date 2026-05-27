# app/services/forecast_service.py

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

import pandas as pd

from app.schemas.price import ForecastPoint

logger = logging.getLogger(__name__)


class ForecastService:
    """ARIMA forecasting service.

    Designed as an injectable dependency — the API layer calls predict()
    and expects list[ForecastPoint] back. train() is called internally
    on every predict() call so forecasts always use the latest data.

    Model choice: ARIMA(2, d, 1) with d determined per-product by an
    Augmented Dickey-Fuller stationarity test, following Udari &
    Hemachandra (2024) who found (2,1,1) optimal for vegetable wholesale
    price series.
    """

    def __init__(self, model_order: tuple[int, int, int] = (2, 1, 1)):
        self.model_order = model_order
        self._model = None
        self._last_price: float = 100.0

    # ── Training ──────────────────────────────────────────────────────────────

    def train(self, df: pd.DataFrame) -> None:
        """Fit an ARIMA model on the historical Avg Price series.

        Steps:
          1. Build a daily DatetimeIndex series; forward-fill short gaps.
          2. Run ADF test to determine differencing order d.
          3. Fit ARIMA(2, d, 1).
        """
        from statsmodels.tsa.arima.model import ARIMA
        from statsmodels.tsa.stattools import adfuller

        series = (
            df.set_index("Date")["Avg Price"]
            .asfreq("D")
            .ffill()
            .dropna()
        )

        if len(series) < 30:
            logger.warning(
                "Series too short for ARIMA (%d rows). Need at least 30. "
                "Falling back to flat forecast.",
                len(series),
            )
            self._model = None
            self._last_price = float(series.iloc[-1]) if len(series) > 0 else 100.0
            return

        # --- ADF stationarity test to pick d ---
        p_value = adfuller(series)[1]
        d = 0
        if p_value > 0.05:                               # non-stationary
            d = 1
            if adfuller(series.diff().dropna())[1] > 0.05:
                d = 2                                     # still non-stationary after 1 diff

        self.model_order = (2, d, 1)
        logger.info("ADF p-value=%.4f → ARIMA order set to %s", p_value, self.model_order)

        try:
            arima = ARIMA(series, order=self.model_order)
            self._model = arima.fit()
            logger.info(
                "ARIMA%s fitted successfully. AIC=%.2f",
                self.model_order,
                self._model.aic,
            )
            self._last_price = float(series.iloc[-1])
        except Exception as exc:
            logger.error("ARIMA fitting failed: %s", exc)
            self._model = None
            self._last_price = float(series.iloc[-1])

    # ── Prediction ────────────────────────────────────────────────────────────

    def predict(
        self,
        df: pd.DataFrame,
        steps: int = 30,
        last_date: Optional[date] = None,
    ) -> list[ForecastPoint]:
        """Generate a steps-day price forecast with 95% confidence intervals.

        Re-trains the model on every call so forecasts always reflect the
        latest available data.

        Returns:
            list[ForecastPoint] with record_date, predicted_avg_price,
            lower_bound, upper_bound for each future day.
        """
        self.train(df)

        if last_date is None:
            last_date = pd.to_datetime(df["Date"].max()).date()

        # --- Flat fallback if ARIMA failed to fit ---
        if self._model is None:
            logger.warning("ARIMA unavailable — returning flat forecast.")
            p = self._last_price
            return [
                ForecastPoint(
                    record_date=last_date + timedelta(days=i + 1),   # Fix 14: record_date=, not date=
                    predicted_avg_price=round(p, 2),
                    lower_bound=round(p * 0.85, 2),
                    upper_bound=round(p * 1.15, 2),
                )
                for i in range(steps)
            ]

        # --- Real ARIMA forecast ---
        forecast_result = self._model.get_forecast(steps=steps)
        predicted_mean  = forecast_result.predicted_mean
        conf_int        = forecast_result.conf_int(alpha=0.05)   # 95 % CI

        points: list[ForecastPoint] = []
        for i in range(steps):
            predicted = float(predicted_mean.iloc[i])
            lower     = float(conf_int.iloc[i, 0])
            upper     = float(conf_int.iloc[i, 1])

            # Prices cannot be negative
            predicted = max(0.0, predicted)
            lower     = max(0.0, lower)
            upper     = max(0.0, upper)

            points.append(
                ForecastPoint(
                    record_date=last_date + timedelta(days=i + 1),   # Fix 14: record_date=, not date=
                    predicted_avg_price=round(predicted, 2),
                    lower_bound=round(lower, 2),
                    upper_bound=round(upper, 2),
                )
            )

        return points