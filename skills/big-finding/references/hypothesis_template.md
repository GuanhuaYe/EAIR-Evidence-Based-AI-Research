# Hypothesis template

Every hypothesis node MUST fill all 6 fields. Push back on user
phrasing until it does.

## Required fields

### `short` — one declarative sentence, ≤15 words

Good: "Constrained-letter LLM rerank beats sentence-transformer in narrow-domain code disambiguation."
Bad:  "Letter reranker is better."     (too vague)
Bad:  "We test whether..."             (not declarative)
Bad:  "Constrained-letter is better than sentence-transformer on MIMIC-III because..."  (too long)

### `falsifiable_form` — concrete metric, threshold, sample size, stat test

Good: "On MIMIC-III code_mismatch F1 (n=5 seeds), letter-rerank arm ≥ sentence-transformer arm by ≥+0.02 absolute, paired-t p<0.05, sign 4+/5 seeds."
Bad:  "Letter is better."   (no threshold)
Bad:  "Letter wins by some margin."   (no number)
Bad:  "p<0.05"   (no effect size, no sample size)

Magnitude must be specified. Sign-only effects don't qualify.

### `generalization_scope` — the population the claim ranges over

Good: "all narrow-domain LLM-based candidate-disambiguation tasks where vocab ≤ 10K and KG anchor is available"
Bad:  "MIMIC-III"                       (single dataset; not generalizable)
Bad:  "everything LLM"                  (too broad; can't test)

If the scope is one dataset, the hypothesis is an OBSERVATION not a
finding. Observations are OK to record but they don't become big
findings until they generalize.

### `mechanism_claim` — the causal story

Good: "Constrained single-letter output forces the LLM to integrate FD + k-NN + KG candidates into one decision; two-stage pipelines lose information at each stage boundary because the upstream stage cannot anticipate downstream prompt requirements."
Bad:  "Single-step is better."           (restates the hypothesis)
Bad:  "I don't know why it should hold."  (no mechanism → no testable prediction beyond the headline)

The mechanism must predict ablations. E.g. if the mechanism is
"integration in single decision", the ablation "split letter-rerank
into two stages" should hurt — that's a test.

### `alternatives_to_rule_out` — list of rival explanations

Each alternative MUST have a planned ablation that distinguishes it
from the main hypothesis.

Good:
- "Alternative A: letter wins because K=12 vs K=28 differs. Ablation: hold K constant at 28 across arms."
- "Alternative B: letter wins because of seed luck. Ablation: 5+ seeds."
- "Alternative C: sentence-transformer model is under-tuned. Ablation: run sentence-transformer with paper-grade fine-tuned variant."

Bad: "Could be confound" (which confound?)

### `kill_criteria` — what would refute the hypothesis

Good: "If on any 1 of 3 test datasets letter < sentence-transformer (paired-t p<0.05), REFUTED."
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
