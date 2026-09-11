# Business Problem

## Context

NordBridge Markets is a fictional European digital broker offering retail customers access to
equities, ETFs, and other tradable instruments. Like any brokerage, its operations depend on
data flowing correctly between several independent systems: instrument reference data feeds,
market data providers, corporate action announcements, internal trade/event processing, and
custodian/settlement systems.

Because these systems are independent, they don't always agree. A price feed might publish a
negative or missing price. A corporate action might be announced with an inconsistent date
sequence. An expected settlement might never get processed, or get processed late, or with the
wrong amount. Left unchecked, these discrepancies create financial risk, regulatory exposure,
and customer-facing failures — a client sees a dividend that never arrives, or trades against a
stale price.

## The Problem This Project Solves

Trading Operations teams exist to catch these discrepancies before they become customer-facing
incidents. In practice, this means running a repeatable, systematic **control process**: validate
incoming data, reconcile what was expected against what actually happened, and produce
management information (KPIs) that shows whether operations are healthy or degrading.

This project simulates that control process end-to-end:

1. **Data quality validation** — catching bad data at the source (missing IDs, duplicate
   identifiers, invalid prices, bad date sequences) before it propagates downstream.
2. **Reconciliation** — comparing what was *expected* to happen (an event, a settlement) against
   what *actually* happened, and flagging mismatches, lateness, and failures.
3. **KPI reporting** — summarising the health of the operation in a small set of metrics that a
   manager or team lead could review daily.

## Why This Matters for a Trading Operations Analyst Role

The skills this project exercises — investigating discrepancies, understanding root causes,
building repeatable controls, and communicating findings through clear metrics — are the core of
what a Graduate Trading Operations Analyst does day to day. The synthetic data was deliberately
seeded with realistic problems (a negative price, a duplicate corporate action, a missed
settlement) specifically so the control logic has something real to catch, rather than running
cleanly against a "perfect" dataset that doesn't reflect how operations actually work.