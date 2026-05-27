"""
DataPipeline – Complete ETL (Step 1 + Step 2)
=============================================
Kalimati Wholesale Market Price Monitoring System

Stage 1 – extract()  : Fetch & consolidate raw CSVs from GitHub.
Stage 2 – transform(): Clean, normalise, impute, and enrich.
Stage 3 – validate() : [TBD]
Stage 4 – load()     : [TBD]
"""

import calendar
import io
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DataPipeline")

# ---------------------------------------------------------------------------
# Extraction constants
# ---------------------------------------------------------------------------
GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/ErKiran/kalimati/master/data/csv"
)
EXPECTED_COLUMNS = {"Date", "Product", "Unit", "Max Price", "Min Price", "Avg Price"}
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
]

# ---------------------------------------------------------------------------
# Transformation constants
# ---------------------------------------------------------------------------
PRODUCT_NORMALISATION_MAP: dict[str, str] = {
    # ── Tomatoes ──────────────────────────────────────────────────────────
    "Tomato Big(Nepali)":        "Tomato Big (Nepali)",
    "Tomato Big(Indian)":        "Tomato Big (Indian)",
    "Tomato Small(Local)":       "Tomato Small (Local)",
    "Tomato Small(Tunnel)":      "Tomato Small (Tunnel)",
    "Tomato Small(Indian)":      "Tomato Small (Indian)",
    "Tomato Small(Terai)":       "Tomato Small (Terai)",

    # ── Potatoes ──────────────────────────────────────────────────────────
    "Potato Red(Indian)":        "Potato Red (Indian)",
    "Potato Red(Long)":          "Potato Red (Long)",
    "Potato Red(Mude)":          "Potato Red (Mude)",
    "Potato Red(Round)":         "Potato Red (Round)",

    # ── Onions ────────────────────────────────────────────────────────────
    "Onion Dry (Indian)":        "Onion Dry (Indian)",
    "Onion Dry (Chinese)":       "Onion Dry (Chinese)",

    # ── Cauliflower ───────────────────────────────────────────────────────
    "Cauli Local":               "Cauliflower (Local)",
    "Cauli Local(Jyapu)":        "Cauliflower Local (Jyapu)",
    "Cauli Terai":               "Cauliflower (Terai)",

    # ── Cabbage ───────────────────────────────────────────────────────────
    "Cabbage":                   "Cabbage",
    "Cabbage(Local)":            "Cabbage (Local)",
    "Cabbage(Terai)":            "Cabbage (Terai)",
    "Red Cabbbage":              "Cabbage (Red)",

    # ── Broccoli (typo fix) ───────────────────────────────────────────────
    "Brocauli":                  "Broccoli",
    "Broccoli":                  "Broccoli",

    # ── Radish (spelling fix) ─────────────────────────────────────────────
    "Raddish Red":               "Radish (Red)",
    "Raddish White(Hybrid)":     "Radish White (Hybrid)",
    "Raddish White(Local)":      "Radish White (Local)",

    # ── Chives (likely mistranscribed as Clive) ───────────────────────────
    "Clive Dry":                 "Chive (Dry)",
    "Clive Green":               "Chive (Green)",

    # ── Parsley (typo fix) ────────────────────────────────────────────────
    "Parseley":                  "Parsley",
    "Parsley":                   "Parsley",

    # ── Garlic ────────────────────────────────────────────────────────────
    "Garlic Dry Chinese":        "Garlic Dry (Chinese)",
    "Garlic Dry Nepali":         "Garlic Dry (Nepali)",

    # ── Carrot ────────────────────────────────────────────────────────────
    "Carrot(Local)":             "Carrot (Local)",
    "Carrot(Terai)":             "Carrot (Terai)",

    # ── Cucumber ──────────────────────────────────────────────────────────
    "Cucumber(Hybrid)":          "Cucumber (Hybrid)",
    "Cucumber(Local)":           "Cucumber (Local)",
    "Cucumber(LocalCross)":      "Cucumber (Local Cross)",

    # ── Chilli ────────────────────────────────────────────────────────────
    "Chilli Green(Akbare)":      "Chilli Green (Akbare)",
    "Chilli Green(Bullet)":      "Chilli Green (Bullet)",
    "Chilli Green(Long)":        "Chilli Green (Long)",
    "Chilli Green(Machhe)":      "Chilli Green (Machhe)",

    # ── Brinjal ───────────────────────────────────────────────────────────
    "Brinjal Long":              "Brinjal (Long)",
    "Brinjal Round":             "Brinjal (Round)",

    # ── Gourd ─────────────────────────────────────────────────────────────
    "Bottle Gourd":              "Bottle Gourd",
    "Bitter Gourd":              "Bitter Gourd",
    "Smooth Gourd":              "Smooth Gourd",
    "Snake Gourd":               "Snake Gourd",
    "Sponge Gourd":              "Sponge Gourd",
    "Pointed Gourd(Local)":      "Pointed Gourd (Local)",
    "Pointed Gourd(Terai)":      "Pointed Gourd (Terai)",

    # ── Squash ────────────────────────────────────────────────────────────
    "Squash(Long)":              "Squash (Long)",
    "Squash(Round)":             "Squash (Round)",

    # ── Apple ─────────────────────────────────────────────────────────────
    "Apple(Fuji)":               "Apple (Fuji)",
    "Apple(Jholey)":             "Apple (Jholey)",

    # ── Banana ────────────────────────────────────────────────────────────
    "Banana(Malbhog)":           "Banana (Malbhog)",
    "Banana(Nepali)":            "Banana (Nepali)",

    # ── Mango ─────────────────────────────────────────────────────────────
    "Mango(Calcutte)":           "Mango (Calcutta)",
    "Mango(Chousa)":             "Mango (Chousa)",
    "Mango(Dushari)":            "Mango (Dushari)",
    "Mango(Maldah)":             "Mango (Maldah)",

    # ── Grapes ────────────────────────────────────────────────────────────
    "Grapes(Black)":             "Grapes (Black)",
    "Grapes(Green)":             "Grapes (Green)",

    # ── Litchi ────────────────────────────────────────────────────────────
    "Litchi(Indian)":            "Litchi (Indian)",
    "Litchi(Local)":             "Litchi (Local)",

    # ── Watermelon ────────────────────────────────────────────────────────
    "Water Melon(Dotted)":       "Watermelon (Dotted)",
    "Water Melon(Green)":        "Watermelon (Green)",

    # ── Pear ──────────────────────────────────────────────────────────────
    "Pear(Chinese)":             "Pear (Chinese)",
    "Pear(Local)":               "Pear (Local)",

    # ── Papaya ────────────────────────────────────────────────────────────
    "Papaya(Indian)":            "Papaya (Indian)",
    "Papaya(Nepali)":            "Papaya (Nepali)",

    # ── Orange ────────────────────────────────────────────────────────────
    "Orange(Indian)":            "Orange (Indian)",
    "Orange(Nepali)":            "Orange (Nepali)",

    # ── French Bean ───────────────────────────────────────────────────────
    "French Bean(Hybrid)":       "French Bean (Hybrid)",
    "French Bean(Local)":        "French Bean (Local)",
    "French Bean(Rajma)":        "French Bean (Rajma)",

    # ── Mushroom ──────────────────────────────────────────────────────────
    "Mushroom(Button)":          "Mushroom (Button)",
    "Mushroom(Kanya)":           "Mushroom (Kanya)",

    # ── Mustard Leaf ──────────────────────────────────────────────────────
    "Brd Leaf Mustard":          "Broad Leaf Mustard",

    # ── Fish ──────────────────────────────────────────────────────────────
    "Fish Fresh(Bachuwa)":       "Fish Fresh (Bachuwa)",
    "Fish Fresh(Chhadi)":        "Fish Fresh (Chhadi)",
    "Fish Fresh(Mungari)":       "Fish Fresh (Mungari)",
    "Fish Fresh(Rahu)":          "Fish Fresh (Rahu)",

    # ── Cowpea ────────────────────────────────────────────────────────────
    "Cow pea(Long)":             "Cowpea (Long)",
    "Cowpea(Short)":             "Cowpea (Short)",
}


