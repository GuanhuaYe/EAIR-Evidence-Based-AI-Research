---
name: intro-drafter
description: >-
  Plans a paper Introduction as a pre-emptive rebuttal. From a claim
  summary or claim graph it enumerates the reviewer objections most
  likely to fire against this claim type, ranks them by likelihood and
  lethality, and builds an adaptive 5-7 paragraph plan in which every
  paragraph neutralizes at least one ranked objection before the
  reviewer can form it. Enforces evidence anchors on every
  contribution sentence, a first-100-words rule, and a claim-strength
  verb ladder. Emits an objection-coverage table and a structured JSON
  outline for a downstream Writer agent. Use when asked to plan,
  outline, or restructure an Introduction, or when a draft Intro keeps
  drawing the same reviewer complaints.
license: CC-BY-4.0
---

# Objection-Driven Introduction Drafter

## Premise

Reviewers do not read an Introduction to learn what you did. They read
it while silently drafting reasons to reject you. By the end of page
two, most reviewers have already formed two or three objections; the
rest of the paper is read as evidence for or against those objections.

Therefore an Introduction is not a story — it is a pre-emptive
rebuttal. The unit of planning is not "what do I want to say" but
"what will the reviewer object to, and where do I kill that objection
before it hardens." A paragraph that neutralizes no predictable
objection is decoration and competes for space with paragraphs that do.

This skill turns a paper's claims into (1) a ranked objection
forecast, (2) an adaptive paragraph plan where each paragraph is
assigned objections to neutralize, and (3) machine-checkable coverage
flags. The output is an outline spec, not prose; a Writer agent (or
the author) turns it into text.

## When to use

- The paper's claims are stable and Introduction planning is next.
- A drafted Introduction keeps attracting the same reviewer complaint
  ("incremental", "unfair comparison", "niche") and needs restructuring.
- Rebuttal season revealed objections the Introduction should have
  pre-empted; the camera-ready or resubmission Intro needs a redesign.
- The user asks to "plan the intro", "outline the introduction",
  "why does this intro feel weak", or "make the intro reviewer-proof".

## When NOT to use

- The core claims are still moving. Objection forecasting against
  unstable claims produces stale plans; finish claim triage first.
- The user wants sentence-level polish of an Introduction whose
  structure is already sound. That is a line-editing task.
- The document is not a reviewed artifact (blog post, tech report
  with no adversarial reader). The objection model does not apply.

## Inputs

Accepted in descending order of preference:

1. **Claim graph**: a list of claims, each with type
   (method / problem / measurement / resource / theory), the evidence
   that supports it, and where that evidence lives in the paper.
2. **Claim summary**: 3-6 sentences of "we claim X, supported by Y".
3. **Draft Introduction**: reverse-engineer the claims from it first,
   confirm them with the user, then proceed as if given (2).

Also collect: target venue (or venue class), and whether the paper's
central claim is primarily a method, a problem formulation, a
measurement/analysis result, a dataset/tool resource, or a theorem.
The claim type selects the objection catalogue section.

## Procedure

### Step 1 — Forecast objections

See `references/objection-catalogue.md` for the catalogue of
predictable objections by claim type, with trigger conditions and
neutralization patterns.

From the claim type and claim content, enumerate the objections most
likely to fire. The core catalogue:

- **"Incremental"** — delta over nearest prior work looks like tuning.
- **"Unfair baselines"** — baselines are old, weakened, or mis-configured.
- **"Doesn't scale"** — evidence lives at toy sizes only.
- **"Problem is niche"** — reviewer cannot see who needs this.
- **"Correlation, not mechanism"** — result shown, cause not isolated.
- **"Benchmark saturated"** — gains on a benchmark nobody trusts anymore.
- **"Why now"** — nothing explains why this became possible or urgent.
- **"Ill-posed / already solved"** — the problem statement itself is contested.
- **"Cherry-picked"** — evidence pattern suggests selective reporting.
- **"Overclaimed"** — verbs outrun evidence (see Step 4 ladder).

Extend beyond the catalogue when the claim graph suggests a bespoke
objection (e.g. a known negative result in this subfield).

Score each objection on two axes, each on {1, 2, 3}:

- **Likelihood** — how probable a typical reviewer at this venue
  raises it, given the claim type and evidence profile.
- **Lethality** — if raised and unanswered, does it sink the paper
  (3), cost a point (2), or merely cost goodwill (1)?

Rank by likelihood × lethality. Keep every objection with score >= 4
on the active list; note the rest as "monitored". State the score
rationale in one clause each — scores without rationale are not
auditable.

### Step 2 — Build the paragraph plan

Construct an adaptive plan of 5-7 paragraphs. The count is an output
of the objection list, not an input:

- Method-claim papers at systems venues usually land at 6.
- Measurement/analysis papers often need 7 (mechanism objections take
  a dedicated paragraph).
- Resource papers can be tight at 5.
- If two lethal objections cannot be neutralized in one paragraph
  each without crowding, split; if two are neutralized by the same
  move, merge. Never pad to reach a count.

Rules for the plan:

1. **Assignment rule.** Every paragraph is assigned at least one
   ranked objection it neutralizes, except at most one paragraph that
   may be pure setup (typically the opener). A paragraph with no
   assigned objection and no setup role gets cut.
