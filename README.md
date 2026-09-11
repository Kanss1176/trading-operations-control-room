# Trading Operations Control Room

Instrument data quality, corporate-action reconciliation and settlement SLA monitoring — an independent portfolio project.

## Overview

This project simulates the internal control system a Trading Operations team uses to monitor multi-source data, detect operational exceptions, and produce decision-ready KPIs. It was built to demonstrate practical capability in data validation, reconciliation, and operational controls for financial-services operations roles.

## Business Context

**NordBridge Markets** is a fictional European digital broker. Its Trading Operations team must ensure instrument reference data, market prices, corporate-action events, operational processing, and settlement records stay accurate, complete, and processed within agreed timelines — because data arrives from multiple independent systems, inconsistencies naturally occur and need to be caught and investigated.

## What It Does

1. Generates realistic synthetic instrument, price, corporate-action, event, and settlement data (with deliberately embedded data-quality issues, so the controls have something real to catch).
2. Loads everything into a SQLite database.
3. Runs data-quality validation checks (missing/duplicate identifiers, invalid currencies, bad prices, unknown instrument references).
4. Reconciles expected corporate-action events against what was actually processed (missing events, late processing, amount mismatches, duplicates).
5. Monitors settlement records against a defined SLA and flags failed settlements.
6. Produces a prioritised, severity-scored exception queue and a KPI summary (data quality score, SLA breach rate, event completeness rate, root-cause breakdown).

## Technology Stack

- Python (pandas)
- SQLite / SQL
- Git / GitHub

## Data Disclosure

- NordBridge Markets is a fictional company.
- All instrument, price, corporate-action, event, and settlement records are synthetic, generated with a fixed random seed for reproducibility.
- No customer, proprietary, employer, or confidential data has been used at any point.

## Repository Structure

```text
trading-operations-control-room/
├── data/
│   ├── raw/            # synthetic input CSVs
│   └── processed/      # exception queue, reconciliation results, KPI summaries
├── database/
│   └── schema.sql       # SQLite table definitions
├── src/
│   ├── generate_synthetic_data.py
│   ├── create_database.py
│   ├── validate_data.py
│   ├── run_reconciliation.py
│   └── calculate_kpis.py
├── docs/                 # business problem, rules, runbook (in progress)
└── README.md
```

## How to Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install pandas numpy sqlalchemy openpyxl matplotlib seaborn

python src/generate_synthetic_data.py
python src/create_database.py
python src/validate_data.py
python src/run_reconciliation.py
python src/calculate_kpis.py
```

## Sample Output

A single run currently detects issues such as:
- Missing instrument identifiers and duplicate ISINs
- Invalid currencies and non-positive market prices
- Missing and late-processed corporate action events
- Amount mismatches between expected and processed events
- Duplicate processed events
- Settlement SLA breaches

...and rolls them into a severity-scored exception queue plus a KPI summary (data quality score, SLA breach rate, event completeness rate, root-cause breakdown).

## Status / Next Steps

- [x] Synthetic data generation
- [x] SQLite database
- [x] Data quality validation
- [x] Corporate action & settlement reconciliation
- [x] KPI calculation
- [ ] Documentation (business problem, data quality rules, runbook, limitations)
- [ ] Dashboard / reporting layer
- [ ] Automated scheduled runs

## Author

Kanishka Singh — [GitHub](https://github.com/Kanss1176) · [LinkedIn](https://www.linkedin.com/in/kanishka-singh-534819324)