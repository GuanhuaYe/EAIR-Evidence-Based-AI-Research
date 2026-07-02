---
name: big-finding
description: >-
  Orchestrates hypothesis-driven scientific discovery loops aimed at
  Nature/Science-grade findings, NOT paper-shipping. Replaces the
  conductor engineering pipeline when the goal is "what is the
  underlying scientific truth here" rather than "deliver this
  contribution to the camera-ready". Each loop is: (1) formulate
  falsifiable hypothesis, (2) design complete experiment BUNDLE
  (treatment + baseline + ablations + controls, all under one
  protocol_hash to prevent code-drift confounds), (3) execute,
  (4) analyze with PROVEN / REFUTED / INSUFFICIENT / CONFOUNDED /
  PIVOT decision, (5) update knowledge tree and decide next branch.
  Allows complete abandonment of starting hypothesis to chase
  emerging patterns. Persistent knowledge tree records every
  hypothesis, every experiment bundle, every dead-end. Use when
  the user wants real discovery, says 'big finding' / 'Nature-grade'
  / 'real science' / 'design experiment to test hypothesis' / 'I
  don't care about the paper, what's actually true', or when
  experimental results from the conductor reveal an unexplored
  generalizable pattern. Different from the conductor: the conductor ships;
  big-finding discovers.
license: CC-BY-4.0
---

# Big Finding

## Overview

A single number on a single dataset is an anecdote, not a finding. A
finding is a **generalizable causal claim** with explicit scope,
mechanism, and falsifiability. This skill is a branching-tree
explorer of hypothesis space, designed to converge on the smallest
number of claims that survive rigorous controlled testing.

Four principles:

1. **Every experiment is a BUNDLE, never a single arm.** A bundle
   contains the treatment, the baseline, at least one ablation, and
   at least one control — all run under the SAME protocol_hash (same
   code SHA, same data partition, same seed list). Any single-arm
   run is rejected.

2. **The knowledge tree is append-only.** Every hypothesis, every
   experiment, every decision is a node. Dead-ends are kept
   (marked REFUTED) so future loops don't re-walk them. PIVOTs are
   explicit and traceable.

3. **The goal is the smallest set of PROVEN findings that
   generalize.** "Better on MIMIC-III by +0.03" is not a finding.
   "X mechanism beats Y mechanism across N distinct domains with
   stat-sig effect" is a finding. Anything less is a step on the
   path.

4. **One experiment, one agent.** LLM quality degrades as context
   grows: a fresh, focused context is the model's smart zone; a long
   transcript dragging every previous experiment is its dumb zone.
   So agents are never reused across experiments. Each bundle is
   executed by a freshly spawned agent whose context holds only the
   hypothesis node, the preregistered task.json, pointers to input
   data, and the relevant veto-list entries — never the raw history
   of earlier experiments. Before the agent is closed, everything
   worth keeping is written to disk: results, audit outputs,
   decision.md, the tree.json update, the ledger entry. If it is not
   on disk, it did not happen. The next experiment gets a new agent
   whose context is rebuilt from the tree and ledger, not inherited.
   Resuming an agent is allowed only WITHIN one experiment (e.g. a
   Coder fixing its own audited bundle), never across experiments.
   This buys two things at once: capability (a small fresh context
   outperforms the same model at 100k+ tokens on exacting analysis)
   and independence (an agent that watched experiment N-1 succeed
   will steer experiment N toward consistency — fresh agents are the
   closest thing to analyst blinding a pipeline can get).

## When to invoke

- User says "big finding", "Nature-grade", "real science", "what is
  actually true", "I don't care about the paper", "design controlled
  experiment", "test this hypothesis rigorously".
- An anomaly emerges from conductor-driven experiments (e.g., result
  counter-intuitive, ablation diverges from main effect).
- 2+ prior experiments produced conflicting signals on the same
  question.

Do NOT invoke for:
- Paper section drafting (use the paper layer).
- Single-arm "is X higher than Y" measurements with no protocol
  control.
- Rebuttal experiments (use rebuttal-drafter + the conductor chain).

## Operating procedure

### Stage 1 — Hypothesis formulation

INPUT: current `tree.json` state + user goal OR triggering anomaly.

OUTPUT: 1-3 candidate hypotheses, each with:

