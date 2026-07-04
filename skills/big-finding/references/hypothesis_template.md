# Hypothesis template

Every hypothesis node MUST fill all 6 fields. Push back on user
phrasing until it does.

## Required fields

### `short` — one declarative sentence, ≤15 words

Good: "single-step joint scoring beats two-stage retrieve-then-rank in small-catalog candidate matching."
Bad:  "Joint scoring is better."       (too vague)
Bad:  "We test whether..."             (not declarative)
Bad:  "Joint scoring is better than two-stage on BENCH-A because..."  (too long)

### `falsifiable_form` — concrete metric, threshold, sample size, stat test

Good: "On BENCH-A match_F1 (n=5 seeds), joint-scoring arm ≥ two-stage arm by ≥+0.02 absolute, paired-t p<0.05, sign 4+/5 seeds."
Bad:  "Joint is better."   (no threshold)
Bad:  "Joint wins by some margin."   (no number)
Bad:  "p<0.05"   (no effect size, no sample size)

Magnitude must be specified. Sign-only effects don't qualify.

### `generalization_scope` — the population the claim ranges over

Good: "all small-catalog LLM-based candidate-matching tasks where vocab ≤ 10K and KG anchor is available"
Bad:  "BENCH-A"                         (single dataset; not generalizable)
Bad:  "everything LLM"                  (too broad; can't test)

If the scope is one dataset, the hypothesis is an OBSERVATION not a
finding. Observations are OK to record but they don't become big
findings until they generalize.

### `mechanism_claim` — the causal story

Good: "Single-step joint scoring forces the model to integrate all candidate signals into one decision; two-stage pipelines lose information at each stage boundary because the upstream stage cannot anticipate downstream prompt requirements."
Bad:  "Single-step is better."           (restates the hypothesis)
Bad:  "I don't know why it should hold."  (no mechanism → no testable prediction beyond the headline)

The mechanism must predict ablations. E.g. if the mechanism is
"integration in single decision", the ablation "split joint scoring
into two stages" should hurt — that's a test.

### `alternatives_to_rule_out` — list of rival explanations

Each alternative MUST have a planned ablation that distinguishes it
from the main hypothesis.

Good:
- "Alternative A: joint wins because K=12 vs K=28 differs. Ablation: hold K constant at 28 across arms."
- "Alternative B: joint wins because of seed luck. Ablation: 5+ seeds."
- "Alternative C: two-stage model is under-tuned. Ablation: run two-stage with paper-grade fine-tuned variant."

Bad: "Could be confound" (which confound?)

### `kill_criteria` — what would refute the hypothesis

Good: "If on any 1 of 3 test datasets joint < two-stage (paired-t p<0.05), REFUTED."
Good: "If treatment-vs-baseline margin shrinks to <0.005 when K is held constant, CONFOUNDED → real driver was K, not the architecture."
Bad:  "If it doesn't work."  (what does 'work' mean?)

## Optional fields

- `prior_evidence` — link to existing data that motivated this
- `prior_literature` — citations of related work
- `expected_effect_size` — what magnitude do you actually expect?
- `risk_of_null` — what's your prior that null result is true?

## Anti-patterns

❌ **Confirmation-mode hypotheses**: "Treatment X is better than Y" written without imagining what would refute it. Force yourself to write the kill criteria FIRST, hypothesis SECOND.

❌ **Wrapper claims**: "Our system beats baselines." This is not a hypothesis, this is a paper claim. Hypotheses are about mechanisms.

❌ **Composite hypotheses**: "X and Y together cause Z." Split into atomic hypotheses; test each.

❌ **Untestable mechanism**: "There's something about the structure of the problem." If you can't write an ablation that tests the mechanism, you don't have a mechanism, you have a guess.
