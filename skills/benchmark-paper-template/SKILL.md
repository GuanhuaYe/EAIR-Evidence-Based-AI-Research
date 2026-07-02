---
name: benchmark-paper-template
description: Audits and structures benchmark or evaluation papers as measurement instruments. Runs a five-property Measurement-Validity Audit (construct validity, reliability, discriminative power, contamination resistance, actionability), each property backed by concrete tests the paper must report. Emits an evidence-gated audit table with computed severities, a paper skeleton in which each section exists to prove one property, and a structured JSON verdict. Use when writing a benchmark paper, auditing a benchmark draft, deciding whether a benchmark idea will survive review, or planning the validation experiments a benchmark needs.
license: CC-BY-4.0
---

# Benchmark Paper Template — Measurement-Validity Audit

## Premise

A benchmark is a measurement instrument. It is not judged by the novelty of its
dataset, the size of its item pool, or the cleverness of its collection script.
It is judged the way any instrument is judged: does it measure the thing it
claims to measure, does it measure it repeatably, can it tell its subjects
apart, can it be gamed, and does a reading tell you what to fix?

Measurement theory gives those five questions names, and each name comes with
experiments a paper can actually run and report. This skill audits a benchmark
paper (or plan) against all five properties, marks every gap with a computed
severity and the concrete missing experiment, and derives the paper's section
structure directly from the properties — each property gets the section that
proves it.

The audit is **evidence-gated**: every claim of "this test is present" must
cite where in the document it appears (section number, table, figure, or
quoted sentence). If the evidence cannot be located, the row says `NOT-IN-DOC`
— never "probably covered" or "implied".

## The five measurement properties

### P1. Construct validity — does the metric measure the claimed capability?

