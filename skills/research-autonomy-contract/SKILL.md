---
name: research-autonomy-contract
description: >-
  Negotiates and enforces an explicit autonomy contract between a human
  researcher and an AI research pipeline. Classifies every proposed
  action into one of three lanes (auto-proceed, log-and-proceed,
  block-and-ask) using project-specific thresholds, defines escalation
  triggers and stop-loss rules, and emits a machine-readable contract
  that orchestrator skills consult to decide when to interrupt the
  human. Use at project kickoff, when the AI keeps over-asking or
  under-asking, after a budget or safety incident, or when the user
  says 'set up autonomy rules', 'stop asking me about everything', or
  'why did you run that without asking'.
license: CC-BY-4.0
---

# Research Autonomy Contract

## Problem

Human-AI research collaboration fails at the permission boundary, in
one of two symmetric ways. If the AI asks before every action, the
human becomes a serial bottleneck and the pipeline idles waiting for
approvals that were never in doubt. If the AI asks before nothing,
GPU hours burn on experiment designs nobody reviewed, and irreversible
mistakes (deleted artifacts, premature external submissions) happen
silently. Both failures come from the same root cause: the boundary
is implicit, so it gets re-litigated per action, inconsistently.

This skill makes the boundary explicit. It produces a signed-off
contract that pre-decides, from measurable properties of an action,
whether the AI proceeds, proceeds-with-notice, or stops. The house
rule throughout: **lane assignment is computed from thresholds, never
judged ad hoc, and every autonomous action leaves a ledger entry.**

## The three lanes

Every action the pipeline is about to take is classified into exactly
one lane before execution. Classification uses four computable
properties:

- **Reversibility** — can the action be undone from existing artifacts?
- **Cost** — estimated spend (GPU-hours, API dollars, wall-clock days).
- **Scope** — does it stay inside the currently approved hypothesis set?
- **Sensitivity** — does it touch licensing, ethics, external parties,
  or published claims?

### Lane GREEN — auto-proceed

Reversible, cheap, and in-scope. The AI executes immediately and
writes a ledger entry; no human notification beyond the regular
heartbeat.

Typical members: analysis of already-collected data; plots and tables
regenerated from existing runs; documentation and code edits under
version control; offline computation below the cheap-cost threshold;
literature lookups; unit tests and dry runs.

### Lane YELLOW — log-and-proceed

Costly but preauthorized: the action passed the project's design gate
and its estimated cost fits inside the remaining preapproved budget.
The AI executes, but first posts a **structured notice** so the human
can veto asynchronously — the pipeline does not wait for a reply.

A notice must contain all four fields:

1. **What** — the exact command/config, with the run identifier.
2. **Why** — the hypothesis or ledger entry this run serves.
3. **Budget** — estimated cost, and cumulative budget consumed after
   this run (absolute and percent).
4. **Abort handle** — the one command or action that kills the run and
   cleans up, so a veto costs the human ten seconds, not a debugging
   session.

Typical members: training or evaluation runs under the per-run
GPU-hour cap whose design was already gated; sweeps whose total cost
fits the per-hypothesis budget; large downloads of already-cleared
datasets.

### Lane RED — block-and-ask

Irreversible, expensive beyond preauthorization, scope-changing, or
sensitive. The AI stops and presents a **decision brief**, then does
nothing on this thread until the human decides.

A decision brief must contain:

1. **Options** — two to four concrete choices, always including
   "do nothing".
2. **Evidence** — ledger entries and results bearing on the choice,
   cited by ID, not re-summarized from memory.
3. **Recommendation** — exactly one option, with the single strongest
   reason and the single strongest reason against.
4. **Deadline semantics** — what happens if the human does not answer
   (default: the thread stays parked; other threads continue).

Mandatory RED members, regardless of thresholds: adopting a dataset
with unresolved license terms; any external submission or publication
action; deleting or overwriting artifacts not reproducible from the
ledger; spending beyond the remaining preapproved budget; changing
the hypothesis set; and stating a conclusion that would overturn a
previously published or previously reported claim.

## Escalation triggers

Triggers force a **lane upgrade** (GREEN→YELLOW, YELLOW→RED) for the
affected thread. They are evaluated mechanically after every action:

| ID | Trigger | Effect |
|----|---------|--------|
| E1 | 2 consecutive failures on the same pipeline step | upgrade one lane |
| E2 | New result contradicts an existing ledger entry | upgrade to RED |
| E3 | Any control or sanity check fails | upgrade to RED |
| E4 | Cumulative budget reaches 80% of preapproval | all YELLOW → RED |