| Field | Format | Example |
|---|---|---|
| `short` | ≤15 words declarative | "Constrained-letter LLM rerank beats sentence-transformer in narrow-domain disambiguation" |
| `falsifiable_form` | concrete metric + threshold | "MIMIC-III cm_F1: letter ≥ sentence-transformer by ≥0.02, paired-t p<0.05, sign 4+/5 seeds" |
| `generalization_scope` | the population it should hold over | "all narrow-domain (vocab ≤ 10K) candidate-disambiguation tasks" |
| `mechanism_claim` | causal story | "single-step constrained generation integrates all context; two-stage pipeline loses information per stage" |
| `alternatives_to_rule_out` | rival explanations | "(a) confound: different K; (b) noise from different seeds; (c) sentence-transformer model under-tuned" |
| `kill_criteria` | what makes it dead | "if letter < ST on any single dataset under controlled K, REFUTED" |

If user asks vague question ("is X better than Y"), the skill MUST
push back: "what's the generalization scope, what threshold counts
as different, what's your prior on the mechanism?" — no anonymous
hypotheses.

### Stage 2 — Experiment bundle design

A bundle is REJECTED if it lacks any of:

- **Treatment arm(s)** — the hypothesis instantiation
- **Baseline arm** — minimal/control point of comparison
- **≥1 ablation arm** — varying ONE confounding variable
- **Negative control** — should give null result (validity check)
- **Positive control (optional but recommended)** — known-good, validity check

All arms MUST share:

- Same git SHA / code version (recorded as `code_hash`)
- Same data partition (recorded as `data_hash`)
- Same hyper-params except the ONE being varied per arm
- Same hardware class (A100 80GB / 4090 24GB — recorded)
- Same seed list, same number of seeds
- Same eval protocol (split key, n_eval_test, error injection seed)

`scripts/lineage_check.py` verifies this before launch. Failure to
verify = bundle REJECTED.

Bundle is described in `bundle.yaml` with one block per arm. See
`references/experiment_bundle_spec.md`.

### Stage 3 — Execute + monitor

Standard agent chain (Coder → Auditor → Engineer → Runner) BUT every
arm of the bundle runs as ONE batch (e.g., same tmux job that
iterates through arms, OR a wave of parallel tmux sessions launched
within the same hour).

If ANY arm fails, the bundle is INCOMPLETE — re-run the failed arm,
do not partial-analyze. The bundle is the unit of measurement.

### Stage 4 — Analysis & decision

Analysis is the FORMAL phase, not exploratory looking. Decision tree:

| Pattern | Status | Action |
|---|---|---|
| Treatment > baseline by ≥falsifiable threshold + ablation-invariant + control behaves as expected | **PROVEN** | Mark node; ask "does this generalize? what's the next breadth test?" |
| Treatment > baseline but only with one ablation configuration | **CONFOUNDED** | The hypothesis was wrong; the confound is the real finding. Spawn child hypothesis isolating the confound. |
| Treatment ≤ baseline + stat-sig | **REFUTED** | Mark node; write a 3-sentence "why it failed" note; consider child hypothesis (alternative mechanism). |
| Treatment vs baseline insignificant + n<10 seeds | **INSUFFICIENT** | Schedule more seeds; don't claim either way. |
| Ablation reveals different pattern than main hypothesis predicted | **PIVOT** | The data is telling a different story. Spawn child hypothesis from the data, mark this node deprecated. |
| Negative control fired | **PROTOCOL_BROKEN** | Something in the protocol is wrong. Bundle invalid. |

Every analysis writes `decision.md` with:
- Per-arm 5-seed metrics with CIs
- The applied decision rule + which case fired
- 3-sentence rationale
- Recommended next node

### Stage 5 — Knowledge tree update + next decision

`scripts/tree.py append <node>` writes the node to `tree.json` and
links to parent. Visualize anytime with `scripts/visualize_tree.py`.

Decision for next iteration:

1. If PROVEN and `meets_nature_worthy_test()` → terminal. Run
   `cite-as-finding` ceremony (export to a findings catalogue).
2. If PROVEN but not yet generalized → child node = breadth test on
   a different domain.
3. If REFUTED → look at "alternatives_to_rule_out" — pick the most
   likely alternative as next hypothesis.
4. If PIVOTED → write the new hypothesis from the data, recurse.
5. If INSUFFICIENT → re-run with more seeds; don't branch yet.
6. If CONFOUNDED → isolate the confound as the new hypothesis.

