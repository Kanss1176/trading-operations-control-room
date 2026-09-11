"""
Trading Operations Control Room
Synthetic data generator

This script creates the raw CSV files used by the rest of the project.
All data is fictional/synthetic. No real customer or broker data is used.
"""

from pathlib import Path
from datetime import datetime, timedelta
import random
import numpy as np
import pandas as pd

# Fixed seeds so we get the exact same "random" data every time we run this
random.seed(42)
np.random.seed(42)

# Work out where this project lives on disk, and where raw data should go
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

TODAY = pd.Timestamp("2026-09-10")

print("Generating instrument master data...")

# ---------------------------------------------------------------------------
# 1. INSTRUMENT MASTER — the official list of tradable instruments
# ---------------------------------------------------------------------------
valid_instruments = [
    {"instrument_id": "INS001", "isin": "DE000BASF111", "ticker": "BAS",
     "instrument_name": "BASF SE", "asset_class": "Equity", "currency": "EUR",
     "exchange": "XETRA", "country": "DE", "active_flag": "Y",
     "effective_from": "2020-01-01", "effective_to": None},

    {"instrument_id": "INS002", "isin": "IE00B4L5Y983", "ticker": "IWDA",
     "instrument_name": "iShares Core MSCI World UCITS ETF", "asset_class": "ETF",
     "currency": "EUR", "exchange": "XETRA", "country": "IE", "active_flag": "Y",
     "effective_from": "2019-01-01", "effective_to": None},

    {"instrument_id": "INS003", "isin": "US0378331005", "ticker": "AAPL",
     "instrument_name": "Apple Inc.", "asset_class": "Equity", "currency": "USD",
     "exchange": "NASDAQ", "country": "US", "active_flag": "Y",
     "effective_from": "2018-01-01", "effective_to": None},

    {"instrument_id": "INS004", "isin": "US5949181045", "ticker": "MSFT",
     "instrument_name": "Microsoft Corp.", "asset_class": "Equity", "currency": "USD",
     "exchange": "NASDAQ", "country": "US", "active_flag": "Y",
     "effective_from": "2017-01-01", "effective_to": None},
]

# Deliberately broken records, so our validation checks have something to catch
bad_instruments = [
    {"instrument_id": "INS005", "isin": "DE000BASF111", "ticker": "BAS_DUP",
     "instrument_name": "BASF Duplicate", "asset_class": "Equity", "currency": "EUR",
     "exchange": "XETRA", "country": "DE", "active_flag": "Y",
     "effective_from": "2020-01-01", "effective_to": None},  # duplicate ISIN

    {"instrument_id": None, "isin": "GB00B03MLX29", "ticker": None,
     "instrument_name": "Example Invalid Instrument", "asset_class": "Crypto",
     "currency": "EURO", "exchange": "INVALID", "country": "GB", "active_flag": "Y",
     "effective_from": "2030-01-01", "effective_to": None},  # missing ID/ticker, bad currency/exchange/asset class

    {"instrument_id": "INS007", "isin": "CH0000000001", "ticker": "OLD",
     "instrument_name": "Expired Active Instrument", "asset_class": "Equity",
     "currency": "CHF", "exchange": "XETRA", "country": "CH", "active_flag": "Y",
     "effective_from": "2015-01-01", "effective_to": "2024-12-31"},  # active but expired
]

instrument_df = pd.DataFrame(valid_instruments + bad_instruments)
instrument_df["created_at"] = TODAY - pd.to_timedelta(
    np.random.randint(50, 1000, len(instrument_df)), unit="D"
)
instrument_df["updated_at"] = TODAY - pd.to_timedelta(
    np.random.randint(0, 90, len(instrument_df)), unit="D"
)
instrument_df.to_csv(RAW_DIR / "instrument_master.csv", index=False)

print(f"  -> {len(instrument_df)} instrument records written.")

# ---------------------------------------------------------------------------
# 2. MARKET PRICES
# ---------------------------------------------------------------------------
print("Generating market price data...")

price_rows = []
price_id_counter = 1
for inst in valid_instruments:
    for days_ago in range(10):  # last 10 business days
        price_date = TODAY - pd.Timedelta(days=days_ago)
        close = round(random.uniform(50, 400), 2)
        price_rows.append({
            "price_id": f"PRC{price_id_counter:04d}",
            "instrument_id": inst["instrument_id"],
            "price_date": price_date.date().isoformat(),
            "open_price": round(close * random.uniform(0.98, 1.0), 2),
            "high_price": round(close * random.uniform(1.0, 1.03), 2),
            "low_price": round(close * random.uniform(0.95, 0.99), 2),
            "close_price": close,
            "volume": random.randint(1000, 500000),
            "source": "Public Market Data Feed",
            "loaded_at": TODAY.isoformat(),
        })
        price_id_counter += 1

