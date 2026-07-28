# app/services/scheduler.py
import logging
import threading
from datetime import date, timedelta

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


# Use the bundled data extraction pipeline
try:
    from app.services.data_extraction_pipeline import DataPipeline, DatabaseLoader
except ImportError as e:
    logging.getLogger(__name__).error(f"Could not import ETL pipeline: {e}")
    DataPipeline = None
    DatabaseLoader = None

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def _get_engine():
    """Return the SQLAlchemy engine."""
    from app.db.session import engine
    return engine


def _purge_stale_cache(engine):
    """Delete analytics_cache rows older than 14 days to prevent unbounded growth."""
    from sqlalchemy import text
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM analytics_cache WHERE updated_at < datetime('now', '-14 days')")
                if "sqlite" in engine.url.drivername else
                text("DELETE FROM analytics_cache WHERE updated_at < NOW() - INTERVAL '14 days'")
            )
            deleted = result.rowcount
        if deleted:
            logger.info("Cache cleanup — purged %d stale analytics_cache rows.", deleted)
    except Exception as e:
        logger.warning("Cache cleanup failed (non-fatal): %s", e)


def run_etl_job():
    """Incremental ETL: fetch only the days missing from the database."""
    if not DataPipeline or not DatabaseLoader:
        logger.error("ETL pipeline modules not found. Skipping scheduled job.")
        return

    logger.info("Starting scheduled ETL background job...")
    try:
        engine = _get_engine()
        loader = DatabaseLoader(engine)
        pipeline = DataPipeline()

        last_date = loader.get_last_date()
        if last_date is None:
            logger.info("Database is empty. Skipping scheduled run (requires manual parquet load).")
            return

        # Convert to date if it's a datetime or string (SQLite returns str)
        if hasattr(last_date, 'date'):
            last_date = last_date.date()
        elif isinstance(last_date, str):
            from datetime import datetime
            last_date = datetime.strptime(last_date, "%Y-%m-%d").date()

        today = date.today()
        fetch_start = last_date + timedelta(days=1)

        if fetch_start > today:
            logger.info("Database is already up to date (last_date=%s). Nothing to fetch.", last_date)
            return

        logger.info("Fetching data from %s to %s (%d days).", fetch_start, today, (today - fetch_start).days + 1)

        # Use targeted date range instead of full-year sweep
        pipeline.START_DATE = fetch_start
        pipeline.END_DATE = today

        extraction = pipeline.extract()

        if extraction.dataframe.empty:
            logger.info("No new data extracted from GitHub.")
            return

        transformation = pipeline.transform(extraction.dataframe)
        clean_df = transformation.dataframe
        clean_df = clean_df[clean_df["date"] > pd.Timestamp(last_date)]

        if clean_df.empty:
            logger.info("No new rows to insert after filtering by last_date.")
            return

        inserted = loader.load(clean_df)
        logger.info("Scheduled ETL complete — %d new rows inserted.", inserted)

        # Purge stale cache so analytics recalculate with fresh data
        _purge_stale_cache(engine)

    except Exception as e:
        logger.exception("Scheduled ETL failed with error: %s", e)


def run_startup_etl():
    """Fire ETL immediately on a background thread (non-blocking startup)."""
    logger.info("Startup ETL catch-up triggered.")
    thread = threading.Thread(target=run_etl_job, daemon=True)
    thread.start()


def start_scheduler():
    """Start the background scheduler for ETL jobs."""
    if not scheduler.running:
        # Run every day at 02:00 AM
        scheduler.add_job(
            run_etl_job,
            CronTrigger(hour=2, minute=0),
            id="daily_etl_job",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Background ETL scheduler started.")


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background ETL scheduler stopped.")
