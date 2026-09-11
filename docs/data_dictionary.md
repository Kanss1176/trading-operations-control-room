# Data Dictionary

This document defines every table and column used in the system, its meaning, and any validation
rule that applies to it. Tables live in `database/trading_ops.db` (SQLite) and mirror the raw
CSVs in `data/raw/`.

## instrument_master

| Column | Type | Meaning | Validation Rule |
|--------|------|---------|------------------|
| instrument_id | TEXT | Unique internal identifier for the instrument | Must not be null (DQ-001) |
| isin | TEXT | International Securities Identification Number | Must be unique across active records (DQ-002) |
| instrument_name | TEXT | Human-readable name of the instrument | — |
| currency | TEXT | Trading currency, ISO 4217 code | Must be a valid currency code (DQ-003) |
| asset_class | TEXT | Category of instrument (equity, ETF, bond, etc.) | Must be a valid enumerated value (DQ-004) |
| is_active | BOOLEAN | Whether the instrument is currently tradable | — |
| expiry_date | DATE | Date the instrument record expires, if applicable | Should not be in the past for active records |

## market_prices

| Column | Type | Meaning | Validation Rule |
|--------|------|---------|------------------|
| price_id | INTEGER | Unique identifier for the price record | — |
| instrument_id | TEXT | References instrument_master.instrument_id | Must exist in instrument_master (DQ-008) |
| price_date | DATE | Date the price applies to | — |
| open_price / high_price / low_price / close_price | DECIMAL | OHLC price values | Must be positive (DQ-006); high must be >= low (DQ-007) |

## corporate_actions

| Column | Type | Meaning | Validation Rule |
|--------|------|---------|------------------|
| action_id | INTEGER | Unique identifier for the corporate action | Must not be duplicated (DQ-009) |
| instrument_id | TEXT | References instrument_master.instrument_id | — |
| action_type | TEXT | Type of action (e.g. dividend, split) | — |
| ex_date | DATE | Ex-date of the action | Must be before payable_date (DQ-010) |
| payable_date | DATE | Date the action is payable | Must be after ex_date (DQ-010) |
| amount | DECIMAL | Amount associated with the action (e.g. dividend per share) | Must be present and positive for dividend types (DQ-011) |

## expected_events

| Column | Type | Meaning |
|--------|------|---------|
| event_id | INTEGER | Unique identifier for the expected event |
| instrument_id | TEXT | References instrument_master.instrument_id |
| event_type | TEXT | Type of event expected to be processed |
| expected_date | DATE | Date the event is expected to be processed by |
| expected_amount | DECIMAL | Amount expected to be processed |

## trading_events

| Column | Type | Meaning |
|--------|------|---------|
| processed_event_id | INTEGER | Unique identifier for the processed event |
| instrument_id | TEXT | References instrument_master.instrument_id |
| event_type | TEXT | Type of event that was processed |
| processed_date | DATE | Date the event was actually processed |
| processed_amount | DECIMAL | Amount that was actually processed |

## settlement_status

| Column | Type | Meaning |
|--------|------|---------|
| settlement_id | INTEGER | Unique identifier for the settlement record |
| trade_reference | TEXT | Reference to the originating trade |
| expected_settlement_date | DATE | Date settlement is expected |
| status | TEXT | Current status (pending, settled, failed) |
| settled_date | DATE | Date settlement actually completed, if applicable |

## data_quality_exceptions

| Column | Type | Meaning |
|--------|------|---------|
| exception_id | INTEGER | Unique identifier for the exception record |
| rule_id | TEXT | The data quality rule that was triggered (see data_quality_rules.md) |
| severity | TEXT | Critical / High / Medium |
| owner_team | TEXT | Team responsible for investigating |
| affected_record | TEXT | Key identifier(s) of the record that failed the check |
| recommended_action | TEXT | Suggested next step for resolution |
| run_id | INTEGER | References the control_run_log entry that generated this exception |

## control_run_log

| Column | Type | Meaning |
|--------|------|---------|
| run_id | INTEGER | Unique identifier for the control run |
| run_type | TEXT | Type of run (e.g. data_quality, reconciliation) |
| run_timestamp | DATETIME | When the run executed |
| records_checked | INTEGER | Total number of records checked in this run |
| exceptions_found | INTEGER | Total number of exceptions raised in this run |