# Kalimati Price Monitor — Setup Guide
## VS Code · Windows · PowerShell

---

## 1. Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.11+ | https://python.org |
| Git | any | https://git-scm.com |
| VS Code | any | https://code.visualstudio.com |

> **Verify Python is installed:**
> ```powershell
> python --version
> # Expected: Python 3.11.x
> ```

---

## 2. Clone / Open the Project

```powershell
# Navigate to where you want the project
cd C:\Users\YourName\Projects

# If using Git
git clone <repo-url> kalimati_backend
cd kalimati_backend

# OR open an existing folder
cd C:\path\to\kalimati_backend
code .          # opens VS Code
```

---

## 3. Create & Activate a Virtual Environment

```powershell
# Create the virtual environment (run once)
python -m venv venv

# Activate it (run every time you open a new terminal)
.\venv\Scripts\Activate.ps1
```

> **PowerShell Execution Policy error?** Run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then activate again.

You should see `(venv)` at the start of your prompt when active.

---

## 4. Install Dependencies

```powershell
# Upgrade pip first (good practice)
python -m pip install --upgrade pip

# Install all project dependencies
pip install -r requirements.txt
```

> This installs: FastAPI, Uvicorn, Pydantic, Pandas, NumPy,
> SQLAlchemy, statsmodels, scikit-learn, requests, and more (all versions
> pinned in requirements.txt for reproducibility).

---

## 5. Configure Environment Variables (optional)

No `.env` file is required to run the project — `app/core/config.py`
defines sensible defaults for everything (SQLite database, debug mode
on, default analytics thresholds), so you can skip straight to Step 6.

If you want to override any setting (e.g. to point at a real Postgres
instance), create your own `.env` file in the project root — there
isn't one checked into the repo by default:

```powershell
code .env    # creates a new file
```

Key settings you can set in it:

| Variable | Default | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `sqlite:///./kalimati.db` | DB Expert: change to Postgres |
| `PRICE_SPIKE_THRESHOLD` | `0.30` | 30 % spike threshold |
| `SPIKE_WINDOW_DAYS` | `7` | Rolling average window |

---

## 6. Run the Development Server

```powershell
# From the project root (where app/ folder is)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Creating database tables (if they do not exist)…
INFO:     Database tables ready.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 7. Explore the Interactive API Docs

Open your browser and go to:

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8000/docs | **Swagger UI** — click & test every endpoint |
| http://127.0.0.1:8000/redoc | **ReDoc** — clean reference documentation |
| http://127.0.0.1:8000/health | Health check (returns `{"status": "ok"}`) |

---

## 8. Run the Tests

```powershell
# Run all tests with verbose output
pytest tests/ -v

# Run a specific test file
pytest tests/test_analytics.py -v

# Run with coverage report
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 9. Database Setup (for the DB Expert)

### Option A — SQLite (default, zero config)
Works out of the box. The file `kalimati.db` is created automatically on first run.

### Option B — PostgreSQL (recommended for production)

```powershell
# Install psycopg2 driver
pip install psycopg2-binary

# Create/update your .env (see Step 5 — none is checked in by default)
# DATABASE_URL=postgresql://user:password@localhost:5432/kalimati_db
```

### Alembic Migrations (optional — not currently used)

The project currently manages the schema with SQLAlchemy's
`Base.metadata.create_all()` (see `app/main.py`), not Alembic, and
`alembic` is **not** in `requirements.txt`. If you want real migrations
instead of `create_all()`, install and set it up yourself:

```powershell
pip install alembic
alembic init migrations

# Edit migrations/env.py — add these two lines:
#   from app.db.session import Base
#   target_metadata = Base.metadata

alembic revision --autogenerate -m "initial_price_records_table"
alembic upgrade head
```

---

## 10. ARIMA Forecasting

`app/services/forecast_service.py` already contains a complete, working
ARIMA implementation (auto-selects the differencing order via an ADF
stationarity test, falls back to a flat forecast for short or constant
series). Nothing further is required to run it.

```powershell
# statsmodels is already installed via requirements.txt
# To verify:
python -c "import statsmodels; print(statsmodels.__version__)"
```

If you want to extend it further:
1. Swap in a different model in `ForecastService.train()` / `predict()`.
2. Optionally persist trained models: `joblib.dump(model, "models/tomato.pkl")`.
3. Update the `model_used` field returned by `/analytics/forecast` accordingly.

---

## 11. Project Structure Reference

```
kalimati_backend/
│
├── app/
│   ├── main.py                  ← FastAPI app entry-point, CORS, lifespan
│   │
│   ├── api/
│   │   ├── __init__.py          ← Aggregates all routers
│   │   ├── prices.py            ← CRUD endpoints  (/api/v1/prices)
│   │   └── analytics.py         ← Analytics endpoints (/api/v1/analytics)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            ← Settings (all have defaults; .env optional)
│   │   └── analytics.py         ← Business logic (spikes, volatility, trend)
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── price.py             ← Pydantic models with CSV field aliases
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py           ← SQLAlchemy engine + get_db() dependency
│   │   ├── models.py            ← ORM models (PriceRecord, AnalyticsCache)
│   │   ├── bootstrap.py         ← Postgres-only DB object setup, runs at startup
│   │   └── crud.py              ← DB queries
│   │
│   └── services/
│       ├── __init__.py
│       ├── forecast_service.py          ← ARIMA forecasting
│       ├── scheduler.py                 ← Background ETL + cache-purge jobs
│       └── data_extraction_pipeline.py  ← ETL used by the live app
│
├── tests/
│   ├── test_analytics.py        ← Unit tests for core analytics
│   ├── test_api.py              ← API tests (mocked DB layer)
│   └── test_etl.py              ← ETL transform tests
│
├── test_accuracy.py             ← Standalone forecast-accuracy script; expects a
│                                 local Postgres DB, not run as part of `pytest`
├── requirements.txt             ← All Python dependencies (version-pinned)
└── SETUP_GUIDE.md               ← This file
```

> **Note:** `data_engineering/data_extraction_pipeline.py` (outside `app/`)
> is an older standalone copy of the ETL script, kept for manual/offline
> use. It is **not** imported by the running app — the live scheduler
> uses `app/services/data_extraction_pipeline.py`. If you edit the ETL
> logic, edit the copy under `app/services/`.

---

## 12. Useful VS Code Extensions

Install these from the Extensions panel (`Ctrl+Shift+X`):

| Extension | Purpose |
|-----------|---------|
| `ms-python.python` | Python language support |
| `ms-python.pylint` | Linting / PEP8 checks |
| `ms-python.black-formatter` | Auto-format on save |
| `rangav.vscode-thunder-client` | REST API client (like Postman, built-in) |
| `mtxr.sqltools` | SQL database browser |

---

## 13. Common Issues & Fixes

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'app'` | Make sure you're in the project root, not inside `app/` |
| `(venv)` not showing | Re-run `.\venv\Scripts\Activate.ps1` |
| Port 8000 already in use | `uvicorn app.main:app --reload --port 8001` |
| SQLite locked error | Stop other running server instances |
| Pydantic `ValidationError` on import | Check that column alias names match the CSV exactly |
