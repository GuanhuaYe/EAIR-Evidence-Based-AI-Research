---
name: supervisor
description: >
  Auto-triggered checkpoint system + autonomous decision layer. Replaces human checkpoints by automatically
  performing reviews and go/no-go decisions at critical nodes.
  Trigger words: /supervisor, self-check, audit, checkpoint.
  **This skill should be auto-triggered during other skill execution; it does not require explicit user invocation.**
argument-hint: "<check|gate|review-dispatch> [context]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, Agent
user-invocable: true
---

# Supervisor: Auto-Checkpoint + Autonomous Decision System

Replaces human checkpoints. Automatically performs reviews and makes go/no-go decisions at critical nodes, recording decision rationale in PIPELINE_STATE.json when necessary.

> **v1 scope note:** This document references `idea-gen`, `exp-run`,
> `exp-engineer`, and `paper-write` — stage skills from the full internal
> pipeline that ship in a later release (see the repo Roadmap). The
> checkpoint/gate logic itself is stage-agnostic: read those names as "your
> idea-generation step", "your experiment-execution step", etc.

## Core Principles

1. **Auto-triggered** — Does not wait for user prompts; proactively executes when trigger conditions are met
2. **Decision transparency** — Every decision outputs structured rationale, auditable by user after the fact
3. **Conservative bias** — Better to check once more than to miss a bug or false novelty claim
4. **Single authority** — All review logic is centralized in supervisor; other skills must not define their own review processes ([M3] fix)

---

## Checkpoint 1: CODE AUDIT (Before Experiment Launch) — The Single Entry Point for Code Review

**Trigger condition:** About to run `python3 <experiment>.py` or `nohup ... &`

**Note:** This is the single entry point for all experiment code reviews. exp-run must not define its own Pre-Launch Audit; it should invoke supervisor CP1 instead. ([M3] fix)

**Execution steps:**
1. Re-read the entire script
2. Check for known failure modes:
   - `dtype=` vs `torch_dtype=` in `from_pretrained`
   - Tautological comparisons (oracle == oracle)
   - Shape mismatches (batch*seq vs seq indexing)
   - Scale mismatches (logits vs probabilities in interpolation)
   - Missing `attn_implementation="eager"` when using manual attention masks
   - Hardcoded device IDs conflicting with CUDA_VISIBLE_DEVICES
   - Off-by-one in token indexing
   - Circular reasoning: using test labels in "prediction"
   - Idea-code consistency: does the script implement the method described in the idea document?
   - Control group validity: is the baseline/random control fair?
   - metrics.json schema compliance: will the script output a metrics.json conforming to the standard schema (see G1)?
3. Output `| Issue | Severity | Line | Status |` table
4. **CRITICAL issues → fix then re-audit; MEDIUM → flag but allow to proceed**

---

## Checkpoint 2: NOVELTY AUDIT (Before Claiming Novel)

**Trigger condition:** About to output claims such as "no one has done this", "novel", "first to propose", etc.

**Relationship with idea-gen.verify ([O1] fix):**
- The `verify.py` results from idea-gen.generate step 3 are cached in the ideas table of papers.db
- When Gate1 invokes CP2, **it first checks for cached results** and reuses them if available, without re-searching
- CP2 is re-executed only when an idea has been modified through Adversarial Refinement
- This way each idea consumes at most 5 SerpAPI calls, not 10

**Execution steps:**
1. Check if the ideas table in papers.db already has novelty results for this idea → if so, return directly
2. Google Scholar search (SerpAPI, ≤5 queries, strictly observe the daily limit of 100 total calls):
   - `"<core method keywords>"`
   - `"<problem keywords>"`
   - Known competitor names
3. For each result, evaluate 3-axis overlap:
   - **Problem overlap:** Solves the same problem?
   - **Method overlap:** Uses the same technique?
   - **Setting overlap:** Same constraints (frozen model, post-training)?
4. Output verdict:
   - **Novel** — No paper matches all 3 axes
   - **Partially novel** — Matches 2/3 axes; must clearly state the differentiating dimension
   - **Not novel** — Matches 3/3 axes; must pivot or abandon
5. Identify the **strongest competitor** and state the difference in one sentence
6. Write output to `$PROJECT_ROOT/{idea_id}/data/related_work.json` and the ideas table in papers.db

**Fallback when SerpAPI is unavailable ([G5] fix):**
- Rely solely on local ChromaDB + arXiv search
- Mark novelty assessment as `confidence: "LOW"`
- Gate1 hard-caps the novelty score at 0.6 (no high-confidence novel claims allowed)
- Record `"serpapi_unavailable": true` in the supervisor_log of PIPELINE_STATE.json

