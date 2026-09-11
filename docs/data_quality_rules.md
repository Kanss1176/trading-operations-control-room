# Data Quality Rules

This document lists every data quality check implemented in `src/validate_data.py`, with its
severity, the exception type it produces, and which team would own investigating it in a real
operational setting.

| Rule ID | Check | Table | Severity | Owner Team | Description |
|---------|-------|-------|----------|------------|--------------|
| DQ-001 | Missing instrument_id | instrument_master | Critical | Instrument Data | Instrument record has no unique identifier; cannot be reliably referenced downstream. |
| DQ-002 | Duplicate ISIN | instrument_master | High | Instrument Data | Two or more instrument records share the same ISIN, creating ambiguity in reference data. |
| DQ-003 | Invalid currency code | instrument_master | Medium | Instrument Data | Currency code does not match an accepted ISO 4217 code. |
| DQ-004 | Invalid asset class | instrument_master | Medium | Instrument Data | Asset class does not match an accepted enumerated value. |
| DQ-005 | Missing market price for active instrument | market_prices | High | Market Data | An active, tradable instrument has no corresponding price record for the period. |
| DQ-006 | Invalid / non-positive price | market_prices | Critical | Market Data | Price is zero, negative, or otherwise not a valid tradable price. |
| DQ-007 | High price < low price | market_prices | High | Market Data | The day's high price is lower than the day's low price — an internally inconsistent record. |
| DQ-008 | Unknown instrument reference | market_prices | High | Market Data | Price record references an instrument_id that does not exist in instrument_master. |
| DQ-009 | Duplicate corporate action | corporate_actions | Medium | Corporate Actions | The same corporate action appears more than once for an instrument. |
| DQ-010 | Invalid corporate action date sequence | corporate_actions | High | Corporate Actions | Ex-date falls after the payable date, which is not logically possible. |
| DQ-011 | Invalid / missing dividend amount | corporate_actions | High | Corporate Actions | A dividend-type corporate action has no amount, or a non-positive amount. |

## Severity Definitions

- **Critical** — directly impacts trading or settlement correctness; requires same-day
  investigation.
- **High** — creates downstream risk (e.g. incorrect reconciliation, incorrect KPI) if not
  resolved within the control cycle.
- **Medium** — a data hygiene issue that should be corrected but does not block downstream
  processing on its own.

## How Rules Are Applied

Each run of `validate_data.py` checks every active record against all applicable rules and
writes one row per violation to `data/processed/exception_queue.csv`. Each exception record
includes: the rule ID, severity, owning team, the affected record's key fields, and a
recommended next action. The run itself is logged to `control_run_log` in the database, so every
run is traceable and auditable.