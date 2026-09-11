"""
Trading Operations Control Room
Calculates operational KPIs from the exception queue and reconciliation results.
"""

from pathlib import Path
from datetime import datetime
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database" / "trading_ops.db"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

TODAY = pd.Timestamp("2026-09-10")


def load_data():
    """Loads everything needed to calculate KPIs."""
    with sqlite3.connect(DB_PATH) as conn:
        exceptions_df = pd.read_sql("SELECT * FROM data_quality_exceptions", conn)
        expected_df = pd.read_sql("SELECT * FROM expected_events", conn)
        trading_df = pd.read_sql("SELECT * FROM trading_events", conn)
        settlement_df = pd.read_sql("SELECT * FROM settlement_status", conn)
        control_log_df = pd.read_sql("SELECT * FROM control_run_log", conn)
    return exceptions_df, expected_df, trading_df, settlement_df, control_log_df

def calculate_kpis():
    exceptions_df, expected_df, trading_df, settlement_df, control_log_df = load_data()

    # --- Data quality score & exception rate (from the latest control run) ---
    total_records_checked = control_log_df["records_checked"].sum()
    total_exceptions_found = control_log_df["exceptions_found"].sum()
    data_quality_score = max(
        0, round(100 - (total_exceptions_found / max(total_records_checked, 1) * 100), 2)
    )
    exception_rate = round(total_exceptions_found / max(total_records_checked, 1) * 100, 2)

    # --- Critical / High exception counts ---
    critical_open = len(exceptions_df[
        (exceptions_df["severity"] == "Critical") & (exceptions_df["status"] == "Open")
    ])
    high_open = len(exceptions_df[
        (exceptions_df["severity"] == "High") & (exceptions_df["status"] == "Open")
    ])

    # --- Event processing completeness: expected events that DID get processed ---
    merged_events = expected_df.merge(
        trading_df[["action_id", "instrument_id", "event_id"]],
        on=["action_id", "instrument_id"], how="left"
    )
    total_expected = len(merged_events)
    processed_count = merged_events["event_id"].notna().sum()
    event_completeness_rate = round(
        (processed_count / total_expected * 100) if total_expected else 0, 2
    )

    # --- SLA breach rate: expected events missing OR late ---
    merged_with_dates = expected_df.merge(trading_df, on=["action_id", "instrument_id"], how="left")
    merged_with_dates["expected_processing_date"] = pd.to_datetime(
        merged_with_dates["expected_processing_date"]
    )
    merged_with_dates["processed_date"] = pd.to_datetime(merged_with_dates["processed_date"])
    missing_or_late = merged_with_dates[
        merged_with_dates["event_id"].isna() |
        (merged_with_dates["processed_date"] > merged_with_dates["expected_processing_date"])
    ]
    sla_breach_rate = round(
        (len(missing_or_late) / total_expected * 100) if total_expected else 0, 2
    )

    # --- Settlement pending rate ---
    total_settlements = len(settlement_df)
    pending_settlements = len(settlement_df[settlement_df["settlement_status"] == "Pending"])
    settlement_pending_rate = round(
        (pending_settlements / total_settlements * 100) if total_settlements else 0, 2
    )

    # --- Root cause breakdown: which exception types show up most ---
    root_cause_summary = (
        exceptions_df.groupby("exception_type").size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    summary = pd.DataFrame([{
        "run_date": datetime.now().date().isoformat(),
        "total_records_checked": int(total_records_checked),
        "total_exceptions_found": int(total_exceptions_found),
        "data_quality_score": data_quality_score,
        "exception_rate_pct": exception_rate,
        "critical_open_exceptions": critical_open,
        "high_open_exceptions": high_open,
        "event_completeness_rate_pct": event_completeness_rate,
        "sla_breach_rate_pct": sla_breach_rate,
        "settlement_pending_rate_pct": settlement_pending_rate,
    }])

    summary.to_csv(PROCESSED_DIR / "control_summary.csv", index=False)
    root_cause_summary.to_csv(PROCESSED_DIR / "root_cause_summary.csv", index=False)

    print("=== Trading Operations Control Room — KPI Summary ===\n")
    print(f"Data quality score:          {data_quality_score}%")
    print(f"Exception rate:               {exception_rate}%")
    print(f"Critical open exceptions:     {critical_open}")
    print(f"High open exceptions:         {high_open}")
    print(f"Event completeness rate:      {event_completeness_rate}%")
    print(f"SLA breach rate:              {sla_breach_rate}%")
    print(f"Settlement pending rate:      {settlement_pending_rate}%")
    print("\nTop root causes:")
    print(root_cause_summary.to_string(index=False))
    print(f"\nSaved: {PROCESSED_DIR / 'control_summary.csv'}")
    print(f"Saved: {PROCESSED_DIR / 'root_cause_summary.csv'}")


if __name__ == "__main__":
    calculate_kpis()