# Panel calibration log

Append-only log of past panels. Use to sanity-check current panel
score distributions before committing the verdict.

Format per row:
- Date (YYYY-MM-DD)
- Paper (≤30 chars)
- Venue
- R1 / R2 / R3 scores
- AC verdict
- Actual outcome (filled in post-submission, if known)
- Drift notes (if panel was re-passed for calibration)

## Log

| Date | Paper | Venue | R1 | R2 | R3 | AC | Actual | Notes |
|---|---|---|---|---|---|---|---|---|
| _initial_ | — | — | — | — | — | — | — | template row, ignore |

## Sanity rules

After 5+ entries:
- If panel mean is consistently >2 points above actual reviewer mean,
  personas are soft. Re-tighten persona prompts.
- If R1/R2/R3 always agree within ±1, personas are not diverse enough.
- If AC always says ACCEPT, AC is mis-calibrated; re-inject venue
  acceptance rate.
