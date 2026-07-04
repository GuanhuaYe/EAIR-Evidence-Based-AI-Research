# Experiment bundle spec

A bundle is the unit of measurement. Single-arm runs are never
accepted as evidence for a hypothesis.

## Required arms

Every bundle MUST contain:

1. **≥1 treatment arm** — the hypothesis instantiation
2. **≥1 baseline arm** — minimal/no-op comparison
3. **≥1 ablation arm** — varies ONE confounding variable
4. **≥1 negative control** — should produce null result (validity)
5. **≥0 positive control** — known-good (recommended, not required)

Minimum bundle size: 4 arms.

## Required statistical protocol — `cv_folds`

Every bundle MUST declare `cv_folds: K` at top level:

| K | Meaning | Allowed verdict ceiling |
|---|---|---|
| 1 | Single fixed train/test split + multi-seed injection | **PROVEN_SINGLE_SPLIT** (cannot reach Nature-worthy) |
| ≥5 | K-fold cross-validation; each fold has disjoint test partition | **PROVEN** (Nature-worthy gate accessible) |
| ≥10 | 10-fold or repeated 5-fold | strongest evidence tier |

A bundle with `cv_folds: 1` can produce a useful finding but the verdict
is tagged `_SINGLE_SPLIT` and **cannot** pass the Nature-worthy gate
(`nature_worthy_test.md`) until a follow-up bundle with `cv_folds: ≥5`
re-confirms.

Lineage_check enforces this — if cv_folds is missing or < 5, the
bundle's `decision_rule` MUST include a `_SINGLE_SPLIT` suffix on the
PROVEN_if clause.

### Why CV is mandatory

A fixed train/test split could be "lucky" — the test partition might
happen to contain easy/hard examples that favor one arm by accident.
Multi-seed (varying injection randomness within the same split) only
tests injection-noise robustness, NOT data-partition robustness.

**5-fold CV** rotates the test partition: each fold uses 4/5 of data
for train + 1/5 for test, no overlap. Aggregating across 5 folds
tests both: (a) injection robustness within a fold (if you run multi-
seed per fold too), and (b) cross-fold partition stability.

For "Nature-worthy" claims, cross-partition stability is non-negotiable.

### Implementation requirements

When `cv_folds: K`:
- The runner MUST accept a `fold_id ∈ [0, K-1]` parameter
- Train/test split MUST be controlled by `(split_seed_base + fold_id)` so each fold has a deterministic, reproducible partition
- Test sets MUST be DISJOINT across folds (verified by `assert_no_test_overlap` post-hoc)
- Per-fold metrics MUST be aggregated as: mean ± fold-std (NOT seed-std within fold)
- Statistical test should be **paired** across folds OR **mixed-effects** (fold as random effect, seed nested within fold if multi-seed-per-fold)

## Bundle YAML schema

```yaml
bundle_id: E001
hypothesis: H001
created: 2026-06-29
code_hash: sha256:<git-sha or content-hash if no git>
data_hash: sha256:<hash of data partition files>
seed_list: [1, 2, 3, 4, 5]
hardware: datacenter-80gb
eval_protocol:
  split_key: subject_id
  injection_seed_base: 1000
  n_errors_per_type: 500
  error_types: [typo, missing_value, unit_error, fk_violation, code_mismatch, out_of_range]

arms:
  treatment:
    description: "Constrained-letter LLM rerank (kg_v31_reranker.LLMReranker)"
    code_path: kg/kg_v31_reranker.py
    config_overlay:
      rerank: constrained_letter
      rerank_model: Qwen2.5-7B-Instruct
      kg_candidates_k: 28
    purpose: "Test the hypothesis directly"

  alt_arm:
    description: "Sentence-transformer rerank + Qwen-14B router (scripts/within_bucket_rerank.py)"
    code_path: scripts/within_bucket_rerank.py
    config_overlay:
      rerank: sentence_transformer
      rerank_model: all-MiniLM-L6-v2
      router_model: Qwen2.5-14B-Instruct
      kg_candidates_k: 28
    purpose: "Test the alternative architecture"

  baseline:
    description: "No rerank, proposer-only with KG anchor"
    config_overlay:
      rerank: none
      kg_candidates_k: 28
    purpose: "Establish floor performance"

  ablation_K12:
    description: "Treatment with K=12 (rule out K-confound)"
    code_path: kg/kg_v31_reranker.py
    config_overlay:
      rerank: constrained_letter
      kg_candidates_k: 12
    purpose: "Rule out K as the cause of treatment win"

  negative_control:
    description: "No KG anchor, no rerank — pure LLM proposer"
    config_overlay:
      kg_anchor: disabled
      rerank: none
    purpose: "Confirm KG matters; should produce ~0 cm_F1"

varied_params:
  - rerank: ["constrained_letter", "sentence_transformer", "none"]
  - kg_candidates_k: [12, 28]
  - kg_anchor: ["enabled", "disabled"]

# Pre-registered decision rule (write BEFORE running)
decision_rule:
  PROVEN_if: "treatment mean ≥ alt_arm mean by ≥0.02, paired-t p<0.05, sign 4+/5 seeds; AND ablation_K12 preserves the ranking; AND negative_control < 0.01"
  REFUTED_if: "treatment mean < alt_arm mean OR paired-t p>0.10"
  CONFOUNDED_if: "treatment > alt_arm in main but ablation_K12 reverses the ranking"
  PROTOCOL_BROKEN_if: "negative_control > 0.05"
```

## Lineage check rules

`scripts/lineage_check.py` verifies BEFORE launch:

1. All arms reference same `code_hash` (or document why not)
2. All arms reference same `data_hash`
3. `seed_list` identical across arms
4. `eval_protocol` identical across arms
5. `varied_params` list explicitly enumerates ALL differences
6. No undocumented config diff between arms
7. `decision_rule` is filled in (pre-registration)
8. Hardware class consistent (or documented why mixed)

If any check fails → bundle REJECTED, do not launch.

## Anti-confound rules (learned from W2 R6 vs v3.1 R5 disaster)

- **Same code version**: All arms run against the SAME commit / file mtime. If you must mix versions, document why and treat the comparison as exploratory not confirmatory.
- **Same eval data**: Same split key, same injection seed base, same n_errors_per_type, same error_types list.
- **Same hardware**: datacenter-80gb vs consumer-24gb can have throughput differences and rare numerical differences. Note hardware class.
- **Same vLLM build**: vLLM 0.21.0 vs 0.21.1 may have subtle sampling differences. Pin the build.
- **Same prompt template**: If prompt text differs across arms (other than the controlled variable), the comparison is invalid.

## Bundle execution

Run arms in the smallest possible time window:

- Preferred: same job, iterates through arms in one run
- Acceptable: parallel tmux sessions launched within the same hour
- Borderline: same day (note timestamps)
- Rejected: spanning code-modification events (e.g., file mtime changed between arms)

## Output structure

```
experiments/E001/
├── bundle.yaml
├── code_snapshot/                  # tarball of code dir at run time
│   └── lattice-clean-2026-06-29-Tfoo.tar.gz
├── data_partition_hash.json
├── results.json                    # per-arm per-seed metrics
├── per_seed_detail.json
├── decision.md                     # the pre-registered rule's outcome
└── audit.log
```