The paper names a capability ("compositional reasoning", "long-horizon
planning", "clinical safety"). Construct validity asks whether the score is
actually driven by that capability, or by something cheaper that correlates
with it in this particular item pool.

Tests the paper must report:

- **Shortcut-exploit baseline.** Deliberately build at least one degenerate
  solver that lacks the claimed capability — answer-choice priors, length or
  surface-form heuristics, retrieval over the source corpus, a model given the
  question with the critical premise deleted — and report its score. If a
  shortcut solver lands anywhere near real models, the metric is measuring the
  shortcut. See `references/construct-probes.md` for a probe menu.
- **Adversarial construct probes.** Perturb items so that the claimed
  capability is required in one variant and bypassed in the other; a valid
  metric moves sharply between the variants.
- **Convergent check (when available).** Correlate the score against an
  independent signal of the same capability (human expert ratings, an
  established downstream task). Report the correlation, not just "aligns well".

### P2. Reliability — is the score stable under retest?

A score that moves materially when nothing about the model changed is noise
dressed up as measurement.

Tests the paper must report:

- **Retest stability.** Same model, resampled item subsets and/or reworded
  prompt templates; report a confidence interval on the headline score
  (bootstrap over items is the minimum acceptable; seed variance for sampled
  decoding too). Any leaderboard gap smaller than the CI width must not be
  narrated as a ranking.
- **Annotator agreement.** Wherever humans label items or grade outputs,
  report chance-corrected agreement (Cohen's or Fleiss' kappa, Krippendorff's
  alpha) and the adjudication protocol for disagreements. Raw percent
  agreement alone does not count.
- **Judge stability (if LLM-judged).** Score a fixed output set twice with the
  judge (different seeds or paraphrased rubric) and report the flip rate.

### P3. Discriminative power — can the instrument tell models apart, and for how long?

A benchmark on which every current model scores 9x% is dead on arrival; one on
which they all score ~0% is a dartboard. Discrimination is a property of the
item pool relative to the current model population, and it decays.

Tests the paper must report:

- **Score spread.** Evaluate a representative slate of current models (spanning
  scale and family) and show the distribution — not just the top-3 table rows.
- **Headroom analysis.** Best current model versus the ceiling (human expert
  score or verified upper bound). State the headroom explicitly and estimate
  its half-life if the field's trajectory makes saturation foreseeable.
- **Item-level discrimination.** Which items actually separate strong from weak
  models? Report an item-discrimination statistic (point-biserial correlation
  between item success and total score, or an IRT discrimination parameter) and
  the fraction of items that are dead weight (solved by all or by none).

### P4. Contamination resistance — can the score be inflated by leakage?

If the items (or trivially recoverable variants) are in pretraining corpora,
the benchmark measures memorization plus capability in unknown proportion.

Tests the paper must report:

- **Leakage audit protocol.** n-gram overlap of items against open pretraining
  corpora; URL/source provenance check (were the items scraped from indexed
  pages?); paraphrase probes (does a model reproduce answers, distractors, or
  item text verbatim when prompted with partial items?). The full playbook is
  in `references/contamination-audit.md`.
- **Stated refresh policy.** How and when will items be rotated or regenerated,
  and what stays comparable across refreshes? A held-back private split with a
  stated release schedule counts; "we will monitor the situation" does not.

### P5. Actionability — does a failure localize a capability?

A leaderboard number tells a team where they rank; it does not tell them what
to build. An actionable benchmark converts each failure into a named,
addressable capability deficit.

Tests the paper must report:

- **Error taxonomy tied to capability dimensions.** Failures are classified
  into a taxonomy whose categories map onto the capability dimensions the
  benchmark claims to cover — with inter-annotator agreement on the taxonomy
  labels (this reuses the P2 machinery).
- **Per-dimension reporting.** Scores decompose along the taxonomy, so "model
  X fails at Y" is a supported sentence, not a vibe.
- **At least one actionable finding.** A demonstrated case where the taxonomy
  localizes a deficit that the aggregate score hides (e.g., two models with
  equal totals and disjoint failure modes).

## Severity rules (computed, not vibed)

Severity for each property is assigned by explicit rules, in order; the first
matching rule wins:

- **CRITICAL** — no test for the property appears anywhere in the document
  (all tests `NOT-IN-DOC`), **or** a reported test result actively fails the
  property (shortcut baseline within the inter-model spread of real models;
  CI wider than the claimed ranking gaps; kappa/alpha below 0.4; >50% of items
  are dead weight; verbatim leakage demonstrated with no mitigation).
- **MAJOR** — the property is claimed but at most one of its listed tests is
  reported with evidence, or a reported test omits the quantity that makes it
  checkable (agreement without a chance-corrected statistic, "low
  contamination" without the probe protocol, an error taxonomy with no
  agreement figure).
- **MINOR** — the required tests are present and pass, but a listed supporting
  test is absent (no convergent check, no judge-stability run, no headroom
  half-life estimate) or a threshold is met only marginally (kappa/alpha in
  [0.4, 0.6); headroom under 10 points without a refresh plan).

Every gap, at any severity, must be paired with **the concrete missing
experiment**: what to run, on what inputs, and what number the paper would
then report. "Discuss contamination more" is not an audit output; "run 13-gram
overlap of all items against Dolma and RedPajama and report the hit rate per
split" is.

## Audit table format

One row per property. `Evidence` cites the location in the document or says
`NOT-IN-DOC` per test.

| Property | Tests present (with evidence) | Tests missing | Severity | Missing experiment (concrete) |
|---|---|---|---|---|
| P1 Construct validity | e.g., "adversarial variants, §4.2, Tab. 3" | shortcut-exploit baseline | MAJOR | Build answer-prior + premise-deletion solvers; add both as rows to Tab. 2 |
| P2 Reliability | ... | ... | ... | ... |
| P3 Discriminative power | ... | ... | ... | ... |
| P4 Contamination resistance | ... | ... | ... | ... |
| P5 Actionability | ... | ... | ... | ... |

## Paper skeleton derived from the properties

Each property gets the section that proves it. The skeleton is the audit
turned inside out — a reader should be able to reconstruct the audit table
from the section headings alone.

1. **Introduction — the measurement claim.** State the capability being
   measured as a falsifiable claim, why existing instruments fail to measure
   it (name their validity failures in the P1–P5 vocabulary), and preview the
   validation evidence. The contribution is the *instrument*, argued as an
   instrument.
2. **Instrument design.** Task definition, item pool, scoring function. Every
   design choice justified by the property it protects (e.g., "distractors are
   sampled from model errors, not templates, to block the answer-prior
   shortcut" → P1).
3. **Validity evidence (proves P1).** Shortcut-exploit baselines, adversarial
   construct probes, convergent checks. This section exists so a skeptic
   cannot say "it measures something else".
4. **Reliability evidence (proves P2).** CIs on scores under item resampling
   and prompt rewording; annotator/judge agreement; the adjudication protocol.
5. **Model study (proves P3).** The model slate, score distributions, headroom
   analysis, item-discrimination statistics. The leaderboard table lives here,
   subordinated to the discrimination argument.
6. **Contamination audit and refresh policy (proves P4).** The leakage
   protocol, its results per split, and the rotation/held-out plan. May be a
   subsection of 5 if results are clean, but the protocol must be printed.
7. **Failure analysis (proves P5).** The error taxonomy, per-dimension
   decomposition, and at least one aggregate-hiding finding.
8. **Limitations and threats to validity.** Which properties are weakest and
   what would falsify the measurement claim; scope of the construct.

Appendices absorb: full probe prompts, annotation guidelines, per-item
statistics, contamination hit lists.

## JSON output spec

Alongside the human-readable audit, emit:

```json
{
  "benchmark": "<name>",
  "document": "<path or citation of the audited draft/plan>",
  "properties": [
    {
      "name": "construct_validity | reliability | discriminative_power | contamination_resistance | actionability",
      "tests_present": [
        {"test": "<test name>", "evidence": "<section/table/figure or quote>"}
      ],
      "tests_missing": [
        {"test": "<test name>", "missing_experiment": "<concrete run: inputs, procedure, reported number>"}
      ],
      "severity": "CRITICAL | MAJOR | MINOR | PASS",
      "severity_rule_fired": "<which rule from the severity section matched>"
    }
  ],
  "skeleton": [
    {"section": "<title>", "proves": "<property name or 'framing'>", "sketch": "<1-2 sentences>"}
  ],
  "verdict": {
    "status": "SOUND | FIXABLE | UNSOUND",
    "rationale": "<1-3 sentences citing the severities>",
    "blocking_items": ["<the CRITICAL/MAJOR missing experiments, in priority order>"]
  }
}
```

Verdict rules: any CRITICAL → `UNSOUND`; no CRITICAL but any MAJOR →
`FIXABLE`; only MINOR or PASS → `SOUND`.

## Procedure

1. **Ingest.** Read the draft, plan, or idea description. If it is an idea
   (no experiments yet), audit the *planned* tests: a plan that never intends
   to run a shortcut baseline earns the same severity as a paper that omits it.
2. **Audit P1–P5 in order.** For each listed test, locate evidence or record
   `NOT-IN-DOC`. Quote or cite locations; do not summarize from memory.
3. **Fire severity rules** mechanically and record which rule matched.
4. **Write the missing experiments** — concrete enough that a student could
   start tomorrow.
5. **Emit** the audit table, the skeleton (adapted to the paper's content, not
   copied verbatim), and the JSON block.
6. **One-line verdict** to the caller: status plus the single highest-leverage
   missing experiment.

## Usage notes

- Run at scope-lock time if possible: the cheapest place to add a held-out
  split or a shortcut baseline is before data collection finishes.
- Do not let a strong leaderboard table compensate for a missing property;
  the properties are conjunctive. A benchmark with great findings and no
  reliability evidence is `FIXABLE` at best.
- For method/algorithm papers this rubric does not apply — the artifact under
  audit must be an instrument, not a solver. If the paper's main claim is a
  new model, route it to the technical-paper skill instead.
- When the audited object measures with an LLM judge, the judge inherits the
  full audit: its construct validity (P1) and stability (P2) are part of the
  instrument, not an implementation detail.

## References

- [`references/construct-probes.md`](references/construct-probes.md): a menu
  of shortcut-exploit baselines and adversarial probe designs for P1.
- [`references/contamination-audit.md`](references/contamination-audit.md):
  the leakage-audit playbook for P4 — n-gram, provenance, and paraphrase
  probes, plus refresh-policy patterns.

## Acknowledgments

The pipeline role of this skill — structuring and auditing benchmark or
evaluation papers inside a paper-writing workflow — was inspired by
HKUSTDial's Supervisor-Skills project. The framework itself is an independent
redesign grounded in measurement theory (validity, reliability,
discrimination, contamination, actionability) and shares no taxonomy or text
with that project.
