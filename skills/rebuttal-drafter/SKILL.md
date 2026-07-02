---
name: rebuttal-drafter
description: >-
  Drafts point-by-point reviewer responses for top-tier AI/DB venues
  (NeurIPS / ICML / ICLR / ACL / EMNLP / NAACL / AAAI / IJCAI /
  CVPR / ICCV / ECCV / ACM MM / SIGMOD / VLDB / ICDE / KDD / SIGIR
  / WWW). Parses reviewer comments into a triage table, classifies
  each as minor / major / misunderstanding / new-experiment,
  enforces venue character/word limits, and assembles the final
  response under a tone-discipline policy (no fabrication, no
  hedging, quantify every claim). Use when the user says 'draft
  rebuttal', 'write reviewer response', 'rebuttal phase started',
  'reply to reviewers', or pastes reviewer comments and asks for a
  reply. For ICLR/OpenReview discussion-style rebuttals it produces
  one comment per reviewer; for SIGMOD/VLDB shepherd letters it
  produces a single revision-letter draft.
license: CC-BY-4.0
---

# Rebuttal Drafter

## Overview

Rebuttal is the highest-leverage 5-7 days in a paper's lifecycle:
a clear point-by-point response routinely lifts decisions across the
borderline. This skill takes raw reviewer text and produces a draft
that follows the four operating rules every successful rebuttal
shares: triage before drafting, defend in concession-objection-evidence
order, never fabricate, respect the venue's hard character budget.

## When to invoke

- Reviewer comments are pasted or pointed to (`reviews/*.txt`, OpenReview
  thread, EasyChair export, Microsoft CMT JSON).
- User mentions "rebuttal phase", "author response", "shepherd letter",
  "discussion period", or a top venue's known rebuttal window.
- Maestro's pipeline has reached a venue's rebuttal stage and the
  Reviewer agent has flagged reviewer comments inbound.

Do NOT invoke for general editing or for non-rebuttal review responses
(grant rebuttals, editorial decisions on journals not in scope).

## Operating procedure

### Stage 0 — Detect venue and load constraints

Identify the venue from the user message or from `PIPELINE_STATE.json`'s
`venue` field. Load the venue's hard limits from `references/venue_limits.md`.
If venue is ambiguous, ask once.

### Stage 1 — Triage table

For every reviewer comment produce one row:

| ID | Reviewer | Comment (≤25 words) | Class | Severity | Evidence path | Char budget |

Classes:
- **MINOR-ACK** — typo, citation, wording. Acknowledge in ≤25 words.
- **MAJOR-DEFEND** — methodological objection. Concede the surface
  point if any, then refute with evidence already in the paper or
  appendix. 60-120 words.
- **MAJOR-MISUNDERSTANDING** — reviewer misread. Quote the misread
  passage, clarify, point to the exact section/line. 40-80 words.
- **NEW-EXPERIMENT** — requires a new run. Flag and surface to Maestro
  as a P-task; do NOT draft prose until the run lands.
- **OUT-OF-SCOPE** — politely decline, redirect to future work. 30-60
  words. Use sparingly (≤1 per reviewer).

Severity 1-3. Sum severity × char-budget per reviewer; verify under
venue cap.

### Stage 2 — Defense order per reviewer

Order is NOT the reviewer's order. Use:

1. Strongest MAJOR-DEFEND first (sets the tone).
2. Remaining MAJOR-DEFEND descending by severity.
3. MAJOR-MISUNDERSTANDING grouped (one paragraph each).
4. NEW-EXPERIMENT results (if landed).
5. MINOR-ACK bulleted at the end.
6. OUT-OF-SCOPE last, single sentence.

### Stage 3 — Prose generation

For each row, generate prose under these rules:

**MUST**
- Start MAJOR-DEFEND with a one-clause concession ("The reviewer is
  right that X, however ..."). Never start with "We disagree".
- Quote ≤8 words of the comment verbatim when responding, in italics.
- Cite the supporting evidence by section + line number or
  table/figure ID. If evidence is in appendix only, say so.
- Numbers: report mean ± std or 95% CI, never bare means.

**MUST NOT**
- "We believe", "We think", "We hope", "It is clear that",
  "obviously", "trivially", "novel", "first of its kind".
- New unverified claims. If a claim is not in the paper or run logs,
  do not write it.
- Em-dashes (use semicolons or commas per house style).
- Personal attacks or defensive tone ("the reviewer misunderstood
  the entire premise") even when justified.

**Tone discipline check** before assembly: scan every draft for the
banned tokens above. Fail if any survives.

### Stage 4 — Assembly and budget enforcement

- ICLR / NeurIPS / OpenReview: one comment per reviewer, Markdown,
  ≤ venue limit per comment.
- ACL / EMNLP / NAACL: single PDF/text response, ≤ venue word limit
  total.
- SIGMOD / VLDB / ICDE: single revision letter, prose plus a
  changes-summary table at the top.
- CVPR / ICCV / ECCV / AAAI / IJCAI: one comment per reviewer plus
  a 1-page common response.

If the assembled draft exceeds budget, compress in this order: drop
OUT-OF-SCOPE, then trim MINOR-ACK to bullets, then trim MAJOR-DEFEND
secondary evidence, never trim the lead concession.

### Stage 5 — New-experiment loop (optional)

If any NEW-EXPERIMENT rows exist, emit a structured handoff to Maestro:

```json
{
  "rebuttal_new_experiments": [
    {"row_id": "...", "reviewer": "R2", "exp_brief": "...",
     "gpu_h_estimate": 1.5, "deadline_relative_to_rebuttal": "T-72h"}
  ]
}
```

Maestro fans these out to Coder/Engineer/Runner. Drafter waits, then
resumes Stage 3 for those rows once metrics.json lands.

## Output structure

```
rebuttal/
├── triage_table.md          (Stage 1)
├── per_reviewer/
│   ├── R1.md                (Stage 4 per-reviewer)
│   ├── R2.md
│   └── ...
├── common_response.md       (only for CVPR-family)
├── revision_letter.md       (only for SIGMOD-family)
└── new_exp_handoff.json     (only if Stage 5 fired)
```

## Cross-skill interactions

- `pre-submission-reviewer` — if rebuttal references new figures/tables,
  re-invoke pre-submission-reviewer on the appendix to scrub for fresh
  AI-tone / em-dash violations.
- `citation-verifier` — if rebuttal cites a new paper (e.g.,
  "[Smith 2024] addresses this concern"), invoke citation-verifier on
  the new bibtex entry.
- `reviewer-panel` — to dry-run the rebuttal: feed back to a fresh
  reviewer-panel and check whether the draft response would actually
  shift R1/R2/R3 scores. If not, revise.

## References

- `references/venue_limits.md` — character/word caps per top venue
- `references/banned_tokens.md` — full banned-word list (mirrors
  pre-submission-reviewer for consistency)
- `references/defense_templates.md` — concession-objection-evidence
  template phrases, vetted