# Deliberately broken price records
price_rows.append({
    "price_id": "PRC9001", "instrument_id": "INS001", "price_date": TODAY.date().isoformat(),
    "open_price": 10, "high_price": 8, "low_price": 12, "close_price": -5,  # negative price, high < low
    "volume": 1000, "source": "Public Market Data Feed", "loaded_at": TODAY.isoformat(),
})
price_rows.append({
    "price_id": "PRC9002", "instrument_id": "INS999", "price_date": TODAY.date().isoformat(),
    "open_price": 100, "high_price": 105, "low_price": 95, "close_price": 101,  # unknown instrument
    "volume": 500, "source": "Public Market Data Feed", "loaded_at": TODAY.isoformat(),
})

market_prices_df = pd.DataFrame(price_rows)
market_prices_df.to_csv(RAW_DIR / "market_prices.csv", index=False)

print(f"  -> {len(market_prices_df)} price records written.")

# ---------------------------------------------------------------------------
# 3. CORPORATE ACTIONS
# ---------------------------------------------------------------------------
print("Generating corporate action data...")

corporate_actions = [
    {"action_id": "CA001", "instrument_id": "INS001", "action_type": "Dividend",
     "announcement_date": "2026-08-01", "ex_date": "2026-08-15", "record_date": "2026-08-16",
     "payable_date": "2026-08-30", "currency": "EUR", "amount": 2.50,
     "status": "Confirmed", "source": "Corporate Actions Feed", "loaded_at": TODAY.isoformat()},

    {"action_id": "CA002", "instrument_id": "INS003", "action_type": "Stock Split",
     "announcement_date": "2026-07-01", "ex_date": "2026-07-20", "record_date": "2026-07-21",
     "payable_date": "2026-07-22", "currency": "USD", "amount": 2.0,
     "status": "Confirmed", "source": "Corporate Actions Feed", "loaded_at": TODAY.isoformat()},

    {"action_id": "CA003", "instrument_id": "INS004", "action_type": "Dividend",
     "announcement_date": "2026-08-10", "ex_date": "2026-08-25", "record_date": "2026-08-26",
     "payable_date": "2026-09-05", "currency": "USD", "amount": 0.75,
     "status": "Confirmed", "source": "Corporate Actions Feed", "loaded_at": TODAY.isoformat()},

    # Deliberately broken: duplicate of CA001
    {"action_id": "CA004", "instrument_id": "INS001", "action_type": "Dividend",
     "announcement_date": "2026-08-01", "ex_date": "2026-08-15", "record_date": "2026-08-16",
     "payable_date": "2026-08-30", "currency": "EUR", "amount": 2.50,
     "status": "Confirmed", "source": "Corporate Actions Feed", "loaded_at": TODAY.isoformat()},

    # Deliberately broken: ex_date after payable_date, missing amount
    {"action_id": "CA005", "instrument_id": "INS002", "action_type": "Dividend",
     "announcement_date": "2026-08-05", "ex_date": "2026-09-01", "record_date": "2026-08-20",
     "payable_date": "2026-08-15", "currency": "EUR", "amount": None,
     "status": "Announced", "source": "Corporate Actions Feed", "loaded_at": TODAY.isoformat()},
]

corporate_actions_df = pd.DataFrame(corporate_actions)
corporate_actions_df.to_csv(RAW_DIR / "corporate_actions.csv", index=False)

print(f"  -> {len(corporate_actions_df)} corporate action records written.")

# ---------------------------------------------------------------------------
# 4. EXPECTED EVENTS — what operational processing SHOULD happen
# ---------------------------------------------------------------------------
print("Generating expected events data...")

expected_events = [
    {"expected_event_id": "EXP001", "action_id": "CA001", "instrument_id": "INS001",
     "expected_event_type": "Dividend Entitlement Calculation", "expected_processing_date": "2026-08-30",
     "expected_status": "Completed", "owner_team": "Trading Operations", "priority": "High"},

    {"expected_event_id": "EXP002", "action_id": "CA002", "instrument_id": "INS003",
     "expected_event_type": "Stock Split Adjustment", "expected_processing_date": "2026-07-22",
     "expected_status": "Completed", "owner_team": "Trading Operations", "priority": "High"},

    {"expected_event_id": "EXP003", "action_id": "CA003", "instrument_id": "INS004",
     "expected_event_type": "Dividend Entitlement Calculation", "expected_processing_date": "2026-09-05",
     "expected_status": "Completed", "owner_team": "Trading Operations", "priority": "Medium"},

    # This one deliberately has NO matching processed event later (missing event)
    {"expected_event_id": "EXP004", "action_id": "CA005", "instrument_id": "INS002",
     "expected_event_type": "Dividend Entitlement Calculation", "expected_processing_date": "2026-08-15",
     "expected_status": "Completed", "owner_team": "Trading Operations", "priority": "High"},
]

