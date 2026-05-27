from sqlalchemy import text

from app.db.session import engine


def ensure_db_objects() -> None:
    """
    Ensure required indexes/tables exist in PostgreSQL.

    This is intentionally idempotent via IF NOT EXISTS.
    """
    if engine.dialect.name != "postgresql":
        return

    ddls = [
        "CREATE INDEX IF NOT EXISTS prices_product_date_idx "
        "ON public.prices USING btree (product, date)",
        "CREATE INDEX IF NOT EXISTS prices_product_idx "
        "ON public.prices USING btree (product)",
        "CREATE INDEX IF NOT EXISTS prices_product_date_desc_idx "
        "ON public.prices USING btree (product, date DESC)",
        """
        CREATE TABLE IF NOT EXISTS public.analytics_cache (
          id           BIGSERIAL PRIMARY KEY,
          product      VARCHAR(100) NOT NULL,
          metric_type  TEXT NOT NULL,
          window_days  INTEGER,
          as_of_date   DATE NOT NULL,
          payload      JSONB NOT NULL,
          created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          UNIQUE (product, metric_type, window_days, as_of_date)
        )
        """,
        "CREATE INDEX IF NOT EXISTS analytics_cache_lookup_idx "
        "ON public.analytics_cache USING btree "
        "(product, metric_type, window_days, as_of_date DESC)",
    ]

    with engine.begin() as conn:
        for ddl in ddls:
            conn.execute(text(ddl))

