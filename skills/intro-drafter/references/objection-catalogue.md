# Objection Catalogue by Claim Type

Each entry: **trigger** (the evidence/claim profile that makes the
objection likely), **default scores** (likelihood L / lethality D on
{1,2,3}; adjust from the actual claim graph), and **neutralization
pattern** (the move the paragraph plan should make, and what kind of
evidence anchor it needs).

Objection ids are stable so coverage tables can reference them.

## Universal objections (apply to all claim types)

### OBJ-INCREMENTAL — "This is incremental"
- Trigger: nearest prior work is < 2 years old and the headline delta
  is a metric improvement rather than a capability change.
- Default: L3 / D3 for method claims; L2 / D2 otherwise.
- Neutralize: state the *qualitative* delta before the quantitative
  one — the case the prior method cannot handle at any tuning budget.
  Anchor: the experiment or example that isolates the delta
  (an ablation table or a failure-case figure), not the headline table.

### OBJ-WHY-NOW — "Why is this paper appearing now?"
- Trigger: the problem is old, or the technique existed for years.
- Default: L2 / D1, rising to D2 at venues that prize timing narratives.
- Neutralize: name the enabling change (new data regime, new hardware,
  new model class, new deployment reality) in the opening paragraph.
  Anchor: a citation cluster or a measurement in the paper (Sec/Fig).

### OBJ-OVERCLAIM — "The claims outrun the evidence"
- Trigger: any verb above its licensed rung on the claim-strength
  ladder; superlatives ("first", "solves") without a scoping clause.
- Default: L2 / D3 — reviewers forgive weak results sooner than
  strong verbs on weak results.
- Neutralize: fix the verbs; add explicit scope ("in the offline
  setting", "for models under 10B"). Anchor: the limitation-bearing
  section, cited where the claim is made.

### OBJ-CHERRY — "Results look cherry-picked"
- Trigger: evidence spans few seeds, few datasets, or only the
  favorable slice; qualitative examples all succeed.
- Default: L2 / D2.
- Neutralize: preview the breadth of evaluation (n datasets, n seeds,
  worst-case slice) in the results-preview paragraph and show one
  failure honestly. Anchor: the full-results table and the failure
  analysis subsection.

## Method claims

### OBJ-UNFAIR — "Baselines are unfair"
- Trigger: baselines older than the strongest known competitor;
  compute/tuning budgets not equalized; a well-known baseline absent.
- Default: L3 / D3.
- Neutralize: name the strongest baseline *by name* in the
  Introduction and state the equalized-budget protocol in one clause.
  Anchor: the experimental-setup section and the head-to-head table.

### OBJ-NOSCALE — "Won't scale beyond toy settings"
- Trigger: all experiments at small model/data/problem sizes; method
  has a superlinear-cost component.
- Default: L2 / D3 at systems/ML venues; L2 / D2 elsewhere.
- Neutralize: give the cost story (complexity or wall-clock) next to
  the idea reveal, and preview the largest-scale result early.
  Anchor: the scaling figure or cost table.

### OBJ-MECHANISM — "You show it works, not why"
- Trigger: gains reported without ablation or with entangled changes.
- Default: L2 / D2 for method claims (D3 if the paper's pitch is
  understanding rather than performance).
- Neutralize: promise the isolation experiment (ablate the one
  component the story credits) where the idea is introduced.
  Anchor: the ablation table.

## Problem-formulation claims

### OBJ-NICHE — "Who needs this problem?"
- Trigger: the problem statement is new and no deployed system or
  measurable population is shown to suffer from it.
- Default: L3 / D3 — the lethal objection for new-problem papers.
- Neutralize: open with the concrete sufferer (a system, a workload,
  a user population) and quantify the pain. Anchor: a motivating
  measurement figure or a real-incident citation in the paper.

### OBJ-ILLPOSED — "The formulation is wrong or already covered"
- Trigger: an adjacent formulation exists (special case, or the new
  problem reduces to a known one under mild assumptions).
- Default: L2 / D3.
- Neutralize: state the adjacent formulation and the exact assumption
  under which the reduction fails. Anchor: the formalization section
  and, if present, a separation example or impossibility argument.

## Measurement / analysis claims

### OBJ-CORRELATION — "Correlation, not mechanism"
- Trigger: the headline finding is observational; confounders are
  plausible and not controlled.
- Default: L3 / D3.
- Neutralize: preview the intervention or control (a controlled
  synthetic setting, a natural experiment, a confounder regression)
  in the same paragraph that states the finding. Anchor: the
  intervention experiment's table/figure.

### OBJ-SATURATED — "That benchmark is saturated / gamed"
- Trigger: evidence rests on a benchmark with known leakage or
  ceiling effects.
- Default: L3 / D2 (D3 if it is the only benchmark).
- Neutralize: acknowledge the benchmark's status explicitly and pair
  it with a fresher or held-out evaluation. Anchor: the secondary
  evaluation table.

### OBJ-GENERALIZE — "Finding won't transfer beyond the studied setting"
- Trigger: one model family, one language, one domain.
- Default: L2 / D2.
- Neutralize: scope the claim honestly (ladder rung 2 verbs) and
  preview the widest replication available. Anchor: the
  cross-setting table.

## Resource claims (datasets, tools, benchmarks)

### OBJ-NEEDED — "We already have datasets/tools for this"
- Trigger: >= 2 existing resources in the same space.
- Default: L3 / D3.
- Neutralize: a dimension table in spirit — name the two axes on
  which every existing resource fails and this one does not.
  Anchor: the comparison table.

### OBJ-SHELFLIFE — "This will be stale in a year"
- Trigger: resource derived from current model outputs or a fast-
  moving distribution.
- Default: L2 / D2.
- Neutralize: describe the refresh/extension protocol, not just the
  artifact. Anchor: the maintenance/protocol section.

## Theory claims

### OBJ-ASSUME — "Assumptions are doing all the work"
- Trigger: main theorem needs assumptions that rarely hold in
  practice, or that near-imply the conclusion.
- Default: L3 / D3.
- Neutralize: state the strongest assumption in plain language in the
  Introduction and say what breaks without it (or point to the
  relaxation). Anchor: the theorem statement and the
  assumption-discussion subsection.

### OBJ-VACUOUS — "Bounds are vacuous / result is unsurprising"
- Trigger: bound has large constants or the rate matches folklore.
- Default: L2 / D2.
- Neutralize: pair the theorem with the empirical regime where the
  bound is informative, or with the previously open question it
  closes. Anchor: the numeric-illustration figure or the prior-bound
  comparison.

## Using the catalogue

1. Select the universal block plus the block matching the claim type;
   scan other blocks if the paper straddles types.
2. Re-score defaults against the actual claim graph — defaults encode
   the typical case, not this paper.
3. Anything scoring >= 4 goes on the active list and must appear in
   the coverage table. Lethality-3 entries need anchored
   neutralizations, not rhetorical ones.