UNIT_NORMALISATION_MAP: dict[str, str] = {
    "kg": "KG", "Kg": "KG", "KG": "KG",
    "gm": "GM", "Gm": "GM", "GM": "GM",
    "pcs": "PCS", "Pcs": "PCS", "PCS": "PCS",
    "dozen": "DOZEN", "Dozen": "DOZEN", "DOZEN": "DOZEN",
}

PRICE_COLS = ["max_price", "min_price", "avg_price"]
FFILL_MAX_GAP       = 3
INTERPOLATE_MAX_GAP = 14


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------
@dataclass
class ExtractionResult:
    dataframe: pd.DataFrame
    files_attempted: int = 0
    files_loaded: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    errors: list[dict] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.files_attempted == 0:
            return 0.0
        return round(self.files_loaded / self.files_attempted * 100, 2)

    def summary(self) -> str:
        return (
            f"Extraction complete — "
            f"attempted={self.files_attempted}, "
            f"loaded={self.files_loaded}, "
            f"skipped(404)={self.files_skipped}, "
            f"failed={self.files_failed}, "
            f"success_rate={self.success_rate}%, "
            f"total_rows={len(self.dataframe)}"
        )


@dataclass
class TransformationResult:
    dataframe: pd.DataFrame
    rows_before_dedup: int = 0
    duplicate_rows_dropped: int = 0
    negative_price_rows_nulled: int = 0
    cells_ffilled: int = 0
    cells_interpolated: int = 0
    cells_left_nan: int = 0
    products_remapped: int = 0
    units_remapped: int = 0
    columns_renamed: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"Transformation complete — "
            f"duplicates_dropped={self.duplicate_rows_dropped}, "
            f"negative_cells_nulled={self.negative_price_rows_nulled}, "
            f"cells_ffilled={self.cells_ffilled}, "
            f"cells_interpolated={self.cells_interpolated}, "
            f"cells_left_nan={self.cells_left_nan}, "
            f"products_remapped={self.products_remapped}, "
            f"output_rows={len(self.dataframe)}"
        )