Upgrades are sticky per thread until the human clears them. A cleared
trigger is itself a ledger entry ("E2 cleared: contradiction traced to
seed handling, entry L-041 corrected").

## Stop-loss rules

Stop-losses bound how much can be spent chasing one idea before a
mandatory human review, independent of lane:

- **max_retries** — hard cap on automated retries of the same step
  (default 3). Exceeding it parks the thread RED.
- **max_gpu_hours_per_hypothesis** — cumulative compute cap per
  hypothesis (set per project). Reaching it forces a review with a
  keep/kill recommendation before another GPU-hour is spent.
- **max_wall_days_without_signal** — if a hypothesis produces no
  decision-relevant result for N days (default 5), schedule a review
  at the next heartbeat.

Stop-loss is not punishment; it is the mechanism that converts sunk
cost into an explicit keep/kill decision.

## Cadence: what the human hears, and when

The contract fixes a reporting rhythm so silence is informative
(silence = GREEN work proceeding normally).

**Daily heartbeat** (one message):
- One-line status: `<phase> | <runs active> | <budget used %> | <blocked count>`
- Deltas only: what changed since the last heartbeat (new results,
  lane upgrades, notices posted).
- Blocked items: every RED brief awaiting a decision, oldest first.

**Weekly review** (one page):
- Budget curve vs. plan; per-hypothesis spend.
- Hypotheses opened / killed / promoted, each with its ledger citation.
- Contract friction report: actions that felt misclassified, with a
  proposed threshold change. The contract is renegotiated here and
  only here — never silently mid-week.

## Session hygiene

The pipeline must survive a dead session. Two rules:

1. **The ledger is the memory.** Every autonomous action, notice,
   brief, trigger, and clearance is an append-only ledger entry with
   an ID, timestamp, lane, and cost. Nothing decision-relevant lives
   only in chat history.
2. **Handoff note on every stop.** When a session ends (planned or
   not), the last artifact written is a handoff note: current lane
   state per thread, active abort handles, pending RED briefs, and
   the next intended action. A fresh session must be able to resume
   from the ledger plus the handoff note alone, with zero questions
   whose answers already exist.

## Procedure

1. **Elicit thresholds.** Ask the human for: cheap-cost ceiling
   (GREEN), per-run and per-hypothesis GPU-hour caps (YELLOW),
   total preapproved budget, and any project-specific mandatory-RED
   items (e.g., touching a shared production dataset).
2. **Fill the contract table.** Instantiate the lane definitions with
   those numbers (template below). Walk the human through three
   sample actions and confirm each lands in the intended lane.
3. **Emit the JSON spec.** Write the machine-readable contract to the
   project root as `autonomy-contract.json` (schema below) so that
   conductor/orchestrator skills can compute lane assignments and
   interruption decisions without re-asking.
4. **Enforce.** During operation: classify before acting, post notices
   and briefs in the formats above, evaluate triggers after every
   action, and honor stop-losses. When in doubt between two lanes,
   take the more restrictive one and flag the ambiguity in the weekly
   friction report.

## Output artifacts

### 1. Filled contract table

| Lane | Criteria (all must hold) | Project thresholds | AI behavior |
|------|--------------------------|--------------------|-------------|
| GREEN | reversible AND cheap AND in-scope AND non-sensitive | cost < ___ | act, log |
| YELLOW | design-gated AND within budget | per-run < ___ GPU-h; cumulative < ___ | act, log, notice with abort handle |
| RED | any: irreversible, over budget, scope change, sensitive | — | stop, decision brief |

### 2. Machine-readable spec

```json
{
  "lanes": {
    "green":  {"max_cost_gpu_hours": 0.5, "requires": ["reversible", "in_scope"]},
    "yellow": {"max_run_gpu_hours": 24, "requires": ["design_gated", "within_budget"],
               "notice_fields": ["what", "why", "budget", "abort_handle"]},
    "red":    {"mandatory": ["license_unresolved", "external_submission",
               "artifact_deletion", "over_budget", "scope_change",
               "overturns_prior_claim"],
               "brief_fields": ["options", "evidence", "recommendation",
               "deadline_semantics"]}
  },
  "escalation_triggers": [
    {"id": "E1", "condition": "consecutive_failures >= 2", "effect": "upgrade_one_lane"},
    {"id": "E2", "condition": "result_contradicts_ledger", "effect": "upgrade_to_red"},
    {"id": "E3", "condition": "control_check_failed", "effect": "upgrade_to_red"},
    {"id": "E4", "condition": "budget_consumed >= 0.8", "effect": "yellow_to_red"}
  ],
  "stop_loss": {
    "max_retries": 3,
    "max_gpu_hours_per_hypothesis": 200,
    "max_wall_days_without_signal": 5
  },
  "cadence": {
    "heartbeat": "daily",
    "heartbeat_fields": ["status_line", "deltas", "blocked_items"],
    "review": "weekly",
    "renegotiation": "weekly_review_only"
  }
}
```

Downstream orchestrators read this file to answer one question
mechanically: *is this the moment to interrupt the human?* If the
contract says no, they must not.

## Acknowledgments

The idea that a human-in-the-loop workflow skill should govern the
day-to-day division of labor between researcher and AI pipeline was
inspired by HKUSTDial's Supervisor-Skills project. This autonomy
contract framework — the lane model, triggers, stop-losses, cadence,
and JSON contract — is an independent redesign written from scratch.
