-- Trading Operations Control Room — Database Schema
-- Defines all tables used by the project.

DROP TABLE IF EXISTS instrument_master;
DROP TABLE IF EXISTS market_prices;
DROP TABLE IF EXISTS corporate_actions;
DROP TABLE IF EXISTS expected_events;
DROP TABLE IF EXISTS trading_events;
DROP TABLE IF EXISTS settlement_status;
DROP TABLE IF EXISTS data_quality_exceptions;
DROP TABLE IF EXISTS control_run_log;

CREATE TABLE instrument_master (
    instrument_id TEXT,
    isin TEXT,
    ticker TEXT,
    instrument_name TEXT,
    asset_class TEXT,
    currency TEXT,
    exchange TEXT,
    country TEXT,
    active_flag TEXT,
    effective_from TEXT,
    effective_to TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE market_prices (
    price_id TEXT,
    instrument_id TEXT,
    price_date TEXT,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    source TEXT,
    loaded_at TEXT
);

CREATE TABLE corporate_actions (
    action_id TEXT,
    instrument_id TEXT,
    action_type TEXT,
    announcement_date TEXT,
    ex_date TEXT,
    record_date TEXT,
    payable_date TEXT,
    currency TEXT,
    amount REAL,
    status TEXT,
    source TEXT,
    loaded_at TEXT
);

CREATE TABLE expected_events (
    expected_event_id TEXT,
    action_id TEXT,
    instrument_id TEXT,
    expected_event_type TEXT,
    expected_processing_date TEXT,
    expected_status TEXT,
    owner_team TEXT,
    priority TEXT
);

CREATE TABLE trading_events (
    event_id TEXT,
    action_id TEXT,
    instrument_id TEXT,
    event_type TEXT,
    processed_date TEXT,
    processed_status TEXT,
    processed_amount REAL,
    owner_team TEXT,
    source_system TEXT,
    loaded_at TEXT
);

CREATE TABLE settlement_status (
    settlement_id TEXT,
    trade_reference TEXT,
    instrument_id TEXT,
    trade_date TEXT,
    expected_settlement_date TEXT,
    actual_settlement_date TEXT,
    settlement_status TEXT,
    quantity REAL,
    currency TEXT,
    counterparty TEXT,
    loaded_at TEXT
);

CREATE TABLE data_quality_exceptions (
    exception_id TEXT,
    control_run_id TEXT,
    exception_type TEXT,
    severity TEXT,
    source_table TEXT,
    record_reference TEXT,
    instrument_id TEXT,
    description TEXT,
    recommended_action TEXT,
    owner_team TEXT,
    detected_at TEXT,
    status TEXT
);

CREATE TABLE control_run_log (
    control_run_id TEXT,
    run_timestamp TEXT,
    trigger_type TEXT,
    records_checked INTEGER,
    exceptions_found INTEGER,
    data_quality_score REAL,
    run_status TEXT
);