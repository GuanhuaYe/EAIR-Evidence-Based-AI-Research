# Analysis decision tree

After a bundle finishes, the analysis phase classifies the outcome
into one of 6 states. The decision rule MUST be the pre-registered
one from `bundle.yaml.decision_rule`.

## The 6 states

### 1. PROVEN

Conditions (ALL must hold):
- Treatment arm meets falsifiable_form threshold vs baseline arm
- Result direction-consistent across all ablations (no ablation
  reverses the sign)
- Negative control behaves as expected (null-ish)
- Statistical test meets pre-registered threshold

Action:
1. Mark node PROVEN
2. Apply Nature-worthy test (5-condition gate)
3. If passes → add to findings_catalogue
4. If fails → spawn child hypothesis for next-tier generalization test

### 2. REFUTED

Conditions (ANY one):
- Treatment ≤ baseline by ≥falsifiable threshold (opposite direction)
- Statistical test p > pre-registered threshold AND effect size < 0.5σ
- Result varies wildly across seeds (CV > 50%) — not the same finding twice

Action:
1. Mark node REFUTED
2. Write 3-sentence post-mortem: what was wrong with the hypothesis or what's the data actually showing
3. Pick the most-likely "alternatives_to_rule_out" as the next hypothesis (child node)
4. If no alternative fits → consider whether the original question itself was malformed

### 3. INSUFFICIENT

Conditions:
- Effect direction consistent with hypothesis BUT
- Statistical test p between thresholds (e.g., p ∈ [0.05, 0.20])
- Sample size n < 10 seeds

Action:
1. Mark node INSUFFICIENT
2. Re-launch the SAME bundle with 5 more seeds (n=10 total)
3. If after n=10 still INSUFFICIENT, downgrade to OBSERVATION (effect direction noted but no PROVEN claim)
4. Do NOT spawn children from INSUFFICIENT — premature

### 4. CONFOUNDED

Conditions:
- Treatment > baseline in primary comparison BUT
- An ablation arm reverses the ranking OR
- An ablation reveals that a controlled variable (e.g., K, model size) explains the entire effect

Action:
1. Mark original node CONFOUNDED (NOT REFUTED — finding wasn't false, it was wrongly attributed)
2. The CONFOUND IS THE FINDING — spawn child hypothesis about the actual driver
3. Update node notes: "Treatment effect explained by <confound>; ranking reverses when controlled."
4. Re-run controlled bundle on the new child hypothesis

Example: Original "joint scoring > two-stage" CONFOUNDED by K=28 vs K=12. New hypothesis: "Larger K → higher F1 regardless of scoring choice."

### 5. PIVOTED

Conditions:
- Bundle ran, but ablation arms reveal an unexpected pattern
- Original hypothesis is irrelevant to the actual story in the data
- The data is "telling" a different story

Action:
1. Mark original node PIVOTED
2. Spawn child hypothesis from the data-driven pattern
3. Original node stays as breadcrumb but its claim is no longer relevant
4. Discount any further investment in the original line

Example: Original hypothesis "SC-3 helps" PIVOTED by data showing "SC-3 hurts at T=0.7 but might help at T=0.3" → new hypothesis "There's a temperature sweet-spot for SC-3 in narrow classification."

### 6. PROTOCOL_BROKEN

Conditions:
- Negative control fires (e.g., baseline > 0 when it should be 0)
- Positive control fails (known-good arm gives bad number)
- Arms disagree on basic data (different n_eval_test counts, different injection ids)

Action:
1. Mark bundle PROTOCOL_BROKEN, NOT the hypothesis
2. Find the protocol bug (data hash mismatch? code mismatch? launcher bug?)
3. Re-launch the bundle after fix
4. Do NOT make claims about the hypothesis until protocol is verified

## Pre-registration discipline

The decision rule MUST be written BEFORE the bundle runs. If after
seeing results you want to revise the rule, that's HARKing
(Hypothesizing After Results Known) — forbidden.

If the data reveals an unexpected pattern that the original rule
doesn't capture, the right move is PIVOT (new hypothesis), not
re-interpreting the original rule.

## Multi-arm comparison subtleties

When the bundle has 3+ treatment-style arms (e.g., joint scoring,
two-stage, and a 3rd alternative), the comparison structure must
specify:

- **Primary comparison**: treatment-1 vs baseline (the headline)
- **Secondary comparisons**: treatment-2/3 vs baseline (supplementary)
- **Cross-treatment comparisons**: treatment-1 vs treatment-2 (which is "best")

Each comparison gets its own decision rule. The hypothesis applies
to the PRIMARY one.

## Multiple-hypothesis-testing correction

If a bundle tests 3+ hypotheses simultaneously, apply Bonferroni or
similar correction. Pre-register the correction in `decision_rule`.

## Effect size minimum

Even with stat-sig p<0.05, an effect size below the
"practically relevant" threshold (set in falsifiable_form) is
treated as REFUTED (you got a statistically detectable but
practically meaningless effect).

E.g., if falsifiable says "≥+0.02 absolute match_F1", a measured
+0.005 with p<0.01 is REFUTED, not PROVEN — the effect size
threshold matters.
