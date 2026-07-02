# Nature-worthy test (the 6-condition gate)

The name is the bar the gate aims at, not a claim about any result that
passes it. It exists to keep "better on one benchmark" out of the
findings catalogue.

A PROVEN node passes this gate iff ALL SIX conditions hold.

## Condition 0 (NEW): Cross-validated, not single-split

The evidence for the finding MUST come from a bundle with `cv_folds ≥ 5`
(K-fold cross-validation). Single-split + multi-seed-injection evidence
is informative but NOT sufficient for Nature-worthy claims because:

- A lucky train/test split could inflate the effect by 1-3pp on cm_F1-scale findings
- Multi-seed within one split tests injection noise, NOT partition noise
- Cross-fold paired-t with K≥5 folds gives the strongest practical test

A node with PROVEN_SINGLE_SPLIT status CANNOT pass this gate until a
`cv_folds ≥ 5` follow-up bundle re-confirms it.



## Condition 1: Generalizes across ≥3 distinct domains

Distinct = not MIMIC variants, not subsets of the same dataset.

✅ Examples of distinct:
- MIMIC-III lab events + ICD code disambiguation + protein name resolution
- Code refactoring + medical coding + product taxonomy
- 3 RAG benchmarks from different domains (legal, medical, scientific)

❌ Not distinct:
- MIMIC-III + MIMIC-IV-Demo (same source, same task)
- 3 medical-coding tasks (one domain, different vocab)
- 3 versions of the same dataset

If a finding is PROVEN on one dataset, schedule generalization
tests as children. Only after 3+ distinct domains is the
top-level claim Nature-eligible.

## Condition 2: Mechanistic (causal story tested by ablation)

Not just "X correlates with Y" — must have a CAUSAL story tested
by an ablation that predicted to-and-from-zero.

✅ Mechanistic: "Constrained-letter rerank wins because single-step
generation integrates context; if we artificially split it into
two stages, the advantage disappears." (And the ablation confirms.)

❌ Correlational: "Constrained-letter rerank wins on benchmark X."
(No mechanism, no test of WHY.)

## Condition 3: Falsifiable

The finding's claim must specify a future experiment that could
disprove it.

✅ "Letter-rerank advantage holds for vocab ≤ 10K"  — testable by trying vocab 50K
✅ "SC-3 hurts at T=0.7 on confident classifiers"  — testable by intermediate T

❌ "Letter-rerank is in some sense better"  — vague, unfalsifiable
❌ "Our method works well"                    — not falsifiable

## Condition 4: Counter-intuitive OR foundational

Counter-intuitive: contradicts prior literature or common intuition.
Foundational: establishes a new property (e.g., a guarantee, a
mechanism, a bound).

✅ Counter-intuitive: "Smaller candidate set → higher F1" contradicts
the intuition that more candidates → better recall.
✅ Counter-intuitive: "SC-3 hurts at T=0.7" contradicts the
Wang-et-al. CoT-SC paper's broad claim.
✅ Foundational: "KG-projector intersection guarantees zero
false-positive repair (architectural property, theorem-formalized)."

❌ Not counter-intuitive: "Bigger model is better" (consistent with priors)
❌ Not foundational: "Method X gets +0.01 on dataset Y"

## Condition 5: Quantitative magnitude with CI

Not just sign of effect — must have a confidence interval and
practical interpretation.

✅ "Letter-rerank cm_F1 advantage = +0.036 ± 0.012 (95% CI on
paired-t across 5 seeds × 3 domains), p<0.001, equivalent to ~30%
relative recall improvement."

❌ "Letter-rerank wins"
❌ "p<0.05"

## Composite scoring

Pass = ALL SIX. Fail = any of the six fails. There is no
partial credit.

If a finding passes 4/5, it's still a worthwhile finding (write it
up, share it) — but it's not Nature-eligible yet. Schedule the
missing condition's experiment as a child.

## Adding to findings catalogue

When a node passes all 5:

1. Append to `findings_catalogue` in `tree.json` with the
   finding's quantitative statement
2. Generate `<paper_dir>/big_finding/findings/<F-id>.md` containing:
   - The full 5-condition justification (one paragraph per condition)
   - Citation-ready statement (1 sentence, ≤30 words)
   - Open follow-up questions
   - Connection to literature (related prior work)
3. The finding becomes a building block for papers (via the conductor
   stage 3+ if user wants to write).

## Example: A passing finding

Hypothesized: H001 "Constrained-letter rerank > sentence-transformer in narrow disambiguation"

After E001 (MIMIC-III), E002 (synthetic vocab-1K), E003 (Open-LOINC-real), the finding:
- ✅ Generalizes (3 distinct domains)
- ✅ Mechanistic (ablation confirmed single-step integration is the driver)
- ✅ Falsifiable (vocab >10K predicted to break it)
- ✅ Counter-intuitive (literature favors multi-stage RAG)
- ✅ Quantitative (+0.034 ± 0.011 cm_F1, p<0.001)

→ Added to findings_catalogue as F001.

## Example: A non-passing finding

Hypothesized: H005 "MIMIC-III has 5% non-analyte itemids"

- ❌ Single domain
- ❌ Descriptive not mechanistic
- ✅ Falsifiable (just count again)
- Possibly counter-intuitive (people don't know about this)
- ✅ Quantitative

→ Recorded as OBSERVATION (worth knowing, paper-worthy possibly) but
not Nature-eligible. Stays in tree as a useful observation.
