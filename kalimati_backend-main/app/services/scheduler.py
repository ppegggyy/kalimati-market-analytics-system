# app/services/scheduler.py
import logging
import sys
import os
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings

# Add the Data Engineering folder to sys.path so we can import the pipeline
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
DATA_ENG_DIR = os.path.join(PROJECT_ROOT, "Data Engineering")
if DATA_ENG_DIR not in sys.path:
    sys.path.append(DATA_ENG_DIR)

try:
    from data_extraction_pipeline import DataPipeline, DatabaseLoader
except ImportError as e:
    logging.getLogger(__name__).error(f"Could not import ETL pipeline: {e}")
    DataPipeline = None
    DatabaseLoader = None

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

def run_etl_job():
    if not DataPipeline or not DatabaseLoader:
        logger.error("ETL pipeline modules not found. Skipping scheduled job.")
        return
        
    logger.info("Starting scheduled ETL background job...")
    try:
        pipeline = DataPipeline()
        
        # Parse database URL to create psycopg2 config for the loader
        from app.db.session import engine
        url = engine.url
        db_config = {
            "host": url.host,
            "port": url.port or 5432,
            "dbname": url.database,
            "user": url.username,
            "password": url.password
        }
        loader = DatabaseLoader(db_config)
        
        last_date = loader.get_last_date()
        if last_date is None:
            logger.info("Database is empty. Skipping scheduled run (requires manual parquet load).")
            return
            
        logger.info(f"Last date in DB: {last_date}. Fetching new data only.")
        pipeline.START_YEAR = last_date.year
        extraction = pipeline.extract()
        
        if extraction.dataframe.empty:
            logger.info("No new data extracted.")
            return
            
        transformation = pipeline.transform(extraction.dataframe)
        clean_df = transformation.dataframe
        clean_df = clean_df[clean_df["date"] > pd.Timestamp(last_date)]
        
        if clean_df.empty:
            logger.info("No new rows to insert after filtering by last_date.")
            return
            
        inserted = loader.load(clean_df)
        logger.info(f"Scheduled ETL complete — {inserted} new rows inserted.")
    except Exception as e:
        logger.exception(f"Scheduled ETL failed with error: {e}")

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
