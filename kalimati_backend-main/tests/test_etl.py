# tests/test_etl.py
import pandas as pd
import pytest

# Import the ETL pipeline from its actual package location — this is the
# same module the live background scheduler (app/services/scheduler.py)
# imports and runs, so testing it here actually exercises production code.
#
# NOTE: a top-level standalone copy also exists at data_engineering/ for
# ad-hoc/offline use, but it is not part of the installable "app" package
# and is not what the running server uses, so it is intentionally not
# imported here.
from app.services.data_extraction_pipeline import DataPipeline


@pytest.fixture
def sample_raw_df():
    # Convert dates to actual datetime objects as expected by transform()
    return pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-03"]),
        "Product": [" Tomato Big(Nepali) ", " Tomato Big(Nepali) ", "Tomato Big(Nepali)", "Tomato Big(Nepali)"],
        "Unit": ["kg", "kg", "kg", "kg"],
        "Max Price": [80.0, 80.0, -10.0, 85.0],
        "Min Price": [60.0, 60.0, 65.0, 75.0],
        "Avg Price": [70.0, 70.0, 50.0, 80.0]
    })

def test_etl_transform(sample_raw_df):
    pipeline = DataPipeline()
    result = pipeline.transform(sample_raw_df)
    clean_df = result.dataframe
    
    # Check deduplication (2024-01-01 has a duplicate)
    assert len(clean_df) == 3, "Duplicates should be removed"
    
    # Check product normalization
    assert clean_df["product"].iloc[0] == "Tomato Big (Nepali)"
    
    # Check unit normalization
    assert clean_df["unit"].iloc[0] == "KG"
    
    # Check negative price nulling and imputation
    # Day 2 Max Price was -10, which should be nulled out and then imputed.
    row_day2 = clean_df[clean_df["date"] == pd.to_datetime("2024-01-02")].iloc[0]
    assert row_day2["max_price"] > 0, "Negative price should be corrected/imputed"
