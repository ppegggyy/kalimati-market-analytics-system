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
> SQLAlchemy, Alembic, statsmodels, scikit-learn, pytest, and more.

---

## 5. Configure Environment Variables

```powershell
# Copy the example env file
Copy-Item .env .env.local     # optional — keep .env as-is for dev

# Open .env in VS Code and review settings
code .env
```

Key settings to check:

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

# Update .env
# DATABASE_URL=postgresql://user:password@localhost:5432/kalimati_db
```

### Alembic Migrations (DB Expert)

```powershell
# Initialise Alembic (run once)
alembic init migrations

# Edit migrations/env.py — add these two lines:
#   from app.db.session import Base
#   target_metadata = Base.metadata

# Generate first migration
alembic revision --autogenerate -m "initial_price_records_table"

# Apply migration
alembic upgrade head

# Roll back if needed
alembic downgrade -1
```

---

## 10. ARIMA Model Setup (for the ML Expert)

```powershell
# statsmodels is already installed via requirements.txt
# To verify:
python -c "import statsmodels; print(statsmodels.__version__)"

# Open the placeholder file
code app/services/forecast_service.py
```

**Steps for the ML Expert:**
1. Implement `ForecastService.train()` with real ARIMA fitting.
2. Implement `ForecastService.predict()` with real `model.forecast()` call.
3. Optionally persist models: `joblib.dump(model, "models/tomato.pkl")`.
4. Update `model_used` field in `analytics.py` to the real model name.

---

## 11. Project Structure Reference

```
kalimati_backend/
│
├── app/
│   ├── main.py                  ← FastAPI app entry-point
│   │
│   ├── api/
│   │   ├── __init__.py          ← Aggregates all routers
│   │   ├── prices.py            ← CRUD endpoints  (/api/v1/prices)
│   │   └── analytics.py         ← Analytics endpoints (/api/v1/analytics)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            ← Settings (reads .env)
│   │   └── analytics.py         ← Business logic (spikes, volatility, trend)
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── price.py             ← Pydantic models with CSV field aliases
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py           ← SQLAlchemy engine + get_db() dependency
│   │   ├── models.py            ← ORM model (PriceRecord table)
│   │   └── crud.py              ← DB queries (placeholder → DB Expert)
│   │
│   └── services/
│       ├── __init__.py
│       └── forecast_service.py  ← ARIMA wrapper (placeholder → ML Expert)
│
├── tests/
│   └── test_analytics.py        ← Unit tests for core analytics
│
├── .env                         ← Environment variables (do not commit secrets)
├── requirements.txt             ← All Python dependencies
└── SETUP_GUIDE.md               ← This file
```

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