---

## Checkpoint 3: RESOURCE AUDIT (Before Long Experiments)

**Trigger condition:** Experiment is expected to run >10 minutes

**Execution steps:**
1. `nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader` to check all GPUs
2. `ps aux | grep python | grep -v grep` to identify processes on each GPU (ours vs others')
3. For each idle GPU: can we parallelize?
4. Estimate: required VRAM vs available VRAM — will it OOM?
5. Output `| GPU | Status | Can Parallelize? | What? |` table
6. **Auto-assign:** Set the experiment's DEVICE/CUDA_VISIBLE_DEVICES to the least busy GPU; do not leave idle GPUs unused while stacking experiments on busy ones
   - Prefer the GPU with the lowest memory.used
   - If DEVICE is hardcoded to the wrong GPU in the code, **the code must be modified before launch**

---

## Checkpoint 4: HONEST ASSESSMENT (Before Presenting Conclusions)

**Trigger condition:** About to summarize experiment results, recommend next steps, or evaluate an idea for the user

**Execution steps:**
1. **Steel-man opposition:** What is the strongest argument against this conclusion?
2. **Quantify uncertainty:** Would the conclusion change with more data?
3. **Flag overconfidence:** Are we treating a preliminary result as definitive?
4. **Check cherry-picking:** Are we only showing the best numbers while hiding the worst?
5. Present both optimistic and pessimistic interpretations

---

## Checkpoint 5: IDEA ADVERSARIAL REFINEMENT (After Idea Generation)

**Trigger condition:** idea-gen.generate is complete and a top idea has been selected

**Execution steps:**
1. Use Review Dispatch to select the review backend (the external reviewer CLI or sonnet agent)
2. Send the idea to the reviewer, requesting evaluation on 4 dimensions:
   - **HOOK (1-5):** Can a single sentence convince the reviewer?
   - **DIFFERENTIATION (1-5):** Is the distinction from the strongest competitor clear enough?
   - **FEASIBILITY (1-5):** Is the core hypothesis testable? Is a minimal experiment viable?
   - **WEAKNESS:** The biggest weakness — how would a reviewer attack it?
3. Based on review results:
   - **STRONG (avg ≥ 4):** Proceed directly to experiments
   - **NEEDS_WORK (avg 2.5-4):** Claude modifies the idea based on feedback → re-review
   - **WEAK (avg < 2.5):** Switch to a different idea or re-generate
4. Maximum 3 iterations; **record `refinement_rounds_used` in PIPELINE_STATE.json** ([O4] fix)
5. Write final version to `~/research-ideas/{idea_dir}/idea_final.md`
6. **Also write the refined idea back to the ideas table in papers.db** (update method_summary, motivation, etc.) ([G3] fix)

---

## Checkpoint 6: EXPERIMENT MONITORING (During Experiment Execution) — [M2] fix

**Trigger condition:** Experiment has been launched and is in monitoring phase

**Monitoring strategy (replaces flat 5min polling) ([O2] fix):**
- First 10 minutes: check every 2 minutes (catch early crashes)
- 10-60 minutes: check every 10 minutes
- After 60 minutes: check every 30 minutes
- After 24 hours: auto-terminate

**Each check covers:**
1. **Process alive:** `ps -p <PID> -o state=` — if process does not exist or is zombie → FAIL
2. **GPU utilization:** `nvidia-smi --query-gpu=utilization.gpu --format=csv` — if target GPU utilization is < 5% for 10 consecutive minutes while process is alive → suspected hang, issue warning
   - **Exception: hybrid-architecture models** (attention + mamba/deltanet, e.g., Qwen3.5) naturally have lower GPU util (~30%) because mamba layers do not use CUDA compute. For such models, use memory usage + log activity as health indicators instead of GPU util.
3. **Log health check:** Read the last 20 lines of the log file
   - Check for `NaN`, `inf`, `CUDA error`, `OOM`, `RuntimeError`, `Traceback`
   - If found → immediate FAIL, do not wait for timeout
4. **metrics.json freshness:** `stat -c %Y metrics.json` — if metrics.json has not been updated for >30 minutes while process is still running → warning (possible hang)
5. **Performance check (after first iteration):** Parse `s/it` or `it/s` from logs, estimate total runtime
   - If estimated time > reasonable threshold → invoke `exp-engineer profile` + `optimize`
   - After optimization completes and verify passes → kill old process, restart with optimized code
   - Refer to the runtime threshold table in exp-engineer SKILL.md
6. **Results:**
   - HEALTHY: process active, GPU in use, logs normal
   - SLOW: speed below expectation → trigger exp-engineer optimization
   - WARNING: suspected hang (GPU idle or metrics stale) → check once more to confirm
   - FAIL: process dead / NaN / OOM / Error → generate failure_report.json, trigger Gate2 ABANDON

---

## Gate 1: IDEA SELECTION (Replaces Human Checkpoint 1)

**Trigger condition:** idea-gen has generated multiple ideas and one must be selected to enter the experiment phase

**Autonomous decision logic ([M1] fix — quantified feasibility):**
1. First check CP2 cached results ([O1] fix); execute CP2 only if no cache exists
2. Compute composite score: `score = 0.4 * novelty + 0.3 * feasibility + 0.3 * impact`
   - **novelty** (0-1): novelty score from CP2. If `confidence: "LOW"` (SerpAPI unavailable), cap at 0.6
   - **feasibility** (0-1): **compute-based calculation** ([M1] fix):
     - Estimate required GPU-hours for the idea (refer to references/compute_heuristics.md)
     - `feasibility = clamp(1.0 - estimated_hours / 100, 0, 1)`
     - Example: estimated 30h → feasibility=0.7; estimated 120h → feasibility=0 (over budget)
   - **impact** (0-1): proxy metric based on knowledge base data:
     - Paper growth rate in the problem domain over the last 2 years (trend_signals)
     - Average citations of top papers in the domain
     - `impact = normalize(growth_rate * avg_citations)`
3. **Decision rules:**
   - Select the highest-scoring idea (if score >0.5)
   - If all ideas score <0.5 → output "NO VIABLE IDEA", suggest re-generating
   - If the top-2 score gap is <0.1 → **first execute CP3 (Resource Audit) to check if there are enough GPUs for parallel runs** ([M6] fix):
     - Two pilots combined budget ≤30% of total budget (≤72 GPU-h) → pilot both simultaneously
     - Otherwise → sequentially pilot the higher-scoring one
4. Write decision to PIPELINE_STATE.json:
   ```json
   {"gate": "idea_selection", "decision": "proceed",
    "selected": "idea_001", "score": 0.72,
    "novelty": 0.8, "feasibility": 0.7, "impact": 0.6,
    "novelty_confidence": "HIGH",
    "reason": "..."}
   ```

---

## Gate 2: EXPERIMENT EVALUATION (Replaces Human Checkpoint 2)

**Trigger condition:** Pilot or formal experiment is complete; need to decide proceed/revise/abandon

**Autonomous decision logic:**
1. **Validate metrics.json schema** ([G1] fix):
   ```
   Required fields:
   - primary_metric: {name, value, baseline_value}
   - statistical_test: {test_name, p_value}  (if single run only, mark p_value as null)
   - experiment_id, idea_id
   Missing required fields → mark as INCOMPLETE, do not make PROCEED decision, request supplementation
   ```
2. First execute CP4 (Honest Assessment)
3. **Read `revise_count` from PIPELINE_STATE.json** ([C4] fix)
4. **Decision rules:**
   - **PROCEED** conditions (all must be met):
     - Primary metric outperforms baseline with p < 0.05 (if p_value is null, require consistent trend across at least 3 runs)
     - Effect is within 50%+ of competitor range, or has clear advantage on another dimension (e.g., 10x+ lower inference cost)
     - Has a clear differentiating angle such as efficiency / simplicity / generalization
   - **REVISE** conditions (any one triggers):
     - Primary metric outperforms baseline but not significantly (p > 0.05)
     - Effect exists but is insufficient to support a paper (improvement < 30% of competitor's)
     - **`revise_count` < 2** ([C4] fix) → allow revise
     - → Generate failure_report.json with specific revision suggestions
     - → `revise_count += 1`, write to PIPELINE_STATE.json
   - **ABANDON** conditions (any one triggers):
     - Primary metric does not outperform baseline (improvement ≤ 0)
     - Core hypothesis is refuted by experimental data
     - **`revise_count` >= 2** ([C4] fix) → revise quota exhausted, force abandon
     - → Generate postmortem.json recording failure reasons and lessons learned
5. Write decision to PIPELINE_STATE.json

---

## Gate 3: REVIEW FEEDBACK TRIAGE (Review Feedback Classification) — [M5] fix

**Trigger condition:** paper-write.improve has received review feedback

**Classification logic:**
1. Parse ACTION_ITEMS and MISSING_EXPERIMENTS from REVIEW_REPORT.md
2. Classify into two types:
   - **Type A (writing fixes):** Can be completed within paper-write (reframing, overclaim correction, figure/table improvements, language polishing)
   - **Type B (experiment fixes):** Requires going back to exp-run for additional experiments (missing baseline, missing ablation, insufficient statistical significance requiring multiple runs)
3. If Type B items exist:
   - Set `needs_reexperiment: true` and `missing_experiments: [...]` in PIPELINE_STATE.json
   - Pipeline falls back to Stage 2 to run supplementary experiments
   - After experiments complete → update metrics.json → return to Stage 3 to update the paper
4. If only Type A items:
   - Fix within paper-write in priority order

---

## Review Dispatch: Automatic Review Backend Selection

**Trigger condition:** paper-write's `review` or `improve` subcommand requires external review, or CP5 Idea Refinement needs review

**Selection logic:**
1. **Check external reviewer CLI availability:**
   ```bash
   # Check if the external reviewer CLI is installed
   which "$REVIEWER_CLI" 2>/dev/null
   # Check for active tmux sessions
   tmux list-sessions 2>/dev/null | grep -i "$REVIEWER_CLI"
   # Attempt external reviewer CLI health check
   timeout 10 "$REVIEWER_CLI" --version 2>/dev/null   # if your network needs a proxy, set $HTTPS_PROXY in the environment
   ```

2. **Decision branches:**

   **Path A: External reviewer CLI available** → Drive it via tmux interaction
   - Follow the external reviewer CLI's double-Enter protocol
   - Send long text via batch file method
   - **Each review round prompt must include all previous rounds' REVIEW_REPORT** (the external reviewer CLI's tmux has no stateful memory) ([C5] fix)
   - Monitor completion status

   **Path B: External reviewer CLI unavailable** → Fall back to Sonnet Agent
   - Launch independent review agent using `Agent` tool with `model: "sonnet"`
   - Use review prompt template (see below)
   - Advantage: no external dependencies, no quota limits
   - Disadvantage: same Anthropic model family, slightly less review perspective diversity

3. **Sonnet Review Agent Template:**
   ```
   You are an adversarial reviewer for a top ML venue ({venue}).
   Review this paper with the rigor of an Area Chair at the target venue. Match style to: NeurIPS/ICML/ICLR (ML), CVPR/ICCV (CV), ACL/EMNLP (NLP), SIGMOD/VLDB/ICDE (DB), SIGKDD (DM), SIGIR/WWW (IR/Web), ACM MM (MM), AAAI/IJCAI (general AI).

   Score each dimension (1-10):
   1. Novelty: Is this actually new?
   2. Experiments: Are claims supported by evidence?
   3. Clarity: Is the writing clear and well-organized?
   4. Claims-Evidence Alignment: Does every claim have matching evidence?
   5. Reproducibility: Could someone replicate this?
   6. Related Work: Are comparisons fair and complete?

   For each dimension:
   - Give specific line/section references
   - Classify issues as CRITICAL / MAJOR / MINOR
   - Suggest concrete fixes

   Also classify each action item:
   - TYPE_A (writing fix): can be fixed without new experiments
   - TYPE_B (experiment fix): requires running additional experiments

   Output format:
   ## Overall Score: X/10
   ## Verdict: STRONG_REJECT / WEAK_REJECT / BORDERLINE / WEAK_ACCEPT / ACCEPT
   ## Detailed Review
   [dimension-by-dimension breakdown]
   ## Required Changes
   [prioritized list with TYPE_A/TYPE_B labels]
   ## Missing Experiments
   [list of experiments needed, or "None"]
   ```

4. **Record which backend was used:**
   ```json
   {"reviewer": "external-cli" | "sonnet-agent", "reason": "external reviewer CLI unavailable: no tmux session"}
   ```

---

## metrics.json Standard Schema — [G1] fix

All experiment scripts must output a metrics.json conforming to the following schema. Gate2 validates schema completeness before making decisions.

```json
{
  "experiment_id": "pilot-003",
  "idea_id": "example-idea",
  "timestamp": "2025-01-15T15:30:00",
  "primary_metric": {
    "name": "top1_accuracy",
    "value": 0.312,
    "baseline_value": 0.112,
    "improvement": 0.200,
    "higher_is_better": true
  },
  "secondary_metrics": [
    {"name": "top8_recall", "value": 0.67, "baseline_value": 0.45}
  ],
  "statistical_test": {
    "test_name": "paired_ttest",
    "p_value": 0.003,
    "n_samples": 240,
    "note": "null if single run; pipeline will request multiple runs"
  },
  "ablations": [
    {"name": "no_layer_embedding", "primary_metric_value": 0.25}
  ],
  "compute_cost": {
    "gpu_hours": 2.5,
    "gpu_type": "datacenter-80gb"
  },
  "competitor_comparison": {
    "name": "MethodX",
    "their_improvement": 0.15,
    "our_improvement": 0.20,
    "our_advantage": "100x lower inference cost"
  }
}
```

**CP1 checks during code audit:** Does the script output a metrics.json in the above format? Missing `primary_metric` or `statistical_test` → MEDIUM warning.

---

## Unified Threshold Definitions — [M4/X3] fix

The following thresholds are defined exclusively in supervisor; all other skills reference this section:

| Threshold | Value | Meaning |
|-----------|-------|---------|
| `REVIEW_STOP_SCORE` | 7 | Review score ≥7 → stop improve loop |
| `REVIEW_ABORT_SCORE` | 4 | Review score <4 → terminate pipeline, wait for user review |
| `GATE1_VIABLE_THRESHOLD` | 0.5 | Idea composite score ≥0.5 to enter experiment phase |
| `MAX_REVISE_COUNT` | 2 | Maximum 2 revisions per idea |
| `MAX_REFINEMENT_ROUNDS` | 3 | Maximum 3 rounds of idea adversarial refinement |
| `MAX_REVIEW_ROUNDS` | 3 | Maximum 3 rounds of paper review improvement |
| `EXPERIMENT_TIMEOUT_HOURS` | 24 | Maximum runtime for a single experiment |
| `IDEA_GPU_BUDGET_HOURS` | 100 | Maximum GPU budget per idea |
| `TOTAL_GPU_BUDGET_HOURS` | 240 | Total GPU budget |
| `DUAL_PILOT_BUDGET_CAP` | 0.3 | Dual-pilot must not exceed 30% of total budget |

---

## Sub-stage Checkpointing — [G2] fix

To prevent progress loss when the context window is exhausted, write to the `sub_stage` field in PIPELINE_STATE.json at the following nodes:

```
Stage 1: idea_crawled → ideas_generated → novelty_verified → idea_selected → idea_refined
Stage 2: code_audited → pilot_started → pilot_monitoring → pilot_evaluated → formal_started → formal_done → ablation_done
Stage 3: outline_done → claims_matrix_done → method_drafted → experiments_drafted → intro_drafted → related_drafted → abstract_drafted → conclusion_drafted → compiled
Stage 4: review_round_0 → improve_round_1 → review_round_1 → ...
```

On resume, read `sub_stage` to continue from the exact breakpoint, avoiding re-execution of completed sub-steps.

---

## Anti-Patterns Checklist

| Anti-Pattern | Example | Corresponding Checkpoint |
|-------------|---------|--------------------------|
| Running code without review | `dtype` silently ignored | CP1 |
| Hasty novelty claims | "No one has done this" but only checked 4 papers | CP2 |
| Wasting idle GPUs | cuda:0 sitting idle | CP3 |
| Overly optimistic presentation | Hiding data where competitor outperforms us | CP4 |
| Confirmation bias | Citing only supporting evidence | CP4 |
| False positive novelty | Ignoring strongest competitor to protect novelty claim | CP2 |
| Silent experiment failure | NaN loss running for 24h before discovery | CP6 |
| Redundant searches | verify + CP2 double SerpAPI calls | CP2 (caching) |

---

## SerpAPI Configuration

- Endpoint: `https://serpapi.com/search.json?engine=google_scholar`
- Key: user-provided (ask user at runtime, or read from environment variable)
- **Hard limit: ≤100 total calls per day, ≤5 queries per novelty audit**

---

## Integration Points with Other Skills

```
idea-gen.generate ──→ verify (cached) ──→ [Gate1 reuses cache] ──→ [CP5 Refinement] ──→ write back to DB
exp-run.pilot     ──→ [CP1 single audit entry point] + [CP3] ──→ launch ──→ [CP6 monitoring]
                                                                    │
                                                              speed < threshold?
                                                                    ▼ YES
                                                          exp-engineer.profile
                                                                    │
                                                          exp-engineer.optimize
                                                                    │
                                                          exp-engineer.verify ──→ restart experiment
exp-run.evaluate  ──→ [schema validation] ──→ [CP4] ──→ [Gate2] ──→ proceed/revise/abandon
paper-write.draft ──→ [CP4] ──→ honest claims-matrix
paper-write.review──→ [Review Dispatch] ──→ external reviewer CLI or sonnet-agent
paper-write.improve → [Gate3 Triage] ──→ Type A (writing fix) or Type B (fall back to exp-run)
```
