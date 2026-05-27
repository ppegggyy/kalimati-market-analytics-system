# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import pandas as pd
from datetime import date

from app.main import app

client = TestClient(app)

@patch("app.api.prices.crud.get_unique_products")
def test_get_products(mock_get_unique_products):
    mock_get_unique_products.return_value = ["Tomato Big (Nepali)", "Potato Red"]
    response = client.get("/api/v1/prices/products")
    assert response.status_code == 200
    assert response.json() == ["Tomato Big (Nepali)", "Potato Red"]

@patch("app.api.prices.crud.get_latest_prices")
def test_get_latest_prices(mock_get_latest_prices):
    class MockRecord:
        def __init__(self):
            self.id = 1
            self.product = "Tomato Big (Nepali)"
            self.unit = "KG"
            self.max_price = 80
            self.min_price = 60
            self.avg_price = 70
            self.date = date(2024, 1, 10)
            self.Date = date(2024, 1, 10)
    mock_get_latest_prices.return_value = [MockRecord()]
    
    response = client.get("/api/v1/prices/latest")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["Product"] == "Tomato Big (Nepali)"
    assert data[0]["Avg Price"] == 70.0

@patch("app.api.analytics.crud")
def test_get_trend_api(mock_crud):
    mock_crud.get_latest_date_for_product.return_value = date(2024, 1, 10)
    mock_crud.get_cached_analytics.return_value = None
    
    df = pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=10, freq="D"),
        "Product": "Tomato Big (Nepali)",
        "Unit": "KG",
        "Max Price": [80]*10,
        "Min Price": [60]*10,
        "Avg Price": [70, 72, 74, 76, 78, 80, 82, 84, 86, 88],
    })
    mock_crud.get_records_as_dataframe.return_value = df
    
    response = client.get("/api/v1/analytics/trend?product=Tomato%20Big%20(Nepali)")
    assert response.status_code == 200
    data = response.json()
    assert data["overall_change_pct"] > 0
    assert data["highest_price"]["value"] == 88.0
    
    # Assert cache was set
    mock_crud.set_cached_analytics.assert_called_once()
