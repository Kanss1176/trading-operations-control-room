"""
Trading Operations Control Room
Reconciliation checks — expected vs processed corporate action events,
and settlement SLA monitoring.
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

TODAY = pd.Timestamp("2026-09-10")
SETTLEMENT_SLA_DAYS = 2


def make_exception(exception_type, severity, source_table, record_reference,
                    instrument_id, description, recommended_action, owner_team):
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


def load_tables():
    """Loads the tables needed for reconciliation from the SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        expected_df = pd.read_sql("SELECT * FROM expected_events", conn)
        trading_df = pd.read_sql("SELECT * FROM trading_events", conn)
        actions_df = pd.read_sql("SELECT * FROM corporate_actions", conn)
        settlement_df = pd.read_sql("SELECT * FROM settlement_status", conn)
    return expected_df, trading_df, actions_df, settlement_df

def check_missing_events(expected_df, trading_df):
    """Finds expected events that were never processed at all."""
    exceptions = []
    merged = expected_df.merge(
        trading_df[["action_id", "instrument_id", "event_id"]],
        on=["action_id", "instrument_id"], how="left"
    )
    missing = merged[merged["event_id"].isna()]
    for _, row in missing.iterrows():
        exceptions.append(make_exception(
            "Missing expected event", "Critical", "trading_events",
            row.get("expected_event_id"), row.get("instrument_id"),
            f"Expected event '{row.get('expected_event_type')}' due "
            f"{row.get('expected_processing_date')} was never processed.",
            "Confirm event source and create/repair the missing processing record.",
            row.get("owner_team", "Trading Operations")
        ))
    return exceptions


def check_late_events(expected_df, trading_df):
    """Finds events that were processed, but after their expected deadline."""
    exceptions = []
    merged = expected_df.merge(trading_df, on=["action_id", "instrument_id"], how="inner")
    merged["expected_processing_date"] = pd.to_datetime(merged["expected_processing_date"])
    merged["processed_date"] = pd.to_datetime(merged["processed_date"])
    late = merged[merged["processed_date"] > merged["expected_processing_date"]]
    for _, row in late.iterrows():
        days_late = (row["processed_date"] - row["expected_processing_date"]).days
        exceptions.append(make_exception(
            "Late event processing", "High", "trading_events",
            row.get("event_id"), row.get("instrument_id"),
            f"Event was processed {days_late} day(s) after the expected date.",
            "Investigate processing delay and confirm no downstream impact.",
            "Trading Operations"
        ))
    return exceptions


def check_amount_mismatches(actions_df, trading_df):
    """Finds processed events where the amount doesn't match the corporate action."""
    exceptions = []
    merged = actions_df.merge(trading_df, on="action_id", suffixes=("_expected", "_processed"))
    mismatches = merged[
        (merged["amount"].notna()) &
        ((merged["processed_amount"] - merged["amount"]).abs() > 0.01)
    ]
    for _, row in mismatches.iterrows():
        exceptions.append(make_exception(
            "Amount mismatch", "High", "trading_events",
            row.get("event_id"), row.get("instrument_id_expected"),
            f"Processed amount {row.get('processed_amount')} does not match "
            f"expected corporate action amount {row.get('amount')}.",
            "Reconcile the amount difference with the corporate actions team.",
            "Trading Operations"
        ))
    return exceptions


def check_duplicate_events(trading_df):
    """Finds processed events that appear more than once for the same action/instrument/type."""
    exceptions = []
    duplicates = trading_df[trading_df.duplicated(
        subset=["action_id", "instrument_id", "event_type"], keep=False
    )]
    for _, row in duplicates.iterrows():
        exceptions.append(make_exception(
            "Duplicate processed event", "Medium", "trading_events",
            row.get("event_id"), row.get("instrument_id"),
            "This event appears more than once for the same action/instrument/type.",
            "De-duplicate and confirm which record is authoritative.",
            "Trading Operations"
        ))
    return exceptions

def check_settlement_sla(settlement_df):
    """Finds settlements still pending beyond the SLA threshold."""
    exceptions = []
    settlement_df = settlement_df.copy()
    settlement_df["expected_settlement_date"] = pd.to_datetime(
        settlement_df["expected_settlement_date"]
    )
    settlement_df["days_overdue"] = (TODAY - settlement_df["expected_settlement_date"]).dt.days

    breaches = settlement_df[
        (settlement_df["settlement_status"] == "Pending") &
        (settlement_df["days_overdue"] > SETTLEMENT_SLA_DAYS)
    ]
    for _, row in breaches.iterrows():
        exceptions.append(make_exception(
            "Settlement SLA breach", "High", "settlement_status",
            row.get("settlement_id"), row.get("instrument_id"),
            f"Settlement has been pending for {row.get('days_overdue')} day(s), "
            f"exceeding the {SETTLEMENT_SLA_DAYS}-day SLA.",
            "Escalate to Settlements team for resolution.",
            "Settlements"
        ))

    # Also flag any settlement that has explicitly failed
    failed = settlement_df[settlement_df["settlement_status"] == "Failed"]
    for _, row in failed.iterrows():
        exceptions.append(make_exception(
            "Failed settlement", "Critical", "settlement_status",
            row.get("settlement_id"), row.get("instrument_id"),
            "Settlement has failed and requires immediate investigation.",
            "Escalate to Settlements team for urgent resolution.",
            "Settlements"
        ))

    return exceptions


def main():
    expected_df, trading_df, actions_df, settlement_df = load_tables()

    exceptions = []
    exceptions.extend(check_missing_events(expected_df, trading_df))
    exceptions.extend(check_late_events(expected_df, trading_df))
    exceptions.extend(check_amount_mismatches(actions_df, trading_df))
    exceptions.extend(check_duplicate_events(trading_df))
    exceptions.extend(check_settlement_sla(settlement_df))

    exceptions_df = pd.DataFrame(exceptions)

    exceptions_df.to_csv(PROCESSED_DIR / "reconciliation_results.csv", index=False)

    with sqlite3.connect(DB_PATH) as conn:
        if not exceptions_df.empty:
            exceptions_df.to_sql("data_quality_exceptions", conn, if_exists="append", index=False)

        records_checked = len(expected_df) + len(trading_df) + len(actions_df) + len(settlement_df)
        exceptions_found = len(exceptions_df)

        control_log = pd.DataFrame([{
            "control_run_id": CONTROL_RUN_ID,
            "run_timestamp": RUN_TIMESTAMP,
            "records_checked": records_checked,
            "exceptions_found": exceptions_found,
            "data_quality_score": max(0, round(100 - (exceptions_found / max(records_checked, 1) * 100), 2)),
            "run_status": "Completed",
        }])
        control_log.to_sql("control_run_log", conn, if_exists="append", index=False)

    print(f"Reconciliation run completed: {CONTROL_RUN_ID}")
    print(f"Records checked: {records_checked}")
    print(f"Exceptions found: {exceptions_found}")
    print(f"\nReconciliation results saved to: {PROCESSED_DIR / 'reconciliation_results.csv'}")


if __name__ == "__main__":
    main()