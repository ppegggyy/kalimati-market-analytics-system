# Kalimati Market Analytics System - System Context

This document provides a comprehensive overview of the Kalimati Market Analytics System, detailing its architecture, components, and how they interact.

## 1. System Overview
The Kalimati Market Analytics System is a production-ready, full-stack application designed to track, analyze, and forecast vegetable and fruit prices from the Kalimati Wholesale Market in Nepal. It consists of three major components:
- **Data Engineering (ETL Pipeline):** Automates the extraction, cleaning, imputation, and loading of daily price data.
- **Backend (FastAPI):** Exposes a REST API to serve historical data, analytics (moving averages, trends, volatility), and machine-learning-based forecasts (ARIMA).
- **Frontend (React + Vite):** Provides an interactive dashboard for users to visualize data, compare volatilities, and view future price predictions.

---

## 2. Data Engineering (ETL Pipeline)
**Location:** `data_engineering/data_extraction_pipeline.py`

The ETL pipeline handles ingesting raw CSV files from a GitHub repository and securely transforming them before loading them into a PostgreSQL database.

### 2.1 Extraction (Stage 1)
- **Source:** Iterates through dates (Years 2023–2026, Months 1-12, Days 1-31) and fetches raw CSVs from `https://raw.githubusercontent.com/ErKiran/kalimati/master/data/csv/{YYYY}/{MM}/{DD}.csv`.
- **Handling Errors:** Utilizes retry mechanisms, rate limiting, and robust date-parsing (supporting multiple date formats). Identifies missing days (HTTP 404s) and logs them without failing.
- **Output:** Combines fetched daily CSVs into a raw Pandas DataFrame.

### 2.2 Transformation (Stage 2)
- **Column Mapping:** Normalizes columns to standard names (`Date` -> `date`, `Product` -> `product`, `Max Price` -> `max_price`, etc.).
- **Data Normalisation:** Maps diverse spellings of products (e.g., `Tomato Big(Nepali)` -> `Tomato Big (Nepali)`, `Brocauli` -> `Broccoli`) and units (e.g., `kg`, `Kg`, `gm`) to standardized strings using predefined dictionaries (`PRODUCT_NORMALISATION_MAP`, `UNIT_NORMALISATION_MAP`).
- **Deduplication:** Removes duplicated records by keeping the one with the highest average price for a given date and product.
- **Price Validation:** Identifies negative prices and replaces them with `NaN`. Checks for price order violations (where `min_price > avg_price` or `avg_price > max_price`) and corrects the `avg_price` to the mathematical midpoint of `min_price` and `max_price`.
- **Tiered Imputation:** 
  - **Short gaps (<= 3 days):** Imputed using Forward Fill (ffill).
  - **Medium gaps (4 to 14 days):** Imputed using Linear Interpolation.
  - **Long gaps (> 14 days):** Left as `NaN` to prevent distorting real data.
- **Enrichment:** Adds derived columns such as `price_spread` (max - min), `price_midpoint`, `year`, `month`, `week_of_year`, `day_of_week`, `is_weekend`, and tracking columns (`_source_url`, `_ingested_at`, `_transformed_at`).

### 2.3 Load (Stage 3)
- **Database:** Inserts cleaned data into a PostgreSQL database (`kalimati`).
- **Idempotency:** Implements idempotent upserts using `psycopg2.extras.execute_values` and an `ON CONFLICT (date, product) DO NOTHING` strategy.
- **Incremental Loading:** Before fetching data, the pipeline queries the database for the `MAX(date)`. If records exist, the pipeline only downloads data newer than the `MAX(date)`, saving bandwidth and time. If the DB is empty, it can load from a cached `kalimati_clean.parquet` file.

---

## 3. Backend (FastAPI)
**Location:** `kalimati_backend-main/`

The backend serves the frontend and orchestrates data access, analytics, and background scheduling.

### 3.1 Architecture & Setup
- **Framework:** FastAPI with Uvicorn server.
- **Database ORM:** SQLAlchemy with Pydantic for validation and serialization, and Alembic for database migrations. Default development supports SQLite; Production supports PostgreSQL.
- **App Lifespan:** On startup (`app/main.py`), the app automatically ensures database objects exist, starts a background scheduler (`start_scheduler()`), and gracefully tears them down upon exit.

### 3.2 Key API Endpoints
All routes are prefixed with `/api/v1/`.

**Price Endpoints (`/prices`):**
- `/products`: Returns a distinct list of all tracked product names.
- `/latest`: Returns the most recent price record for every product in the database.

**Analytics Endpoints (`/analytics`):**
- `/moving-average`: Calculates the moving average (default 7 days) of prices over a selected timeframe.
- `/volatility`: Calculates the standard deviation of the average price and counts records for a product over a given period.
- `/trend`: Returns overall statistical metrics including percentage change, highest price, lowest price, mean, and volatility over time.
- `/forecast` (POST): Predicts future prices (e.g., 30 steps ahead) using an ARIMA (AutoRegressive Integrated Moving Average) statistical model via `statsmodels`.

### 3.3 Analytics & ML Logic
- **Core Analytics:** Contained in `app/core/analytics.py`, which identifies price spikes (default 30% jump) against a 7-day rolling window.
- **Forecasting:** Housed in `app/services/forecast_service.py`. The forecasting service fits an ARIMA model to the historical data, enabling predictive price queries.

---

## 4. Frontend (React + Vite)
**Location:** `kalimati_frontend-main/`

The frontend consumes the FastAPI backend, offering a visually appealing representation of the data.

### 4.1 Tech Stack
- **Framework:** React combined with Vite for fast bundling and HMR.
- **Routing:** React Router DOM (`BrowserRouter`).
- **Styling:** Standard CSS (`global.css`, `components.css`) ensuring high responsiveness and aesthetics without over-reliance on massive CSS frameworks.

### 4.2 Application Structure
- **Pages:**
  - **Dashboard (`/`):** The primary view displaying high-level metrics, moving averages, and current prices.
  - **Volatility Comparison (`/volatility`):** Allows users to select multiple products and contrast their price volatility across chosen timeframes.
  - **Forecast (`/forecast`):** Renders the future price projection utilizing the backend's ARIMA forecast endpoint.
- **Components:** Modular UI elements including `Sidebar`, `Header`, and `MobileNav` to ensure seamless mobile and desktop navigation.

### 4.3 API Client (`src/api.js`)
Handles all external data fetching using standard `fetch`:
- Seamlessly switches between the Vite development proxy (`/api/v1` mapping to `localhost:8000`) and the production URL (`https://kalimati-backend.onrender.com/api/v1`) depending on the build environment (`import.meta.env.DEV`).
- Exports strongly typed/commented asynchronous functions: `fetchProducts`, `fetchMovingAverage`, `fetchVolatility`, `fetchTrend`, `fetchLatestPrices`, and `fetchForecast`.
