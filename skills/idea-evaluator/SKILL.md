---
name: idea-evaluator
description: >-
  Kill-Cheap Triage for research ideas: instead of scoring how good an
  idea sounds, it measures how cheaply the idea can be killed. Designs
  the single cheapest decisive experiment, classifies the claim type,
  converts novelty into falsifiable literature-search statements, and
  audits whether the evidence budget can actually detect the claimed
  effect. Emits GREENLIGHT / RESHAPE / KILL plus a machine-readable
  JSON block for downstream pipeline gates. Use when triaging a draft
  research idea, deciding whether to fund an experiment, or comparing
  candidate directions before any code is written.
license: CC-BY-4.0
---

# Idea Evaluator — Kill-Cheap Triage

## Philosophy

Most idea reviews ask "how promising is this?" and answer with adjectives.
This skill asks a colder question: **how cheaply can this idea be proven
wrong?** An idea that can be killed for 4 GPU-hours is a good bet even if
it probably fails, because the failure is cheap and informative. An idea
that cannot be killed for less than three months of work is a liability
even if it sounds brilliant, because you will not learn you were wrong
until the budget is gone.

Operating rules, in priority order:

1. **Falsifiability first.** Every claim in the idea must map to an
   observation that could contradict it. A claim no experiment can
   contradict is not evaluated further — it is flagged.
2. **Evidence over rhetoric.** The triage never cites the idea's framing,
   ambition, or timeliness as evidence. Only measurable consequences count.
3. **Verdicts are computed, not felt.** The verdict follows mechanically
   from the flag table in "Verdict computation" below. If the flags say
   KILL, the verdict is KILL, however appealing the idea reads.
4. **Findings must be actionable.** "Novelty is unclear" is banned output.
   The correct output is a literature query string that resolves the
   question one way or the other.

## When to use

- A draft idea document exists and someone must decide whether to spend
  compute, annotation money, or weeks of a person's time on it.
