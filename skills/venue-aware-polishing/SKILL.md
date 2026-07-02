---
name: venue-aware-polishing
description: >-
  Polishes English prose for a specific CCF A venue's house style.
  Selects the right register, sentence shape, and vocabulary band
  per venue family — NeurIPS / ICML / ICLR are compact and
  formal; ACL / EMNLP / NAACL are narrative; SIGMOD / VLDB / ICDE
  are engineering-direct; CVPR / ICCV / ECCV are visual-anchored.
  Removes AI-tone, em-dashes, hedge tokens, and Chinglish patterns
  common in non-native English writing. Use when the user says
  'polish this section', 'refine the prose', 'tighten the writing',
  'sound more like a NeurIPS paper', 'rewrite for ACL style', or
  asks for a style pass distinct from copy-editing. Different from
  pre-submission-reviewer (which only flags) — this one rewrites.
license: CC-BY-4.0
---

# Venue-Aware Polishing

## Overview

A NeurIPS sentence and a SIGMOD sentence reading the same content
should not be written the same way. NeurIPS rewards compact,
quantification-first prose; SIGMOD rewards engineering-direct,
mechanism-first prose; ACL rewards narrative continuity and
hedge-aware claims; CVPR rewards figure-anchored framing. A generic
"Nature style" polish is wrong for all four. This skill picks the
venue's house style and rewrites accordingly, while enforcing the
shared hygiene rules (no em-dash, no AI-tone, no banned hedges).

## When to invoke

- User points to a section / file and says "polish for {venue}",
  "rewrite in NeurIPS style", "make this read like an ACL paper",
  "tighten this".
- After paper-write or intro-drafter produces a first draft.
- Before reviewer-panel runs, to remove style penalties that would
  inflate cosmetic objections.

Do NOT invoke for ideas / structure / argument changes (use
intro-drafter or tech-paper-template). Do NOT invoke for line-level
typo fixes (use pre-submission-reviewer).

## Operating procedure

### Stage 0 — Detect venue

Read `PIPELINE_STATE.json` venue field or ask. Load the venue family
profile from `references/style_profiles.md`. Five families:

| Family | Venues | Profile name |
|---|---|---|
| ML-formal | NeurIPS / ICML / ICLR | `ml-formal` |
| NLP-narrative | ACL / EMNLP / NAACL / TACL | `nlp-narrative` |
| DB-engineering | SIGMOD / VLDB / ICDE | `db-engineering` |
| CV-visual | CVPR / ICCV / ECCV / ACM MM | `cv-visual` |
| Mining-applied | KDD / SIGIR / WWW / WSDM / ICDM / CIKM | `mining-applied` |

AAAI / IJCAI: route by topic (theory → ml-formal; application → mining-applied).

### Stage 1 — Style profile load

Each family has a profile spec covering:
- Sentence length target (mean ± std)
- First-person register ("we" vs "this paper" vs passive)
- Quantification placement (sentence-initial / mid / late)
- Acceptable hedges (none for ML-formal; some for NLP-narrative)
- Figure/table reference style ("Fig. 3" vs "Figure 3" vs "(Fig. 3)")
- Technical vocabulary band (jargon-OK level)
- Section-heading register (noun-phrase / sentence / question)

### Stage 2 — Pass 1: Hygiene scrub (shared across venues)

Remove or rewrite:
- All em-dashes → semicolons, commas, parens, or sentence split.
- AI-tone vocabulary (full list in `references/banned_tokens.md`,
  mirrors rebuttal-drafter and pre-submission-reviewer).
- Hedge tokens that the venue family rejects (per profile).
- Sentence-initial "And", "But", "So" (unless venue family allows).
- "Etc." in technical writing.
- Double-negation, triple-negation.
- "It is X that Y" cleft constructions when the venue prefers direct.

### Stage 3 — Pass 2: Venue-aware rewrites

Apply venue-specific transforms:

**ML-formal (NeurIPS/ICML/ICLR)**:
- Mean sentence length 18-25 words.
- Quantification sentence-initial when possible: "On benchmark X,
  method Y achieves +A.B over Z."
- "We" register OK; passive register OK; "this paper" register slightly
  weak.
