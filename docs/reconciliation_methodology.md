# Reconciliation Methodology

## Purpose

Reconciliation answers a simple question: **did what was supposed to happen actually happen,
correctly and on time?** This document explains how `src/run_reconciliation.py` answers that
question across two areas: corporate action event processing, and trade settlement.

## Part 1 — Expected vs. Processed Event Reconciliation

The system holds two independent records of events:

- `expected_events` — what operations expects to happen, derived from corporate action
  announcements (e.g. "Instrument X should pay a dividend on date Y").
- `trading_events` — what was actually processed by downstream systems.

The reconciliation logic matches records between these two tables on instrument and event type,
then checks for four distinct failure modes:

1. **Missing events** — an event exists in `expected_events` but has no corresponding record in
   `trading_events` at all. This is the highest-risk category, since it usually means a customer
   impact was never actioned.
2. **Late processing** — a matching event exists, but its processed date falls after the expected
   deadline. This is measured in days late and contributes to the SLA breach rate KPI.
3. **Amount mismatches** — a matching event exists and was processed on time, but the processed
   amount does not equal the amount on the originating corporate action. This points to either a
   data entry error or a miscalculation upstream.
4. **Duplicate processing** — the same expected event has been processed more than once, which
   risks a double payment or double action to the customer.

## Part 2 — Settlement Reconciliation

Settlement records in `settlement_status` are checked against two rules:

1. **SLA breach** — a settlement is still in a "pending" state more than 2 business days past its
   expected settlement date. The 2-day threshold is a simplified stand-in for a real T+1/T+2
   settlement SLA.
2. **Failed settlement** — the settlement status is explicitly "failed", which always generates
   an exception regardless of how long it's been pending.

## Output

Every reconciliation exception is written to `data/processed/reconciliation_results.csv` with a
category (missing / late / mismatch / duplicate / SLA breach / failed), the affected record's
key identifiers, and enough context to route it to the right team. Each run is logged to
`control_run_log`, in the same way as the data quality checks, so reconciliation runs are
auditable over time — which matters for spotting repeat offenders (see the Root-Cause section of
the KPI report).

## Design Note

This reconciliation logic intentionally mirrors how a real Trading Operations team would work:
rather than a single blanket "everything matches / doesn't match" check, each failure mode is
categorised separately, because the response and the owning team differ. A missing event needs
urgent investigation into why it was never actioned; a late event may just need a process
efficiency fix; a mismatch needs a root-cause investigation into where the numbers diverged.