- An automated pipeline needs a structured go/no-go signal before its
  experiment stage (this skill's JSON block is designed to feed a gate).
- Two or more candidate ideas compete for one budget; run the triage on
  each and compare kill costs and power checks side by side.
- An idea has been running for a while with ambiguous results and you
  suspect it was never falsifiable to begin with.

## When NOT to use

- Brainstorming from scratch — triage presupposes a stated claim.
- Reviewing a finished manuscript — the experiments already happened;
  use a manuscript-review skill instead.
- Pure engineering tasks with no empirical claim (e.g. "port the
  pipeline to JAX") — there is nothing to falsify.

## Inputs

Required from the caller (ask for anything missing before proceeding):

- **Idea statement** — one paragraph to one page. Must contain at least
  one sentence of the form "we claim that X".
- **Budget envelope** — available GPU-hours, API-call budget, annotation
  hours, and calendar time. Rough numbers are fine; "unknown" is not.
- **House rule overrides** (optional) — see "Configurable house rules".

## The four axes

Evaluate every idea on all four axes, in this order. Each axis produces
zero or more flags; flags drive the verdict.

### Axis K — Killability

**Question: does a decisive first experiment exist, and what does it cost?**

Design **THE single cheapest killing experiment**: the smallest procedure
whose outcome, if it lands one way, ends the idea. Specify exactly three
things:

- `design` — what is run and what is measured. Concrete enough that a
  competent engineer could start today without asking questions.
- `kill_condition` — the specific observable result that kills the idea.
  A number with a threshold, not a mood ("if the ablated variant matches
  the full method within 0.5 points on the held-out split, the proposed
  mechanism contributes nothing and the idea is dead").
- `cost` — estimated GPU-hours, API calls, and/or annotation hours.

Rules:

- Prefer kill experiments that reuse existing checkpoints, public
  datasets, and cached model outputs. Zero-training kill shots
  (probing an existing model, re-scoring existing predictions) beat
  anything that requires a training run.
- If the cheapest conceivable kill experiment exceeds roughly 20% of the
  total budget envelope, flag `EXPENSIVE-KILL`.
- If no experiment can kill the idea — every outcome can be explained
  away — flag `UNFALSIFIABLE`. This flag is terminal.
- If the idea can only be killed by running the *full* proposed project,
  flag `NO-CHEAP-KILL`.

### Axis C — Claim class

**Question: what kind of claim is this, and does it clear the house floor?**

Classify the idea's central claim into exactly one class (rubric with
boundary cases in `references/claim-classes.md`):

- **method** — "doing X makes metric M better under matched conditions."
- **mechanism** — "phenomenon P happens because of Z" (with or without a
  fix derived from Z).
- **benchmark** — "here is a new task/dataset/protocol that measures
  something existing suites do not."
- **analysis** — "here is a characterization of existing systems, with
  no new method, mechanism-with-fix, or benchmark."

**House rule (configurable, default on):** submissions aimed at top
venues must carry a *method* claim or a *mechanism* claim that includes
a derived fix. A bare *analysis* claim gets flag `CLAIM-BELOW-FLOOR` —
not because analysis is worthless, but because analysis-only papers at
top venues live or die on reviewer taste, which this triage refuses to
bet on. The flag forces an explicit decision rather than a drift into a
weak submission.

If the idea document mixes classes, classify by the claim the abstract
would lead with, and note the secondary claims.

### Axis D — Delta (novelty as an attack surface)

**Question: what literature finding would kill the novelty claim?**

Novelty is not a vibe to be admired; it is a claim to be attacked. Emit
**3–5 concrete literature-search queries** such that: *if any query
returns a paper doing X, the idea is dead as stated.* Each entry pairs a
query string with its dead-if condition:

```
query:   "selective prediction" "confidence calibration" retrieval-augmented
dead_if: any paper applies abstention thresholds to RAG answer heads
         with a comparable gating signal
```

Rules:

- Queries must be runnable verbatim on Google Scholar / Semantic Scholar.
  No placeholders like "search for related work on X".
- Each query attacks a *different* facet of the delta (the mechanism,
  the setting, the metric, the combination).
- If you can already name a paper that satisfies a dead-if condition
  from your own knowledge, do not hide it behind a query — flag
  `NOVELTY-DEAD` and cite the paper. Uncertain memories are flagged
  `NOVELTY-SUSPECT` with the query that would confirm.
- If the delta cannot be phrased as any dead-if statement — i.e. no
  possible prior paper could contradict the novelty claim — that is a
  disguised `UNFALSIFIABLE` and gets the same flag.

The triage itself does not run the searches (it may not have network
access); it hands the queries downstream. A gate that *can* search runs
them before any GREENLIGHT is acted on.

### Axis E — Evidence economics

**Question: can the budget buy enough evidence to detect the claimed effect?**

Work through, with numbers:

1. **Expected effect size.** How big is the claimed improvement or
   difference likely to be, stated in the metric's own units? If the
   idea document does not say, derive a charitable estimate from the
   nearest published comparable and say so.
2. **Achievable n.** Given the budget envelope, how many independent
   evaluation units (test items, seeds, subjects, tasks) can actually
   be afforded?
3. **Minimum detectable effect (MDE).** At the achievable n, what is
   the smallest effect distinguishable from noise? Back-of-envelope is
   fine (binomial standard error for accuracy-type metrics, seed
   variance for training-run comparisons) — but it must be written down.
4. **Power-trap check.** Screen against the known failure patterns in
   `references/power-traps.md` — headline AUROC/accuracy claims built
   on double-digit n, seed-count-of-one training comparisons, test sets
   small enough that one relabeled item moves the headline number, and
   friends. These are claims that collapse at scale.

Flags: `UNDERPOWERED` if expected effect < MDE; `POWER-TRAP` if a
pattern from the reference matches; `BUDGET-SHORTFALL` if reaching the
MDE requires more resources than the envelope contains.

## Verdict computation

Apply the first row that matches. No holistic override is permitted.

| Condition | Verdict |
|---|---|
| `UNFALSIFIABLE` present | **KILL** |
| `NOVELTY-DEAD` present | **KILL** |
| `UNDERPOWERED` or `BUDGET-SHORTFALL` present, and no single change to scope/metric/n repairs it | **KILL** |
| Two or more of: `NO-CHEAP-KILL`, `CLAIM-BELOW-FLOOR`, `POWER-TRAP`, `EXPENSIVE-KILL`, `NOVELTY-SUSPECT` | **KILL** |
| Exactly one binding flag, and one specific change would clear it | **RESHAPE** |
| No flags (or only `NOVELTY-SUSPECT` with queries emitted) | **GREENLIGHT** |

Verdict obligations:

- **GREENLIGHT** is never unconditional: the kill experiment from Axis K
  is the *mandatory first step*, and the novelty queries from Axis D
  must be run before any result is claimed as novel. State both.
- **RESHAPE** must name the *single specific change* that flips the
  verdict — a different metric, a narrower claim, a larger n, a claim
  upgrade from analysis to mechanism-with-fix. "Strengthen the
  evaluation" is not a reshape directive; "replace the 50-item probe
  set with the full 2,000-item public split so the MDE drops below the
  expected 3-point effect" is.
- **KILL** must present the evidence: the flag(s), and for each flag the
  concrete observation or computation that raised it. A KILL that the
  idea's author cannot check for themselves is invalid output.

## Configurable house rules

Callers may override defaults by stating them in the request:

- `claim_floor` — default `method | mechanism-with-fix`. A workshop
  paper or an internal tech report might lower it to `analysis`.
- `kill_budget_fraction` — default `0.20`. The fraction of the total
  envelope above which a kill experiment raises `EXPENSIVE-KILL`.
- `venue_tier` — default `top`. Affects only the claim-floor default.

## Output format

Produce the human-readable triage first (the four axes, each with its
findings and flags, then the verdict with its obligations). End with the
machine-readable block, exactly this schema, fenced as ```json:

```json
{
  "verdict": "GREENLIGHT | RESHAPE | KILL",
  "claim_class": "method | mechanism | benchmark | analysis",
  "kill_experiment": {
    "design": "<what is run and measured>",
    "kill_condition": "<observable result that ends the idea>",
    "cost": "<GPU-hours / API calls / annotation hours>"
  },
  "novelty_queries": [
    {"query": "<verbatim search string>", "dead_if": "<condition>"}
  ],
  "power_check": {
    "expected_effect": "<size, in metric units>",
    "achievable_n": "<number of evaluation units>",
    "mde": "<minimum detectable effect at that n>",
    "passes": true
  },
  "fatal_flags": ["UNFALSIFIABLE", "..."],
  "reshape_directive": "<the single change that flips the verdict, or null>"
}
```

Field rules: `kill_experiment` is required even for KILL verdicts (a
kill experiment that was never needed is still the record of *why* the
idea was killable); `reshape_directive` is non-null iff verdict is
RESHAPE; `fatal_flags` uses only the flag vocabulary defined above;
`novelty_queries` contains 3–5 entries unless `NOVELTY-DEAD` made
searching moot, in which case it contains the single query-equivalent
citation that killed it.

Downstream consumers (a pipeline gate or supervisor step) treat the JSON
block as authoritative: a KILL verdict removes the idea from
consideration regardless of any other scoring signal, and a GREENLIGHT
schedules the kill experiment as the first dispatched job.

## Worked micro-example

Idea: "LLM uncertainty heads predict retrieval failure; claim: gating
retrieval by an uncertainty probe improves open-domain QA accuracy."

- **K**: probe an existing checkpoint's hidden states on 2,000 cached
  QA traces; kill_condition: probe AUROC < 0.65 against retrieval
  failure labels; cost: ~2 GPU-hours (no training run). No flag.
- **C**: method claim (gating improves accuracy). Clears the floor.
- **D**: four queries attacking "uncertainty-gated retrieval",
  "selective retrieval augmentation", "adaptive RAG confidence",
  "when to retrieve LLM" — each with a dead-if. One suspected prior
  hit → `NOVELTY-SUSPECT`.
- **E**: expected effect ~2 points EM; n=2,000 gives MDE ≈ 1.8 points
  (binomial SE at ~50% base rate, two-sided). Passes, narrowly; noted.
- **Verdict**: GREENLIGHT — run the 2 GPU-hour probe first, run the four
  queries before writing a word of related-work positioning.

## References

- `references/claim-classes.md` — the four claim classes, boundary
  cases, and the claim-upgrade paths used by RESHAPE directives.
- `references/power-traps.md` — catalog of evidence-economics failure
  patterns with detection heuristics and repairs.

## Acknowledgments

The *pipeline role* of this skill — an explicit idea-evaluation
checkpoint that feeds a structured verdict into a supervisor gate before
resources are committed — was inspired by HKUSTDial's Supervisor-Skills.
The Kill-Cheap Triage framework itself (killability, claim class, delta
as attack surface, evidence economics, and the computed verdict table)
is an independent redesign and shares no scoring dimensions, taxonomy,
or text with that project.
