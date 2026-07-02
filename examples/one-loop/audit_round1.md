# Adversarial audit — H001 harness, round 1

- **Target:** `run_bundle.py` @ default path, `results.json` (seed 20260702)
- **Auditor:** cross-model reviewer B (different model family from the author agent)
- **Scope:** scoring code, vote aggregation, controls, CI computation
- **Verdict: FAIL — severity CRITICAL (decision-flipping)**

## Finding 1 (CRITICAL): tie-break in `vote()` is biased toward the gold answer

`vote()` in default mode resolves plurality ties with
`sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]` — the
lexicographically **smallest** answer id wins every tie. That would be merely
arbitrary, except `build_questions()` encodes gold as `opt0` of each question
(`q012_opt0` sorts before `q012_opt1..4`), so gold is lexicographically
smallest **by construction** and every tie is silently awarded to the gold
label. This is scoring-side leakage, not a property of the method under test.

Evidence from `results.json` diagnostics:

1. **Tie volume.** 19 / 300 treatment questions were decided by tie-break —
   6.3% of the benchmark, concentrated in the clustered-error questions where
   the gold count and the cluster-distractor count race closely.
2. **Direction.** All 19 ties contained the gold answer, and the default rule
   resolved **19 / 19 to gold**. Under an unbiased tie-break the expectation
   is ~9.5. Binomial p(19/19 | fair) ≈ 1.9e-6.
3. **Reversal test.** Flipping only the tie-break to lexicographically
   *largest* moves treatment accuracy 67.00% → 60.67% (−6.33pp). A seeded
   random tie-break gives 64.00%. The tie-break alone swings the arm by more
   than the entire preregistered 3pp decision margin.

Decision impact: reported delta is +5.84pp, CI95 [+1.78, +9.64] → PROVEN.
With an unbiased tie-break the projected delta is ≈ +2.84pp with CI95
straddling 0 → not PROVEN. The finding flips the verdict; the current
results.json must not be used.

## Non-findings

Positive control (100.00%) and negative control (24.67%, band [12%, 28%])
pass — they cannot catch this leak, which only activates on ties that the
noiseless and label-shuffled arms rarely exercise decisively. Bootstrap is
correctly paired over questions; seeds fixed; arms share draws as preregistered.

## Required fix

Replace the default tie-break with a seeded random choice among tied answers
(any rule statistically independent of gold identity is acceptable). Rerun
the full bundle unchanged otherwise and emit `results_v2.json`. Re-audit not
required if the diff is confined to the tie-break.