expected_events_df = pd.DataFrame(expected_events)
expected_events_df.to_csv(RAW_DIR / "expected_events.csv", index=False)

print(f"  -> {len(expected_events_df)} expected event records written.")

# ---------------------------------------------------------------------------
# 5. TRADING EVENTS — what operational processing ACTUALLY happened
# ---------------------------------------------------------------------------
print("Generating trading (processed) events data...")

trading_events = [
    {"event_id": "EVT001", "action_id": "CA001", "instrument_id": "INS001",
     "event_type": "Dividend Entitlement Calculation", "processed_date": "2026-08-30",
     "processed_status": "Completed", "processed_amount": 2.50, "owner_team": "Trading Operations",
     "source_system": "Ops Platform", "loaded_at": TODAY.isoformat()},

    # Deliberately late (processed after expected date)
    {"event_id": "EVT002", "action_id": "CA002", "instrument_id": "INS003",
     "event_type": "Stock Split Adjustment", "processed_date": "2026-07-25",
     "processed_status": "Completed", "processed_amount": 2.0, "owner_team": "Trading Operations",
     "source_system": "Ops Platform", "loaded_at": TODAY.isoformat()},

    # Deliberately wrong amount (mismatch vs corporate action)
    {"event_id": "EVT003", "action_id": "CA003", "instrument_id": "INS004",
     "event_type": "Dividend Entitlement Calculation", "processed_date": "2026-09-05",
     "processed_status": "Completed", "processed_amount": 0.50, "owner_team": "Trading Operations",
     "source_system": "Ops Platform", "loaded_at": TODAY.isoformat()},

    # Deliberate duplicate of EVT001
    {"event_id": "EVT004", "action_id": "CA001", "instrument_id": "INS001",
     "event_type": "Dividend Entitlement Calculation", "processed_date": "2026-08-30",
     "processed_status": "Completed", "processed_amount": 2.50, "owner_team": "Trading Operations",
     "source_system": "Ops Platform", "loaded_at": TODAY.isoformat()},
    # Note: EXP004 has no matching event here at all — that's our "missing event" case
]

trading_events_df = pd.DataFrame(trading_events)
trading_events_df.to_csv(RAW_DIR / "trading_events.csv", index=False)

print(f"  -> {len(trading_events_df)} trading event records written.")

# ---------------------------------------------------------------------------
# 6. SETTLEMENT STATUS
# ---------------------------------------------------------------------------
print("Generating settlement status data...")

settlement_rows = [
    {"settlement_id": "SET001", "trade_reference": "TR1001", "instrument_id": "INS001",
     "trade_date": "2026-09-08", "expected_settlement_date": "2026-09-10",
     "actual_settlement_date": "2026-09-10", "settlement_status": "Settled",
     "quantity": 100, "currency": "EUR", "counterparty": "CP-A", "loaded_at": TODAY.isoformat()},

    # Deliberately pending beyond SLA (more than 2 days overdue)
    {"settlement_id": "SET002", "trade_reference": "TR1002", "instrument_id": "INS003",
     "trade_date": "2026-09-01", "expected_settlement_date": "2026-09-03",
     "actual_settlement_date": None, "settlement_status": "Pending",
     "quantity": 50, "currency": "USD", "counterparty": "CP-B", "loaded_at": TODAY.isoformat()},

    {"settlement_id": "SET003", "trade_reference": "TR1003", "instrument_id": "INS004",
     "trade_date": "2026-09-09", "expected_settlement_date": "2026-09-11",
     "actual_settlement_date": None, "settlement_status": "Failed",
     "quantity": 30, "currency": "USD", "counterparty": "CP-C", "loaded_at": TODAY.isoformat()},

    # Deliberately missing trade reference
    {"settlement_id": "SET004", "trade_reference": None, "instrument_id": "INS002",
     "trade_date": "2026-09-07", "expected_settlement_date": "2026-09-09",
     "actual_settlement_date": "2026-09-09", "settlement_status": "Settled",
     "quantity": 20, "currency": "EUR", "counterparty": "CP-A", "loaded_at": TODAY.isoformat()},
]

settlement_df = pd.DataFrame(settlement_rows)
settlement_df.to_csv(RAW_DIR / "settlement_status.csv", index=False)

print(f"  -> {len(settlement_df)} settlement records written.")

print("\nAll synthetic data files created successfully in data/raw/")