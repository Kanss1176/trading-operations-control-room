"""
Trading Operations Control Room
Data quality validation checks.

Scans instrument, price and corporate action data for problems and
writes them out as a list of exceptions.
"""

from pathlib import Path
from datetime import datetime
import sqlite3
import uuid
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database" / "trading_ops.db"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

CONTROL_RUN_ID = f"CTRL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
RUN_TIMESTAMP = datetime.now().isoformat()

VALID_CURRENCIES = {"EUR", "USD", "GBP", "CHF"}
VALID_ASSET_CLASSES = {"Equity", "ETF", "Bond"}


def make_exception(exception_type, severity, source_table, record_reference,
                    instrument_id, description, recommended_action, owner_team):
    """Builds one standardised exception record."""
    return {
        "exception_id": str(uuid.uuid4()),
        "control_run_id": CONTROL_RUN_ID,
        "exception_type": exception_type,
        "severity": severity,
        "source_table": source_table,
        "record_reference": str(record_reference),
        "instrument_id": instrument_id,
        "description": description,
        "recommended_action": recommended_action,
        "owner_team": owner_team,
        "detected_at": RUN_TIMESTAMP,
        "status": "Open",
    }
def validate_instrument_master(df):
    """Checks the instrument master data for common reference-data problems."""
    exceptions = []

    # Rule: instrument_id must not be missing
    missing_ids = df[df["instrument_id"].isna()]
    for idx, row in missing_ids.iterrows():
        exceptions.append(make_exception(
            "Missing instrument ID", "Critical", "instrument_master", idx, None,
            "Instrument record has no instrument_id.",
            "Create or correct the internal instrument identifier.",
            "Reference Data"
        ))

    # Rule: ISIN must be unique
    duplicate_isins = df[df["isin"].duplicated(keep=False) & df["isin"].notna()]
    for _, row in duplicate_isins.iterrows():
        exceptions.append(make_exception(
            "Duplicate ISIN", "High", "instrument_master",
            row.get("instrument_id"), row.get("instrument_id"),
            f"ISIN {row.get('isin')} appears more than once.",
            "Validate security mapping and retain one authoritative record.",
            "Reference Data"
        ))

    # Rule: currency must be an approved code
    invalid_currency = df[~df["currency"].isin(VALID_CURRENCIES)]
    for _, row in invalid_currency.iterrows():
        exceptions.append(make_exception(
            "Invalid currency", "Medium", "instrument_master",
            row.get("instrument_id"), row.get("instrument_id"),
            f"Currency value '{row.get('currency')}' is not approved.",
            "Standardise to an ISO currency code.",
            "Reference Data"
        ))

    # Rule: asset class must be an approved type
    invalid_asset_class = df[~df["asset_class"].isin(VALID_ASSET_CLASSES)]
    for _, row in invalid_asset_class.iterrows():
        exceptions.append(make_exception(
            "Invalid asset class", "Medium", "instrument_master",
            row.get("instrument_id"), row.get("instrument_id"),
            f"Asset class '{row.get('asset_class')}' is not in the approved list.",
            "Correct asset class using approved taxonomy.",
            "Reference Data"
        ))

    return exceptions

def validate_market_prices(price_df, instrument_df):
    """Checks market price data for missing, invalid or unknown-instrument prices."""
    exceptions = []

    # Rule: every active instrument should have a price record
    active_instruments = instrument_df[instrument_df["active_flag"] == "Y"]["instrument_id"].dropna()
    price_instruments = set(price_df["instrument_id"].dropna())
    missing_prices = set(active_instruments) - price_instruments
    for instrument_id in missing_prices:
        exceptions.append(make_exception(
            "Missing market price", "High", "market_prices", instrument_id, instrument_id,
            "Active instrument has no market-price record in this control run.",
            "Check market data feed and re-ingest missing price.",
            "Market Data Operations"
        ))

    # Rule: close price must be positive, and high must not be below low
    invalid_price_rows = price_df[
        (price_df["close_price"].isna()) |
        (price_df["close_price"] <= 0) |
        (price_df["high_price"] < price_df["low_price"])
    ]
    for _, row in invalid_price_rows.iterrows():
        exceptions.append(make_exception(
            "Invalid market price", "High", "market_prices",
            row.get("price_id"), row.get("instrument_id"),
            "Price record has a missing/non-positive close price, or high price below low price.",
            "Quarantine record and validate source feed.",
            "Market Data Operations"
        ))

    # Rule: instrument referenced in a price record must exist in the instrument master
    unknown_instruments = price_df[~price_df["instrument_id"].isin(instrument_df["instrument_id"])]
    for _, row in unknown_instruments.iterrows():
        exceptions.append(make_exception(
            "Unknown instrument reference", "Critical", "market_prices",
            row.get("price_id"), row.get("instrument_id"),
            "Market price references an instrument absent from master data.",
            "Correct instrument mapping before processing.",
            "Market Data Operations"
        ))

    return exceptions


