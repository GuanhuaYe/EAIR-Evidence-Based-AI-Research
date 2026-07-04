# Knowledge tree schema

`tree.json` is the persistent source of truth for all hypothesis
exploration. Stored at `<paper_dir>/big_finding/tree.json`.

## Top-level structure

```json
{
  "version": 1,
  "project": "lattice-clean-2027 OR <other>",
  "created": "2026-06-29T17:00:00+08:00",
  "nodes": {},
  "experiments": {},
  "findings_catalogue": []
}
```

## Node (hypothesis or observation) schema

```json
"H001": {
  "id": "H001",
  "parent": null,
  "type": "hypothesis | observation | pivot",
  "status": "OPEN | PROVEN | REFUTED | INSUFFICIENT | CONFOUNDED | PIVOTED | DEPRECATED",
  "short": "≤15 word declarative sentence",
  "falsifiable_form": "concrete metric + threshold + n + stat test",
  "generalization_scope": "the population the claim ranges over",
  "mechanism_claim": "causal story",
  "alternatives_to_rule_out": [
    {"name": "K-confound", "ablation": "hold K=28 constant"},
    {"name": "seed noise", "ablation": "n=5 seeds minimum"}
  ],
  "kill_criteria": "concrete failure condition",
  "created_at": "ISO 8601",
  "modified_at": "ISO 8601",
  "status_history": [
    {"at": "ISO 8601", "status": "OPEN", "by": "session-id"},
    {"at": "ISO 8601", "status": "PROVEN", "by": "session-id", "experiment": "E003"}
  ],
  "experiments": ["E001", "E002"],
  "children": ["H002", "H003"],
  "notes": ["free-form annotations"]
}
```

## Experiment node schema

```json
"E001": {
  "id": "E001",
  "hypothesis_id": "H001",
  "bundle_path": "experiments/E001/bundle.yaml",
  "code_hash": "sha256:abc...",
  "data_hash": "sha256:def...",
  "protocol_hash": "sha256:<combined>",
  "arms": [
    {"name": "treatment", "config_overlay": {...}, "purpose": "..."},
    {"name": "baseline",  "config_overlay": {...}, "purpose": "..."},
    ...
  ],
  "lineage_check_passed": true,
  "decision_rule": "pre-registered string",
  "run_window": {
    "start": "ISO 8601",
    "end": "ISO 8601"
  },
  "hardware": "datacenter-80gb",
  "vllm_build": "0.21",
  "result_path": "experiments/E001/results.json",
  "decision_path": "experiments/E001/decision.md",
  "decision": "PROVEN | REFUTED | INSUFFICIENT | CONFOUNDED | PROTOCOL_BROKEN | PIVOTED",
  "gpu_h_consumed": 4.5
}
```

## Status semantics

| Status | Meaning | Action |
|---|---|---|
| OPEN | Hypothesis stated, no experiment yet | Design bundle |
| PROVEN | Experiment satisfied falsifiable form | Mark; consider generalization test |
| REFUTED | Experiment violated falsifiable form | Mark; consider alternative hypothesis as child |
| INSUFFICIENT | Effect direction inconclusive, n too small | Schedule more seeds, same bundle |
| CONFOUNDED | Treatment effect explained by ablation variable | Spawn child hypothesis about the confound |
| PIVOTED | Data revealed unexpected pattern; original question abandoned | Spawn child = new hypothesis from the pivot |
| DEPRECATED | Superseded by a better-formulated hypothesis | Keep for history; future loops skip |

Status changes are EVENTS appended to `status_history`. The current
status is `status_history[-1].status`.

## Tree invariants

- **Append-only experiments**: an experiment node, once committed,
  is immutable. Re-running = new experiment id.
- **Parent ID monotonic**: H002.parent ∈ {H001, null}. No
  forward-references.
- **Children stay even if PIVOTED**: pivoted parents keep their
  children visible in tree (for audit). Children inherit no claim
  from PIVOTED parent.
- **Findings catalogue is curated**: only nodes with status=PROVEN
  AND meets_nature_worthy_test() are added.

## ASCII visualization format

```
└── H001 [PROVEN] single-step joint scoring beats two-stage retrieve-then-rank in small-catalog candidate matching
    │   E001: PROVEN (paired-t p=0.003, n=5, hardware datacenter-80gb, 4.2 GPU-h)
    │   E002: CONFOUNDED (K-ablation: K=12 reverses sign — needs deeper dive)
    │
    ├── H002 [OPEN] joint-scoring advantage scales with vocab size (K-effect mechanism)
    │       (no experiments yet)
    │
    └── H003 [REFUTED] joint-scoring advantage holds on non-BENCH-A small-catalog tasks
            E003: REFUTED (on synthetic vocab-500 task, no significant difference)
```

Use `scripts/visualize_tree.py [--node-filter ...] [--status ...]`.

## Lineage broken markers

When a comparison from OUTSIDE the bundle system (e.g., a the conductor
experiment) is referenced in a hypothesis, mark with
`lineage_warning: "..."` in node notes.

Example: "v3.1 R5 vs W2 R6 0.247 vs 0.211 — code_hash differs
(June 11 vs June 17 implementations) — DO NOT cite as evidence for
or against any hypothesis."

This prevents the W2 R6 disaster pattern (comparing two different
implementations under the same name).