2. **Ordering rule.** Neutralize an objection *before* the reviewer
   would naturally form it. "Incremental" forms when the reader first
   hears the idea, so the delta-over-prior-work move must land in the
   same or preceding paragraph as the idea reveal. "Doesn't scale"
   forms at the results preview, so the scale evidence anchor belongs
   there, not three paragraphs later.
3. **One-job rule.** Each paragraph gets one purpose sentence. If the
   purpose needs "and", split the paragraph.

For each paragraph record: `purpose` (one sentence),
`objection_neutralized` (ids from the ranked list, or `"none:setup"`),
`writing_points` (2-5 actionable bullets derived from the inputs),
`evidence_anchors` (see Step 3).

### Step 3 — Attach evidence anchors

An **evidence anchor** is a concrete pointer into the paper: a section
number, table number, figure number, or theorem number
(`"Sec. 5.2"`, `"Tab. 3"`, `"Fig. 4"`, `"Thm. 1"`).

- Every contribution sentence in the plan MUST name its anchor. A
  contribution without an anchor is flagged `MISSING_ANCHOR` (MAJOR).
- Every neutralization of a lethality-3 objection must cite at least
  one anchor — a lethal objection cannot be talked away, only shown
  away. Missing: `UNANCHORED_NEUTRALIZATION` (CRITICAL).
- If section/table numbering does not exist yet, use symbolic anchors
  (`"Sec. <ablation>"`) and flag them `ANCHOR_UNRESOLVED` (MINOR) so
  the Writer agent resolves them at draft time.

### Step 4 — Apply the claim-strength ladder

Verbs are promises. For each claim that surfaces in the plan, assign
the strongest rung its evidence licenses:

| Rung | Verb | Licensed by |
|---|---|---|
| 4 | we prove | a proof in the paper |
| 3 | we show / we demonstrate | direct experimental or constructive evidence, with controls |
| 2 | we find evidence that | consistent observational results, mechanism not isolated |
| 1 | we hypothesize / we conjecture | plausibility argument only |

Any writing point whose verb sits above its licensed rung is flagged
`OVERCLAIMED_VERB` (MAJOR) — this is exactly the pre-condition for
the "overclaimed" and "correlation, not mechanism" objections firing.
Downgrading the verb is always an acceptable fix; upgrading the
evidence is the better one.

### Step 5 — Enforce the first-100-words rule

The first ~100 words of the Introduction must state (a) the object of
study and (b) the tension — the specific way the current state of
affairs is unsatisfactory. No throat-clearing: no "In recent years,
X has attracted increasing attention", no survey-of-the-field opener,
no three-sentence definition cascade before the tension appears.

Check: the opener paragraph's writing points must contain both an
object-of-study point and a tension point, and neither may be
preceded by more than one scene-setting point. Violation:
`SLOW_OPEN` (MAJOR).

### Step 6 — Compute the coverage table and flags

Build the objection-coverage table: one row per ranked objection,
columns {objection, likelihood, lethality, score, neutralized_in
(paragraph ids), anchors_used, status}.

Status and flags are computed, not judged:

- Objection with score >= 4 and empty `neutralized_in`, lethality 3
  → `UNCOVERED_LETHAL` (CRITICAL).
- Objection with score >= 4 and empty `neutralized_in`, lethality < 3
  → `UNCOVERED` (MAJOR).
- Paragraph with `objection_neutralized = none` beyond the one
  allowed setup paragraph → `DEAD_PARAGRAPH` (MAJOR).
- Plus the flags from Steps 3-5.

The outline is `ready_for_writer` only if there are zero CRITICAL
flags. Never suppress a flag to reach readiness; report it and stop.

## Output format

Emit both a human-readable outline and a JSON spec.

Human-readable: the ranked objection list with score rationales; then
per-paragraph blocks (`purpose`, `objection_neutralized`,
`writing_points`, `evidence_anchors`); then the coverage table; then
the flag list grouped by severity, with the top three fixes first.

JSON spec:

```json
{
  "claim_type": "method | problem | measurement | resource | theory",
  "venue_class": "string",
  "objections": [
    {"id": "OBJ-1", "name": "incremental", "likelihood": 3,
     "lethality": 3, "score": 9, "rationale": "string"}
  ],
  "paragraphs": [
    {"id": "P1",
     "purpose": "one sentence",
     "objection_neutralized": ["OBJ-2"],
     "writing_points": ["...", "..."],
     "evidence_anchors": ["Tab. 3", "Sec. 5.2"]}
  ],
  "contributions": [
    {"text": "one sentence with a licensed verb",
     "verb_rung": 3, "anchor": "Sec. 4"}
  ],
  "coverage": [
    {"objection": "OBJ-1", "neutralized_in": ["P2", "P4"],
     "anchors_used": ["Fig. 2"], "status": "covered"}
  ],
  "flags": [
    {"code": "UNCOVERED_LETHAL", "severity": "CRITICAL",
     "target": "OBJ-3", "fix_hint": "string"}
  ],
  "ready_for_writer": false
}
```

The Writer agent consumes `paragraphs[]` in order and must not add,
drop, or reorder paragraphs without re-running the coverage
computation.

## Acknowledgments

The pipeline role of this skill — producing a structured Introduction
outline for a downstream Writer agent — was inspired by HKUSTDial's
Supervisor-Skills project. The objection-driven framework, the
coverage/flag rules, and all text here are an independent redesign
and share no schema or prose with that project.
