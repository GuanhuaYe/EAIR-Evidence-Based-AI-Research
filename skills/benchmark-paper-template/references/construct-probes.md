# Construct Probes Menu (P1)

Goal: show that the score is driven by the claimed capability, not by a
cheaper correlate present in this particular item pool. Two families of
evidence: degenerate solvers that *lack* the capability (they should score
low), and item perturbations that toggle whether the capability is *needed*
(scores should move).

## A. Shortcut-exploit baselines (degenerate solvers)

Build at least one; report it as a row in the main results table.

| Baseline | What it exploits | Applies to |
|---|---|---|
| Majority / prior answerer | Class or answer-position imbalance | Any classification or MCQ format |
| Option-only model | Distractor quality (answer guessable without the question) | MCQ; feed options, hide the stem |
| Premise-deletion model | Items solvable without the critical input (image, table, document, code context) | Any grounded task; delete the grounding |
| Surface-heuristic scorer | Length, lexical overlap, formatting cues correlated with gold labels | Judged or reference-matched free-form tasks |
| Retrieval-only solver | Items answerable by lookup in the construction sources | Knowledge-flavored tasks; BM25/embedding search over the source corpus |
| Frozen small model + format tuning | Score attributable to output formatting rather than capability | Tasks scored by strict parsers |

Reading the result: a shortcut baseline is *supposed* to be far below real
models. If it lands within the inter-model spread, the metric is measuring
the shortcut — this fires the CRITICAL severity rule. If it is merely well
above chance, quantify how much headroom the shortcut explains and say so in
limitations.

## B. Adversarial construct probes (item perturbations)

Create matched item variants where the claimed capability is required in one
and bypassed in the other; a valid instrument shows a sharp score gap between
variants, and the gap must exceed the P2 confidence interval.

- **Necessity variant.** Remove or corrupt exactly the element the capability
  operates on (swap the entities in a reasoning chain, break the dependency in
  a code context, alter the premise that the plan must respect). Models
  scoring equally on original and corrupted items are not using the element.
- **Sufficiency variant.** Provide the capability's output directly (the
  intermediate reasoning step, the retrieved fact, the plan sketch). The score
  jump bounds how much of the failure is attributable to the claimed
  capability versus everything downstream of it.
- **Distractor stress test.** Regenerate distractors from strong-model errors
  instead of templates; report the score drop. Template distractors are the
  most common construct leak in MCQ benchmarks.
- **Format invariance.** Re-render the same items in a different surface
  format (order, phrasing, serialization). Capability should be format-stable;
  large deltas mean the metric is partly measuring format compliance (or
  contamination — cross-check with the P4 paraphrase probe).

## C. Convergent and divergent checks

- **Convergent:** correlate benchmark scores with an independent measure of
  the same construct — expert human ratings on a model sample, or an
  established downstream task the capability should predict. Report the
  correlation coefficient with a CI over the model slate (n = number of
  models, so keep claims modest; rank correlation is usually the honest
  choice).
- **Divergent:** correlate against a measure of a *different* construct (e.g.,
  raw knowledge recall when the claim is reasoning). A benchmark that
  correlates ~1.0 with an existing generic benchmark measures nothing new —
  this is a construct-redundancy finding worth printing even when
  uncomfortable.

## Minimal reporting block for the paper

> Construct probes: {shortcut baseline(s)} score {x} vs weakest real model
> {y} (chance = {z}); necessity variant gap = {a} points (CI ±{b});
> convergent rank correlation with {external measure} = {rho}; divergent
> correlation with {generic benchmark} = {rho'}.
