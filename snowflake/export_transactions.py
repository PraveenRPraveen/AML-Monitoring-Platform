import os
from sqlalchemy import create_engine, text

SOURCE_URL = os.getenv("DATABASE_URL")
SNOWFLAKE_URL = os.getenv("SNOWFLAKE_URL")

if not SOURCE_URL:
    raise RuntimeError("DATABASE_URL is required")

engine = create_engine(SOURCE_URL)
with engine.connect() as connection:
    result = connection.execute(text("SELECT id, event_id, amount, currency, transaction_type, occurred_at, status FROM transactions"))
    print("[SNOWFLAKE EXPORT] Retrieved", len(result.fetchall()), "transaction rows")

print("Use SNOWFLAKE_URL and your approved connector to load staged CSV/Parquet data into Snowflake.")