- No hedges in claims. Hedge OK in limitations only.
- Equations are first-class — interleave with prose, not in a wall.
- Section headings: short noun-phrases.

**NLP-narrative (ACL/EMNLP/NAACL)**:
- Mean sentence length 20-28 words.
- Quantification mid-sentence acceptable, with explanatory wrap-around.
- "We" register strong; this paper register fine.
- Mild hedges OK ("suggests", "indicates") in analysis.
- Section headings: sentence-length OK, even question form.
- Linguistic examples in italics, with gloss.

**DB-engineering (SIGMOD/VLDB/ICDE)**:
- Mean sentence length 16-22 words. Direct, engineering-tone.
- Quantification mid-late: "Method X reduces latency by 3.2× at
  P99 on TPC-DS scale 100."
- "We" OK; passive OK; "the system" register dominant.
- No hedges. Engineering paper: state what was built, what it
  measured.
- Section headings: noun-phrases, often with mechanism: "4. The
  ABC Operator", "5. Index Maintenance".
- Tables prefer numeric precision; figures prefer architecture.

**CV-visual (CVPR/ICCV/ECCV/ACM MM)**:
- Mean sentence length 18-24 words.
- Quantification mid-sentence with figure/table anchor: "As shown in
  Fig. 4, method X achieves +A.B mAP over Z."
- "We" register strong.
- Visual-first framing — refer to figure before introducing
  quantitative result when possible.
- Section headings: noun-phrases.

**Mining-applied (KDD/SIGIR/WWW)**:
- Mean sentence length 18-26 words.
- Application-first framing: "We deploy X in setting Y serving Z
  users, observing ..."
- "We" + "the system" register both fine.
- Mild hedges OK in deployment discussion.
- Section headings: noun-phrases; "Deployment" sections common.

### Stage 4 — Pass 3: Chinglish patterns (universal, last pass)

Authors writing English as L2 commonly produce these patterns. Detect
and rewrite:

- Article drop: "We propose method" → "We propose a method"
- Article overuse: "The Figure 3 shows" → "Figure 3 shows"
- Tense drift in analysis: keep one tense per discussion paragraph
- Subject-verb agreement on collective nouns
- "Which" vs "that" misuse
- "However" + comma at sentence start used too often
- Comma splice ("X is fast, it has high throughput") → semicolon
  or split
- Topic-comment to subject-predicate restructuring for sentences
  with "as for X, ..." pattern

### Stage 5 — Output

Two-file output per polished section:

```
polished/
├── <section>.diff.md       (side-by-side: original | rewrite)
└── <section>.tex           (drop-in replacement for the .tex file)
```

Diff file shows every sentence-level change with a reason tag:
HYGIENE / VENUE-{family} / CHINGLISH / SENTENCE-LENGTH.

User reviews diff before accepting. Skill MUST NOT write to the
canonical .tex without user confirmation; produce alongside.

## Constraints and overrides

- Numbers, equations, citations: never alter content. Only restructure
  surrounding prose.
- Locked sections (per Maestro's submit-gate locked sections list):
  if a section is locked, refuse to polish unless user explicitly
  unlocks.
- Theorem/lemma/proof environments: do not touch internals. May
  rewrite the prose that introduces them.
- Do not introduce new claims. If a claim does not exist in the source,
  the polish should not invent it.

## Cross-skill interactions

- `pre-submission-reviewer` — run AFTER polish; pre-submission-reviewer
  checks mechanical violations the polish missed.
- `intro-drafter` / `tech-paper-template` — run BEFORE polish; polish
  assumes the argument structure is already correct.
- `citation-verifier` — run BEFORE polish; polish does not touch
  citation contents but assumes cites are valid.
- `rebuttal-drafter` — rebuttal prose has its own tone discipline
  (in rebuttal-drafter); do not invoke venue-aware-polishing on
  rebuttal text.

## References

- `references/style_profiles.md` — per-family profile spec
- `references/banned_tokens.md` — shared with rebuttal-drafter (link)
- `references/chinglish_patterns.md` — L2-English failure modes
- `references/heading_register.md` — venue-specific heading
  capitalization and form