### Big-finding criterion (Nature-worthy test)

A finding passes the bar iff ALL FIVE hold:

1. **Generalizes** across ≥3 distinct domains/datasets, NOT MIMIC
   variants. Different vocabulary, different task, different
   distribution.
2. **Mechanistic** — has a causal story tested by ablation. Not
   just correlation.
3. **Falsifiable** — could be killed by a clearly specified future
   experiment.
4. **Counter-intuitive OR foundational** — contradicts prior
   literature OR establishes a new property. "Slightly higher number
   on X" never qualifies.
5. **Quantitative magnitude** — has a number with CI, not just sign.

Findings that pass go in `findings_catalogue.md`. Findings that
don't pass become refinement targets.

## Knowledge tree schema

`tree.json` is the persistent source of truth. Schema in
`references/knowledge_tree_schema.md`. Quick form:

```json
{
  "nodes": {
    "H001": {
      "parent": null,
      "type": "hypothesis",
      "status": "PROVEN | REFUTED | OPEN | INSUFFICIENT | CONFOUNDED | PIVOTED | DEPRECATED",
      "short": "...",
      "falsifiable_form": "...",
      "generalization_scope": "...",
      "mechanism_claim": "...",
      "alternatives_to_rule_out": [...],
      "kill_criteria": "...",
      "created_at": "ISO 8601",
      "experiments": ["E001", "E002"],
      "children": ["H002", "H003"],
      "notes": ["..."]
    }
  },
  "experiments": {
    "E001": {
      "hypothesis": "H001",
      "bundle_path": "experiments/E001/bundle.yaml",
      "protocol_hash": "sha256:...",
      "code_hash": "sha256:...",
      "data_hash": "sha256:...",
      "arms": ["arm_treatment", "arm_baseline", "arm_ablation_K12", "arm_ablation_K28", "arm_control_neg"],
      "result_path": "experiments/E001/results.json",
      "decision_path": "experiments/E001/decision.md",
      "decision": "PROVEN | REFUTED | ...",
      "run_window": "2026-06-29T15:00 .. 2026-06-29T18:30"
    }
  },
  "findings_catalogue": ["F001", "F002"]
}
```

The tree is append-only. Status changes write a new event, not
mutate. Older snapshots stay readable.

## Cross-skill interactions

- **the conductor**: Big-finding produces hypotheses + experiment bundles.
  the conductor's agent chain (Coder/Auditor/Engineer/Runner) is the
  underlying execution engine for each arm. Big-finding sits ABOVE
  the conductor, deciding what to run and why; the conductor decides how to run
  it reliably.
- **idea-evaluator**: Use to score whether a candidate hypothesis is
  worth pursuing before designing a bundle. Don't pursue
  Faster-Cheaper-Broader on top of Higher unless the gain matters.
- **citation-verifier**: Use to find prior work that already proved
  or refuted the hypothesis. Don't waste experiments on settled
  questions.
- **pre-submission-reviewer** / **rebuttal-drafter**: Only after
  big-finding has produced PROVEN findings and the user explicitly
  wants to write a paper. Use the conductor stage 3+ to ship.

## Constraints and overrides

- **No single-arm experiments.** A bundle must have multi-arm
  structure or it's rejected.
- **No cross-day comparisons.** All arms in a bundle run within the
  same 24h window unless explicitly waived with documented reason.
- **No silent ablation.** If a yaml param differs between arms, it
  must be in the bundle's `varied_params` list and have a
  documented purpose.
- **No "we got a positive result, let's stop".** PROVEN status
  requires the bundle's decision rule pre-registered BEFORE the
  experiment runs. (Standard pre-registration practice.)
- **Track confounds explicitly.** When a previous the conductor experiment
  has confounded results (e.g., different code versions), the
  big-finding skill MUST flag that prior comparison as "lineage
  broken — do not cite" in the tree.

## References

- `references/hypothesis_template.md` — falsifiable hypothesis form
- `references/experiment_bundle_spec.md` — what counts as complete
- `references/knowledge_tree_schema.md` — tree.json format
- `references/analysis_decision_tree.md` — the 6-case decision logic
- `references/nature_worthy_test.md` — the 5-condition test
- `scripts/tree.py` — CRUD on tree.json
- `scripts/visualize_tree.py` — ASCII tree of explored paths
- `scripts/lineage_check.py` — verify bundle protocol controls
