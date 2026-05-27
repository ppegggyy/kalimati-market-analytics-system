# tests/test_etl.py
import sys
import os
import pandas as pd
import pytest

# Add Data Engineering to sys.path so we can import the pipeline
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_ENG_DIR = os.path.join(PROJECT_ROOT, "Data Engineering")
if DATA_ENG_DIR not in sys.path:
    sys.path.append(DATA_ENG_DIR)

from data_extraction_pipeline import DataPipeline

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
