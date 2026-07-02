---
name: reviewer-panel
description: >-
  Simulates a CCF A conference review panel — three independent
  reviewers with distinct personas (theory hawk, empirical
  pragmatist, narrative skeptic) plus an Area Chair meta-review —
  on a draft paper or section. Uses the venue's actual rating scale
  (NeurIPS 1-10, ICLR 1-10, ACL 1-5, SIGMOD A/B/C/D, etc.) and
  produces per-reviewer scores with strengths / weaknesses /
  questions plus an AC recommendation (Accept / Borderline / Reject)
  with weighted rationale. Use when the user asks 'simulate
  reviewers', 'mock review', 'panel review', 'pre-submission
  reviewer panel', or 'what would 3 reviewers say'. Different from
  pre-submission-reviewer, which is a single-perspective copy-edit
  review.
license: CC-BY-4.0
---

# Reviewer Panel

## Overview

CCF A papers are decided by 3 reviewers plus an area chair / meta-
reviewer who weighs the panel. A single-perspective copy-edit review
(handled by `pre-submission-reviewer`) does not surface the divergent
objections a real panel raises. This skill fans out three independent
review passes under distinct personas plus an AC pass, then synthesizes
the four into a verdict and a prioritized revision list.

## When to invoke

- User says "panel review", "mock review", "simulate reviewers",
  "what would reviewers say".
- One-pass `pre-submission-reviewer` has passed but user wants
  decision-level signal before submitting.
- 2-4 weeks before a deadline, after the draft is feature-complete but
  before the final polish round.

Do NOT invoke for line-level copy edits — use `pre-submission-reviewer`
for that. Do NOT invoke on incomplete drafts (missing experiments,
placeholder text) — the panel will reject and the signal is useless.

## Panel composition

Three personas, scored independently with no cross-talk:

### R1 — Theory / methodology hawk
- Reads §3 (problem formulation), §4 (method), proofs/appendix.
- Tests: is the formulation precise? are assumptions stated? is the
  novel claim actually novel vs. cited prior work? do the theorems
  hold without hidden assumptions? does the method follow from the
  formulation or is it a separate engineering artifact glued on?
- Failure modes flagged: under-specified problem, hidden assumption,
  proof gap, incremental over [closest prior work].

### R2 — Empirical / engineering pragmatist
- Reads §5 (experiments), §6 (analysis), tables/figures, appendix
  reproducibility section.
- Tests: are baselines strong and fair? is the metric appropriate?
  are seeds and CIs reported? are the datasets representative? does
  the headline number survive sensitivity / ablation? would I be able
  to reproduce this from the paper alone?
- Failure modes flagged: weak baselines, cherry-picked datasets,
  no error bars, hyperparameter mismatch favoring proposed method,
  missing ablation, reproducibility blockers.

### R3 — Narrative / motivation skeptic
- Reads §1 (intro), §2 (related work), §7 (discussion / limitations),
  abstract.
- Tests: is the motivation grounded in a real problem? is the related
  work fair to prior art and not strawmanned? are the limitations
  honest? does the story hold together across abstract / intro /
  conclusion? is the contribution claim load-bearing or padded?
- Failure modes flagged: motivation handwave, strawman related work,
  scope creep, conclusion over-reaches the experiments.

### AC — Area chair / meta-reviewer
- Reads R1+R2+R3 reviews, skims the paper, looks at the rebuttal-
  affected sections.
- Tests: weigh R1/R2/R3 by which concerns are load-bearing for the
  paper's headline claim. Flag disagreement axes. Recommend ACCEPT /
  BORDERLINE / REJECT with explicit weighting rationale.

## Operating procedure

### Stage 0 — Detect venue and scale

Read venue from `PIPELINE_STATE.json` or ask. Load:
- Rating scale (per venue)
- Acceptance threshold (typical)
- Decision lexicon (Accept/Weak Accept/Borderline/Weak Reject/Reject)
  per `references/venue_scales.md`

### Stage 1 — Three independent reviewer passes

Run R1, R2, R3 in parallel. Each persona MUST:
- Read only its assigned sections deeply; skim the rest.
- Produce: 3-5 strengths, 5-10 weaknesses, 3-7 questions, score on
  venue scale, confidence (1-5).
- NOT collaborate with other personas (no cross-references).

Personas are launched as separate Agent calls with the same paper
input but different system prompts (see `references/persona_prompts.md`).

### Stage 2 — AC meta-review

AC reads the three reviews + the paper's abstract+intro+headline tables.

AC produces:
- Recommendation: ACCEPT / BORDERLINE / REJECT
- Confidence: 1-5
- Weighting: which reviewer's concerns dominate, with rationale
- Top 3 revisions: prioritized list of changes that would shift to
  ACCEPT (if BORDERLINE/REJECT) or harden against future REJECT
  (if ACCEPT)
- Disagreement axes: where reviewers split, who is right and why

### Stage 3 — Verdict synthesis

Output a single JSON:

```json
{
  "venue": "NeurIPS 2026",
  "scores": {"R1": {"rating": 5, "confidence": 4},
             "R2": {"rating": 4, "confidence": 5},
             "R3": {"rating": 6, "confidence": 3}},
  "mean_score": 5.0,
  "ac_recommendation": "BORDERLINE",
  "ac_confidence": 4,
  "top_3_revisions": [...],
  "disagreement_axes": [...],
  "per_reviewer_reports": {"R1": "...", "R2": "...", "R3": "..."},
  "ac_meta_review": "..."
}
```

## Output structure

```
review_panel/
├── R1_theory.md
├── R2_empirical.md
├── R3_narrative.md
├── AC_meta.md
├── verdict.json
└── revision_plan.md      (prioritized, ordered by ROI)
```

## Calibration

Personas tend to drift soft over time. Apply these calibrations:
- If any persona gives all scores ≥7, force a re-pass with the
  prompt: "Re-read assuming the paper is your competitor's. Find 3
  more weaknesses you would press in discussion."
- If AC always says ACCEPT on borderline panels, the panel is
  miscalibrated; re-pass with explicit acceptance rate (e.g.,
  NeurIPS ~26%) injected.
- Maintain `references/calibration_log.md` with score distributions
  from past panels for sanity check.

## Cross-skill interactions

- `pre-submission-reviewer` — run AFTER panel revisions land, for
  copy-edit polish. Panel surfaces decision-level issues;
  pre-submission catches mechanical defects.
- `rebuttal-drafter` — feed the panel's R1/R2/R3 reports into
  `rebuttal-drafter` as a dry-run rebuttal target. If rebuttal cannot
  satisfy the panel on paper, the real rebuttal will fail too.
- `intro-drafter` / `tech-paper-template` — if R3 flags narrative
  problems, re-invoke intro-drafter or tech-paper-template to
  restructure.
- `figure-designer` — if R2 flags figure quality, invoke
  figure-designer.

## References

- `references/persona_prompts.md` — system prompts per persona,
  with section-assignment rules.
- `references/venue_scales.md` — rating scales, acceptance
  thresholds, decision lexicon per CCF A venue.
- `references/calibration_log.md` — score distributions from prior
  panels (append-only).
