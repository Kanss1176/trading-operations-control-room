"""
Trading Operations Control Room
Creates the SQLite database and loads the synthetic CSV data into it.
"""

from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "database" / "trading_ops.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"

tables = {
    "instrument_master": "instrument_master.csv",
    "market_prices": "market_prices.csv",
    "corporate_actions": "corporate_actions.csv",
    "expected_events": "expected_events.csv",
    "trading_events": "trading_events.csv",
    "settlement_status": "settlement_status.csv",
}

with sqlite3.connect(DB_PATH) as conn:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    for table_name, filename in tables.items():
        df = pd.read_csv(RAW_DIR / filename)
        df.to_sql(table_name, conn, if_exists="append", index=False)
        print(f"Loaded {len(df)} rows into '{table_name}'")

print(f"\nDatabase created successfully at: {DB_PATH}")