# ---------------------------------------------------------------------------
# DataPipeline
# ---------------------------------------------------------------------------
class DataPipeline:

    # Stage 1 settings
    START_YEAR: int = 2023
    END_YEAR: int = 2026
    REQUEST_TIMEOUT: int = 15
    RATE_LIMIT_DELAY: float = 0.05
    MAX_RETRIES: int = 3

    def __init__(self):
        self._session = self._build_session()

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 1 – EXTRACTION
    # ══════════════════════════════════════════════════════════════════════

    def extract(self) -> ExtractionResult:
        logger.info("Starting extraction: years %d–%d", self.START_YEAR, self.END_YEAR)
        result = ExtractionResult(dataframe=pd.DataFrame())
        frames: list[pd.DataFrame] = []
        url_list = self._generate_urls()
        result.files_attempted = len(url_list)

        for url, year, month, day in url_list:
            time.sleep(self.RATE_LIMIT_DELAY)
            df = self._fetch_csv(url, year, month, day, result)
            if df is not None:
                frames.append(df)
                result.files_loaded += 1

        if frames:
            result.dataframe = pd.concat(frames, ignore_index=True)
            logger.info(result.summary())
        else:
            logger.warning("No data was extracted.")
        return result

    def _generate_urls(self) -> list[tuple[str, int, int, int]]:
        entries = []
        for year in range(self.START_YEAR, self.END_YEAR + 1):
            for month in range(1, 13):
                for day in range(1, calendar.monthrange(year, month)[1] + 1):
                    url = f"{GITHUB_RAW_BASE}/{year}/{month:02d}/{day:02d}.csv"
                    entries.append((url, year, month, day))
        logger.info("Generated %d candidate URLs.", len(entries))
        return entries

    def _fetch_csv(
        self,
        url: str,
        year: int,
        month: int,
        day: int,
        result: ExtractionResult,
    ) -> Optional[pd.DataFrame]:
        date_tag = f"{year}-{month:02d}-{day:02d}"
        try:
            response = self._session.get(url, timeout=self.REQUEST_TIMEOUT)
            if response.status_code == 404:
                logger.debug("404 – no data for %s", date_tag)
                result.files_skipped += 1
                return None
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            self._record_error(result, date_tag, url, "HTTPError", str(exc))
            return None
        except requests.exceptions.Timeout:
            self._record_error(result, date_tag, url, "Timeout", "Request timed out")
            return None
        except requests.exceptions.RequestException as exc:
            self._record_error(result, date_tag, url, "NetworkError", str(exc))
            return None

        try:
            df = pd.read_csv(io.StringIO(response.text))
        except Exception as exc:
            self._record_error(result, date_tag, url, "CSVParseError", str(exc))
            return None

        missing_cols = EXPECTED_COLUMNS - set(df.columns)
        if missing_cols:
            self._record_error(result, date_tag, url, "ColumnMismatch", f"Missing: {missing_cols}")
            return None

        if df.empty:
            result.files_skipped += 1
            return None

        df["Date"] = self._parse_date_column(df["Date"], date_tag)
        if df["Date"].isna().all():
            self._record_error(result, date_tag, url, "DateParseFailure", "All dates unparseable")
            return None

        df["_source_url"] = url
        df["_ingested_at"] = datetime.now(timezone.utc)
        return df

    @staticmethod
    def _parse_date_column(series: pd.Series, date_tag: str) -> pd.Series:
        for fmt in DATE_FORMATS:
            try:
                return pd.to_datetime(series, format=fmt, errors="raise")
            except (ValueError, TypeError):
                continue
        return pd.to_datetime(series, dayfirst=True, errors="coerce")

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({"User-Agent": "KalimatiPriceMonitor/1.0"})
        return session

    @staticmethod
    def _record_error(result: ExtractionResult, date_tag, url, error_type, detail):
        logger.warning("[%s] %s – %s", date_tag, error_type, detail)
        result.files_failed += 1
        result.errors.append({
            "date": date_tag, "url": url,
            "error_type": error_type, "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 2 – TRANSFORMATION
    # ══════════════════════════════════════════════════════════════════════

    def transform(self, df: pd.DataFrame) -> TransformationResult:
        result = TransformationResult(dataframe=df.copy())
        logger.info("Starting transformation on %d rows.", len(df))

        result.dataframe, result.columns_renamed = self._rename_columns(result.dataframe)
        result.dataframe, result.products_remapped, result.units_remapped = self._normalise_products(result.dataframe)
        result.rows_before_dedup = len(result.dataframe)
        result.dataframe, result.duplicate_rows_dropped = self._deduplicate(result.dataframe)
        result.dataframe, result.negative_price_rows_nulled = self._validate_prices(result.dataframe)
        result.dataframe, result.cells_ffilled, result.cells_interpolated, result.cells_left_nan = self._tiered_imputation(result.dataframe)
        result.dataframe = self._enrich(result.dataframe)

        logger.info(result.summary())
        return result

    @staticmethod
    def _rename_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        rename_map = {
            "Date": "date", "Product": "product", "Unit": "unit",
            "Max Price": "max_price", "Min Price": "min_price", "Avg Price": "avg_price",
        }
        actual_map = {k: v for k, v in rename_map.items() if k in df.columns}
        return df.rename(columns=actual_map), list(actual_map.values())

    @staticmethod
    def _normalise_products(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
        original_products = df["product"].str.strip()
        mapped_products = original_products.map(PRODUCT_NORMALISATION_MAP)
        products_remapped = mapped_products.notna().sum()
        df["product"] = mapped_products.fillna(original_products)

        original_units = df["unit"].str.strip()
        mapped_units = original_units.map(UNIT_NORMALISATION_MAP)
        units_remapped = mapped_units.notna().sum()
        df["unit"] = mapped_units.fillna(original_units.str.upper().str.strip())

        logger.info("Normalisation: %d product rows, %d unit rows remapped.", products_remapped, units_remapped)
        return df, int(products_remapped), int(units_remapped)

    @staticmethod
    def _deduplicate(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        before = len(df)
        df = (
            df.sort_values("avg_price", ascending=False)
            .drop_duplicates(subset=["date", "product"], keep="first")
            .sort_values(["date", "product"])
            .reset_index(drop=True)
        )
        dropped = before - len(df)
        logger.info("Deduplication: dropped %d rows.", dropped)
        return df, dropped

    @staticmethod
    def _validate_prices(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        price_block = df[PRICE_COLS]
        negative_mask = price_block < 0
        cells_nulled = int(negative_mask.values.sum())
        if cells_nulled:
            df[PRICE_COLS] = price_block.where(~negative_mask, other=np.nan)
            logger.warning("Validation: nulled %d negative price cells.", cells_nulled)

        order_violated = (
            df["min_price"].notna() & df["max_price"].notna() & df["avg_price"].notna() &
            ((df["min_price"] > df["avg_price"]) | (df["avg_price"] > df["max_price"]))
        )
        if order_violated.any():
            df.loc[order_violated, "avg_price"] = (
                (df.loc[order_violated, "min_price"] + df.loc[order_violated, "max_price"]) / 2
            )
            logger.warning("Validation: recomputed avg_price for %d rows.", order_violated.sum())

        return df, cells_nulled

    def _tiered_imputation(self, df: pd.DataFrame) -> tuple[pd.DataFrame, int, int, int]:
        logger.info("Starting tiered imputation...")
        full_date_range = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="D")
        products = df["product"].unique()
        frames, ff, interp, left = [], 0, 0, 0

        for product in products:
            pdf, f, i, l = self._impute_product(
                df[df["product"] == product].copy(), full_date_range, product
            )
            frames.append(pdf)
            ff += f; interp += i; left += l

        result_df = (
            pd.concat(frames, ignore_index=True)
            .sort_values(["date", "product"])
            .reset_index(drop=True)
        )
        logger.info("Imputation: ffilled=%d, interpolated=%d, left_nan=%d.", ff, interp, left)
        return result_df, ff, interp, left

    @staticmethod
    def _impute_product(
        pdf: pd.DataFrame,
        full_date_range: pd.DatetimeIndex,
        product: str,
    ) -> tuple[pd.DataFrame, int, int, int]:
        pdf = pdf.set_index("date").reindex(full_date_range)
        pdf.index.name = "date"
        pdf["product"] = product
        pdf["unit"] = pdf["unit"].ffill().bfill()

        ff_count = interp_count = nan_count = 0

        for col in PRICE_COLS:
            series = pdf[col].copy()
            was_nan = series.isna()
            if not was_nan.any():
                continue

            not_nan = series.notna()
            gap_id   = (~not_nan).cumsum()
            gap_size = series.isna().groupby(gap_id).transform("sum")

            short_mask  = was_nan & (gap_size <= FFILL_MAX_GAP)
            medium_mask = was_nan & (gap_size > FFILL_MAX_GAP) & (gap_size <= INTERPOLATE_MAX_GAP)

            if short_mask.any():
                series = series.where(~short_mask, other=series.ffill())
            if medium_mask.any():
                series = series.where(~medium_mask, other=series.interpolate(method="linear", limit_direction="both"))

            ff_count     += int(short_mask.sum())
            interp_count += int(medium_mask.sum())
            nan_count    += int((series.isna() & was_nan).sum())
            pdf[col] = series

        return pdf.reset_index(), ff_count, interp_count, nan_count

    @staticmethod
    def _enrich(df: pd.DataFrame) -> pd.DataFrame:
        df["price_spread"]   = df["max_price"] - df["min_price"]
        df["price_midpoint"] = (df["max_price"] + df["min_price"]) / 2
        dt = df["date"].dt
        df["year"]         = dt.year.astype("int16")
        df["month"]        = dt.month.astype("int8")
        df["week_of_year"] = dt.isocalendar().week.astype("int8")
        df["day_of_week"]  = dt.dayofweek.astype("int8")
        df["is_weekend"]   = dt.dayofweek >= 5
        df["_transformed_at"] = datetime.now(timezone.utc)
        return df


# ---------------------------------------------------------------------------
# STAGE 3 - LOAD
# ---------------------------------------------------------------------------
import psycopg2
from psycopg2.extras import execute_values

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "kalimati",
    "user":     "postgres",
    "password": "admin123"   
}

class DatabaseLoader:
    def __init__(self, config: dict):
        self.config = config

    def get_connection(self):
        return psycopg2.connect(**self.config)

    def get_last_date(self) -> Optional[str]:
        """Check what the latest date already in the database is."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(date) FROM prices;")
                result = cur.fetchone()[0]
                return result  # returns None if table is empty

    def load(self, df: pd.DataFrame) -> int:
        """
        Idempotent upsert — inserts rows, skips duplicates.
        Returns number of rows inserted.
        """
        # Replace NaN with None so PostgreSQL gets NULL
        df = df.replace({float('nan'): None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)

        records = [
            (
                row.date,
                row.product,
                row.unit,
                row.max_price,
                row.min_price,
                row.avg_price,
                row.price_spread,
                row.price_midpoint,
                int(row.year)         if row.year         is not None else None,
                int(row.month)        if row.month        is not None else None,
                int(row.week_of_year) if row.week_of_year is not None else None,
                int(row.day_of_week)  if row.day_of_week  is not None else None,
                row.is_weekend,
                row._source_url      if hasattr(row, '_source_url')      else None,
                row._ingested_at     if hasattr(row, '_ingested_at')     else None,
                row._transformed_at  if hasattr(row, '_transformed_at')  else None,
            )
            for row in df.itertuples(index=False)
        ]

        insert_sql = """
            INSERT INTO prices (
                date, product, unit,
                max_price, min_price, avg_price,
                price_spread, price_midpoint,
                year, month, week_of_year, day_of_week,
                is_weekend, source_url, ingested_at, transformed_at
            ) VALUES %s
            ON CONFLICT (date, product) DO NOTHING;
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, insert_sql, records, page_size=1000)
                inserted = cur.rowcount
            conn.commit()

        logger.info("Load complete — %d rows inserted.", inserted)
        return inserted


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    pipeline = DataPipeline()
    loader   = DatabaseLoader(DB_CONFIG)

    # Check what's already in the database
    last_date = loader.get_last_date()

    if last_date is None:
        # First run — load everything from parquet
        logger.info("Database is empty. Loading full dataset.")
        clean_df = pd.read_parquet("kalimati_clean.parquet")
    else:
        # Incremental run — only fetch new data from GitHub
        logger.info("Last date in DB: %s. Fetching new data only.", last_date)
        pipeline.START_YEAR  = last_date.year
        extraction = pipeline.extract()
        extraction.dataframe.to_parquet("kalimati_raw.parquet", index=False)
        transformation = pipeline.transform(extraction.dataframe)
        clean_df = transformation.dataframe
        # Only keep rows newer than what's already in the database
        clean_df = clean_df[clean_df["date"] > pd.Timestamp(last_date)]

    inserted = loader.load(clean_df)
    print(f"\nDone — {inserted} new rows inserted into PostgreSQL.")