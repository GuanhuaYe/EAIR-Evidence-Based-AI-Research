# Expected output (all numbers deterministic, seed 20260702)

Only the `date` field in `hypothesis.json` history entries varies by run day.

## `python3 run_bundle.py` → results.json

```
bundle mode: default (tie-break: sorted-(count desc, answer id))
  treatment_vote15    67.00%
  baseline_single     61.16%
  ablation_vote5      72.33%
  negative_control    24.67%
  positive_control   100.00%
  delta (vote@15 - single) = +5.84pp, CI95 [+1.78, +9.64]pp
  ties: 19 questions decided by tie-break (19 contained gold)
```

Diagnostics: ties resolved to gold 19/19; treatment accuracy by tie-break:
lex_smallest 67.00%, seeded_random 64.00%, lex_largest 60.67%.

## `python3 verdict.py` (before the fix, results.json only)

```
!!! WARNING banner: results have NOT passed the adversarial audit ... !!!

VERDICT: PROVEN   (hypothesis H001, file results.json, tie-break: sorted-(count desc, answer id))
rationale: delta +5.84pp >= 3pp margin and CI95 [+1.78, +9.64]pp excludes 0
knowledge tree updated: hypothesis.json status -> PROVEN
```

## `python3 run_bundle.py --fixed` → results_v2.json

```
bundle mode: fixed (tie-break: seeded random among tied)
  treatment_vote15    64.00%
  baseline_single     61.16%
  ablation_vote5      69.00%
  negative_control    25.67%
  positive_control   100.00%
  delta (vote@15 - single) = +2.84pp, CI95 [-0.96, +6.73]pp
  ties: 19 questions decided by tie-break (19 contained gold)
```

Diagnostics: ties resolved to gold 10/19.

## `python3 verdict.py` (after the fix, prefers results_v2.json)

```
VERDICT: INSUFFICIENT   (hypothesis H001, file results_v2.json, tie-break: seeded random among tied)
rationale: delta +2.84pp is below the preregistered 3pp margin and CI95 [-0.96, +6.73]pp includes 0
knowledge tree updated: hypothesis.json status -> INSUFFICIENT
```

## Final `hypothesis.json`

`status` = `INSUFFICIENT`; `history` = two entries:
1. `results.json`, `audited: false`, delta +5.84pp, CI [+1.78, +9.64], PROVEN
2. `results_v2.json`, `audited: true`, delta +2.84pp, CI [-0.96, +6.73], INSUFFICIENT
