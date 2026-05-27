# app/core/config.py
# ─────────────────────────────────────────────────────────────────
# Centralised application settings loaded from the .env file.
# Any team member can change behaviour by editing .env — no code
# changes required.
# ─────────────────────────────────────────────────────────────────

import os
from dotenv import load_dotenv  # pip install python-dotenv (already in requirements.txt)

# Load .env file into environment variables before reading them.
load_dotenv()

try:
    # Preferred: pydantic-settings gives full type validation.
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        """Application-wide configuration (pydantic-settings variant).

        Values are read from environment variables / .env file.
        Pydantic automatically coerces types (e.g. str -> float).
        """

        # --- General ---
        app_name: str = "Kalimati Price Monitor"
        app_version: str = "1.0.0"
        debug: bool = True
        port: int = 8000

        # --- Database (hand to DB Expert) ---
        database_url: str = "sqlite:///./kalimati.db"
        postgres_host: str = "localhost"
        postgres_port: str = "5432"
        postgres_db: str = "kalimati"
        postgres_user: str = "postgres"
        postgres_password: str = "admin123"

        # --- Analytics thresholds ---
        # A price is flagged as a "spike" when it exceeds the rolling
        # N-day average by more than this fraction (0.30 = 30 %).
        price_spike_threshold: float = 0.30
        spike_window_days: int = 7

        # Pydantic-settings v2 config
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
        )

except ImportError:
    # Fallback: plain class reading os.environ (works without pydantic-settings).
    # Install pydantic-settings when network is available for full validation.
    class Settings:  # type: ignore[no-redef]
        """Fallback settings class using os.environ directly."""

        app_name: str = os.getenv("APP_NAME", "Kalimati Price Monitor")
        app_version: str = os.getenv("APP_VERSION", "1.0.0")
        debug: bool = os.getenv("DEBUG", "True").lower() == "true"
        database_url: str = os.getenv("DATABASE_URL", "sqlite:///./kalimati.db")
        price_spike_threshold: float = float(os.getenv("PRICE_SPIKE_THRESHOLD", "0.30"))
        spike_window_days: int = int(os.getenv("SPIKE_WINDOW_DAYS", "7"))


# Singleton instance — import this everywhere else in the project.
settings = Settings()
