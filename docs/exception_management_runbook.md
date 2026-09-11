# Exception Management Runbook

This runbook describes the standard workflow for handling an exception once it appears in
`exception_queue.csv` (from data quality validation) or `reconciliation_results.csv` (from
reconciliation). It's written so that anyone — not just the person who built the system — could
pick up an exception and know exactly what to do with it.

## Step 1 — Review

- Pull the exception record and read its rule ID / category, severity, and description.
- Look up the underlying record(s) it references (e.g. the instrument, the corporate action, the
  settlement) directly in the database or source CSVs to see the full context.
- Check whether this is a **new** issue or a **repeat offender** — has this same rule/instrument
  combination triggered in a previous control run? (See the Root-Cause section of the KPI
  report.)

## Step 2 — Confirm

- Determine whether this is a genuine data/process issue, or a false positive caused by a timing
  edge case (e.g. a price legitimately published slightly after the cut-off).
- If it's a false positive, document why and close it with a note — false positives that recur
  often are a signal the rule itself needs tuning.
- If it's genuine, move to triage.

## Step 3 — Assign

- Route the exception to its owning team, as defined in the Data Quality Rules / RACI mapping
  (e.g. Instrument Data team for a duplicate ISIN, Corporate Actions team for a bad date
  sequence).
- Critical and High severity exceptions should be assigned the same day they're detected.
- Medium severity exceptions can be batched into a daily or weekly review.

## Step 4 — Resolve

- The owning team investigates the root cause (see `reconciliation_methodology.md` for how the
  four reconciliation failure modes typically map to different root causes) and applies a fix —
  correcting the source data, re-processing an event, or re-initiating a failed settlement.
- Any fix that changes the underlying data should be re-validated by re-running the relevant
  control script to confirm the exception no longer appears.

## Step 5 — Close

- Once resolved and re-validated, the exception is marked closed with a short note describing the
  root cause and the fix applied.
- Closed exceptions remain in the historical exception log — they're not deleted — so that
  patterns can be analysed over time (this is what powers repeat-offender and root-cause
  reporting).

## Escalation

Any Critical severity exception that is not resolved within one business day should be escalated
to the Trading Operations team lead. Any exception with a potential direct customer or financial
impact (e.g. a failed settlement, a missed dividend payment) should be escalated immediately
regardless of severity classification.