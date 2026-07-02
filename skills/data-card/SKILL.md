---
name: data-card
description: >-
  Drafts the reproducibility apparatus required by top venues:
  dataset card (datasheet for datasets), reproducibility checklist
  (NeurIPS-style or per-venue), code-release statement, model card
  (when models are released), data availability statement, and
  artifact-evaluation submission package (SIGMOD AE / VLDB AE / KDD
  AE). Use when the user says 'write data card', 'reproducibility
  statement', 'datasheet', 'artifact evaluation', 'model card',
  'data availability', or 1-2 weeks before a submission deadline
  for a venue that requires these (NeurIPS / ICLR / ACL / SIGMOD /
  VLDB / KDD). Different from nature-data because it targets venue-
  specific templates, not journal-style FAIR.
license: CC-BY-4.0
---

# Data Card

## Overview

Top venues increasingly require explicit reproducibility apparatus:
NeurIPS has a 14-question reproducibility checklist and a 25-question
datasets&benchmarks track; ACL ARR has the responsible NLP checklist;
SIGMOD/VLDB/KDD run formal Artifact Evaluation tracks; ICLR has open-
reviewable code. Missing or shallow answers in these are a common
silent reject signal. This skill produces all required artifacts for
a target venue.

## When to invoke

- 1-2 weeks before submission deadline.
- After all experiments are complete (datasheet needs final dataset
  stats; checklist needs final compute hours).
- When the user names a venue with a checklist requirement.

Do NOT invoke before experiments are stable; the data card will need
to be redone if metrics change.

## Operating procedure

### Stage 0 — Detect venue and required artifacts

Read venue from `PIPELINE_STATE.json` or ask. Load required artifacts
list from `references/venue_requirements.md`:

| Venue | Required |
|---|---|
| NeurIPS | Reproducibility checklist + (D&B track: full datasheet) |
| ICML | Reproducibility checklist |
| ICLR | Reproducibility statement in §, code link |
| ACL/EMNLP/NAACL | Responsible NLP checklist + limitations § |
| AAAI | Reproducibility checklist |
| CVPR/ICCV/ECCV | Code release encouraged, no formal checklist |
| ACM MM | Code release encouraged |
| SIGMOD | Artifact Evaluation submission (separate track) |
| VLDB | Artifact Evaluation submission |
| ICDE | Artifact Evaluation submission (some years) |
| KDD | Reproducibility checklist + Artifact Evaluation (some years) |
| SIGIR | Reproducibility track / code release |
| WWW | Code release encouraged |

### Stage 1 — Datasheet (when applicable)

Use Gebru et al. "Datasheets for Datasets" structure adapted per venue.
Sections:

1. **Motivation**: why was the dataset created? for what task? funded
   by whom?
2. **Composition**: instances / labels / size / size of test split /
   any structural relationships between instances
3. **Collection process**: how was data gathered? when? by whom?
   any pre-processing / cleaning? noise / missing data documented?
4. **Uses**: tasks the dataset has been used for; tasks it should
   NOT be used for; legal / ethical constraints
5. **Distribution**: license, hosting URL, DOI, third-party
   redistribution constraints
6. **Maintenance**: who maintains, contact, update plan, deprecation
   plan

Output: `data_card/datasheet_<dataset>.md`.

### Stage 2 — Reproducibility checklist (per venue)

Load venue-specific checklist from `references/checklists/`:
- `neurips.md` — 14-question + D&B 25-question
- `icml.md` — code release + numerical reproducibility
- `iclr.md` — reproducibility statement template
- `acl_arr.md` — Responsible NLP checklist
- `aaai.md`
- `sigmod_ae.md` — Artifact Evaluation submission template
- `vldb_ae.md`
- `kdd_ae.md`

Each checklist is a series of YES / NO / N/A questions with required
free-text justification. The skill:
1. Reads the paper to auto-fill each answer with evidence pointers.
2. Flags any question where the paper does NOT have evidence — these
   are blockers; either run the missing experiment or weaken the
   claim.
3. Produces a final markdown file in the venue's required format.

Output: `data_card/checklist_<venue>.md`.

### Stage 3 — Code release statement

If venue accepts a code-release statement (most do), draft one with:
- Repository URL (or anonymized URL for double-blind venues)
- License (Apache-2.0 / MIT / CC-BY recommended)
- README pointer
- Setup instructions summary (full README in repo, summary in
  paper §)
- Compute requirements (GPU model, hours, peak VRAM)
- Dependencies pinned (requirements.txt / environment.yml /
  pyproject.toml)
- Anonymization plan for double-blind (commit history scrubbed,
  author names removed)

Output: `data_card/code_release_statement.md` + suggested .tex insertion
for an Appendix section.

### Stage 4 — Model card (when models are released)

Use Mitchell et al. "Model Cards" structure:
1. Model details (name, version, type, parameters, paper, training
   compute)
2. Intended use (primary tasks, primary users, out-of-scope uses)
3. Factors (groups affected by performance, instrumentation)
4. Metrics (which metrics, how computed)
5. Evaluation data (datasets used, motivation, preprocessing)
6. Training data (datasets, distribution, biases known)
7. Quantitative analyses (per-group / per-factor performance)
8. Ethical considerations
9. Caveats and recommendations

Output: `data_card/model_card_<model>.md`.

### Stage 5 — Data availability statement

Short version for paper body / appendix:
- Where the dataset(s) live (URL, DOI)
- License
- How to obtain (direct download / signed agreement / contact author)
- Whether identifiable / sensitive / PHI / requires IRB
- Citation requirement when downstream users re-cite

Output: `data_card/data_availability.tex` (1-paragraph drop-in).

### Stage 6 — Artifact-Evaluation submission package

SIGMOD AE, VLDB AE, KDD AE: separate submissions after main paper
acceptance. Template per venue in `references/checklists/`.

Package contents:
- README (build instructions, run instructions, expected output)
- Hardware / OS requirements
- Docker / VM image (if applicable)
- Datasets included or download script
- Expected runtime per experiment
- Mapping: each table/figure in paper → script command to reproduce it
- Smoke-test run that completes in <10 min

Output: `data_card/artifact_evaluation/` directory tree.

## Cross-skill interactions

- `pre-submission-reviewer` — runs on the produced .tex inserts to
  check formatting / banned tokens.
- `citation-verifier` — runs on any new cites introduced (especially
  in datasheet motivation and citing prior datasets).
- Maestro — handoffs:
  - If checklist Stage 2 flags missing evidence, surface as new
    P-task to Maestro (probably a missing ablation or sensitivity
    experiment).
  - Code release URL coordination with the actual repository.

## Constraints

- Honesty: every YES answer must have an evidence pointer to the
  paper (§ + line) or to a run log. Never check YES without evidence.
- Anonymization: for double-blind venues, never reveal author /
  institution / repository URL containing names.
- Sensitive data: if dataset contains PHI / personal data, the
  data availability statement must explicitly state ethics approval /
  consent / data-use agreement. Flag any case where this is missing.
- Compute honesty: total GPU-hours reported must match run-log
  aggregation, not just the headline runs.

## References

- `references/venue_requirements.md` — what each venue requires
- `references/checklists/*.md` — per-venue checklist templates
- `references/datasheet_template.md` — Gebru et al. adapted
- `references/model_card_template.md` — Mitchell et al. adapted
- `references/ethics_red_flags.md` — when to escalate (PHI, faces,
  scraped social media, minors)