def validate_corporate_actions(df):
    """Checks corporate action data for duplicates and inconsistent dates/amounts."""
    exceptions = []

    # Rule: same instrument/type/date/amount combination shouldn't repeat
    duplicate_actions = df[df.duplicated(
        subset=["instrument_id", "action_type", "ex_date", "amount"], keep=False
    )]
    for _, row in duplicate_actions.iterrows():
        exceptions.append(make_exception(
            "Potential duplicate corporate action", "High", "corporate_actions",
            row.get("action_id"), row.get("instrument_id"),
            "Corporate action duplicates another event on instrument/type/date/amount.",
            "Validate source event and cancel duplicate if confirmed.",
            "Corporate Actions"
        ))

    # Rule: ex-date cannot be after payable date
    dates = df.copy()
    dates["ex_date"] = pd.to_datetime(dates["ex_date"], errors="coerce")
    dates["payable_date"] = pd.to_datetime(dates["payable_date"], errors="coerce")
    invalid_dates = dates[dates["ex_date"] > dates["payable_date"]]
    for _, row in invalid_dates.iterrows():
        exceptions.append(make_exception(
            "Invalid corporate action date sequence", "High", "corporate_actions",
            row.get("action_id"), row.get("instrument_id"),
            "Ex-date occurs after payable date.",
            "Validate official event dates and correct record.",
            "Corporate Actions"
        ))

    # Rule: dividend amount must be present and positive
    invalid_dividend = df[
        (df["action_type"] == "Dividend") &
        ((df["amount"].isna()) | (df["amount"] <= 0))
    ]
    for _, row in invalid_dividend.iterrows():
        exceptions.append(make_exception(
            "Invalid dividend amount", "High", "corporate_actions",
            row.get("action_id"), row.get("instrument_id"),
            "Dividend event has a missing or non-positive amount.",
            "Confirm event amount with official source.",
            "Corporate Actions"
        ))

    return exceptions

def load_tables():
    """Loads the tables we need to validate from the SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        instrument_df = pd.read_sql("SELECT * FROM instrument_master", conn)
        market_prices_df = pd.read_sql("SELECT * FROM market_prices", conn)
        corporate_actions_df = pd.read_sql("SELECT * FROM corporate_actions", conn)
    return instrument_df, market_prices_df, corporate_actions_df


def main():
    instrument_df, market_prices_df, corporate_actions_df = load_tables()

    exceptions = []
    exceptions.extend(validate_instrument_master(instrument_df))
    exceptions.extend(validate_market_prices(market_prices_df, instrument_df))
    exceptions.extend(validate_corporate_actions(corporate_actions_df))

    exceptions_df = pd.DataFrame(exceptions)

    # Save the exception queue as a CSV file
    exceptions_df.to_csv(PROCESSED_DIR / "exception_queue.csv", index=False)

    # Also save it into the database, and log this control run
    with sqlite3.connect(DB_PATH) as conn:
        if not exceptions_df.empty:
            exceptions_df.to_sql("data_quality_exceptions", conn, if_exists="append", index=False)

        records_checked = len(instrument_df) + len(market_prices_df) + len(corporate_actions_df)
        exceptions_found = len(exceptions_df)
        data_quality_score = max(0, round(100 - (exceptions_found / max(records_checked, 1) * 100), 2))

        control_log = pd.DataFrame([{
            "control_run_id": CONTROL_RUN_ID,
            "run_timestamp": RUN_TIMESTAMP,
            "records_checked": records_checked,
            "exceptions_found": exceptions_found,
            "data_quality_score": data_quality_score,
            "run_status": "Completed",
        }])
        control_log.to_sql("control_run_log", conn, if_exists="append", index=False)

    print(f"Control run completed: {CONTROL_RUN_ID}")
    print(f"Records checked: {records_checked}")
    print(f"Exceptions found: {exceptions_found}")
    print(f"Data quality score: {data_quality_score}%")
    print(f"\nException queue saved to: {PROCESSED_DIR / 'exception_queue.csv'}")


if __name__ == "__main__":
    main()