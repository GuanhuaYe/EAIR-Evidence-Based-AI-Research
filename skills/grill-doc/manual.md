# Interrogation Manual

Fixed question banks per methodology failure category. The griller asks
these — and only these — plus their conditional follow-ups. Free-form
improvisation is forbidden (free-form questioning drifts toward whatever the doc already answers well).

Each question: `qid | criticality | question | what satisfies it`.
Criticality: `critical` (GAP/HAND-WAVED → BLOCK) or `major` (→ PASS-WITH-NOTES).
Follow-ups fire only when the parent condition holds.

Sources: recurring failure patterns in LLM-evaluation research, plus
probing-methodology literature (Hewitt & Liang control tasks; "On the
Data Requirements of Probing" 2202.12801; Card et al. 2020 power).

---

## C1 Confounding & pooling

- **CONF-1 | critical** — Does any headline metric pool samples across
  subgroups (direction, language, source, site, task)? List every
  subgroup entering each headline number.
  *Satisfied by*: a doc section enumerating the subgroups per metric, or
  stating the metric is computed within a single population.
- **CONF-2 | critical** *(follow-up: fires if CONF-1 reveals pooling)* —
  What is each subgroup's label base rate, and where does the doc commit
  to reporting per-subgroup metrics alongside the pooled number?
  *Satisfied by*: per-subgroup base rates + an explicit per-subgroup
  reporting plan. (Failure pattern: two subgroups with 37% vs 74%
  base rates pooled into one AUROC — the classifier could learn
  subgroup identity alone.)
- **CONF-3 | major** *(follow-up: fires if pooling)* — Can any input
  feature identify the subgroup (e.g. language identity in hidden
  states)? What control shows the signal is not subgroup identity
  (within-subgroup metrics, subgroup-shuffled control)?
  *Satisfied by*: a named control experiment in the doc.

## C2 Leakage

- **LEAK-1 | critical** — Is cross-validation / train-test splitting
  grouped by the natural correlated unit (question ID, patient,
  document, entity)? Quote the grouping key.
  *Satisfied by*: explicit group-CV or grouped-split specification.
  (Failure pattern: paired rows derived from the same question were
  split across folds.)
- **LEAK-2 | critical** — At any point, does feature computation, data
  selection, or preprocessing touch labels or test data (including
  fitting PCA/scalers outside the CV fold)?
  *Satisfied by*: a statement that all fitting happens inside folds /
  on train only. (Failure pattern: a judge component retrieved other
  gold items — check tooling can't reach eval data either.)
- **LEAK-3 | major** — Is the final eval set isolated from every tuning
  and model-selection decision? How many times has it been evaluated
  against during development?
  *Satisfied by*: a held-out discipline statement (touch count / final
  set never used for selection).

## C3 Statistical power

- **POW-1 | critical** — What is the effective n per cell (subgroup ×
  condition) for each headline metric — after filtering to the
  relevant subset (e.g. only wrong-answer samples)? State the smallest
  cell.
  *Satisfied by*: per-cell counts in the doc. (Failure pattern: a
  headline metric rested on n=65.)
- **POW-2 | critical** *(follow-up: fires if any model has learned
  parameters)* — Feature dimensionality vs effective n for every fitted
  model? If p is within 10x of n, what regularization/reduction is used
  and where is it fit?
  *Satisfied by*: explicit p, n, and in-fold reduction plan.
  (Failure pattern: 3584-dim features fed into a 65-sample logistic
  regression.)
- **POW-3 | critical** — How is uncertainty quantified for each headline
  number (bootstrap CI / permutation test), and what is the
  pre-declared significance criterion for claiming a win over baseline?
  *Satisfied by*: named procedure + criterion in the doc.
- **POW-4 | major** — What effect size is expected, and is the planned n
  sufficient per published power baselines for this measurement type
  (probing comparisons: N_test≈4096, arXiv 2202.12801)?
  *Satisfied by*: a power justification with a cited or derived basis.

## C4 Baseline parity

- **BASE-1 | critical** — What is the strongest standard baseline in
  this literature (name + citation), and is the plan to run the ORIGINAL
  method or a proxy? If a proxy: quote where the doc justifies it.
  *Satisfied by*: named baseline with citation and faithful-implementation
  commitment. (Failure pattern: a "self-consistency baseline" was
  actually cross-view answer agreement, never Wang et al. 2022
  temperature sampling — the single most reviewer-catchable hole.)
- **BASE-2 | major** — Do baselines get the same compute budget and
  information access as the proposed method?
  *Satisfied by*: a budget-parity statement.
- **BASE-3 | major** — Are oracle upper and random lower bounds planned,
  so the achievable headroom is known before optimizing?
  *Satisfied by*: oracle/random bound specification. (Failure pattern:
  the oracle-random frame is what killed a dead hypothesis cleanly.)

## C5 Metric validity

- **MET-1 | critical** — State the claim→metric chain: what downstream
  claim does the headline metric license, and what is the argument that
  the metric is not a dead end (decodability ≠ actionability: a probe
  AUROC can be high while the signal is useless for any intervention)?
  *Satisfied by*: an explicit chain in the doc from metric to claimed
  payoff.
- **MET-2 | major** — Is there an end-to-end validation (real downstream
  task / accuracy-vs-budget curve), or does evaluation stop at
  intermediate metrics?
  *Satisfied by*: a planned end-to-end experiment.
- **MET-3 | major** — What control task / shuffled-label check shows the
  metric can't be gamed by shortcuts (Hewitt & Liang selectivity)?
  *Satisfied by*: a named control.

## C6 Comparability & reproducibility

- **REP-1 | major** — Are test set, model checkpoint, and decoding
  conditions (temperature, concurrency, seeds) pinned and recorded per
  reported number?
  *Satisfied by*: a conditions table or equivalent commitment.
  (Failure pattern: concurrency=8 flips results at temp=0;
  cross-version F1 incomparable.)
- **REP-2 | major** — Is run-to-run variance measured before any single
  number is treated as a conclusion (repeat runs / seed sweep)?
  *Satisfied by*: a repeat-run plan. (Internal example: 4 reruns of the
  same config scored 81/77/81/81.)
- **REP-3 | major** — Does the project maintain an EVOLUTION.md-style
  ledger with a "do-not-retry" veto list, and does this design
  conflict with any previously vetoed direction?
  *Satisfied by*: pointer to the ledger + a no-conflict statement.

---

## Editing discipline

- Questions may be ADDED or TIGHTENED; acceptance criteria may never be
  loosened (iron rule 4 in SKILL.md).
- After any edit, re-run `regression/` (your own gold set of a design
  doc with known gaps) and require most gold gaps surfaced. Log the
  edit + regression result at the bottom of this file.

## Known limitation (do not paper over)

The quote gate verifies an answer is GROUNDED, not that it MEETS THE BAR
in each question's *Satisfied by* line. Observed in an internal
regression run: POW-3 tagged ANSWERED because the doc states a criterion
("clearly higher than" + a fixed reference line) — grounded, but not a
named uncertainty procedure. Mitigation: the griller must re-read every
ANSWERED item against its *Satisfied by* line during Step 4 and may
downgrade routing (add it to the fix list) — but may NOT overturn the
gate tag or the verdict. If a question keeps producing
grounded-but-below-bar answers, TIGHTEN the question text (allowed)
instead of adding griller discretion (forbidden).

## Edit log

- 2026-07-02 — Initial manual (v1).
  postmortems. Regression run 1 (defender=sonnet, doc=an internal
  pre-run design with 4 pre-registered gaps): 4/4 gold gap areas
  surfaced, verdict BLOCK — PASS. POW-3 grounded-but-weak instance
  logged above.
- 2026-07-02 — gate.py norm() now also strips markdown emphasis chars
  (`* \` _`) symmetrically from quote and doc. Cause: a live grill
  false-HAND-WAVED LEAK-3 because the doc had a bold phrase
  (`**fix-before-run**`) and the defender quoted the unformatted text.
  Symmetric normalization, cannot admit fabricated text — not a
  loosening. Regression re-run: 4/4 surfaced, verdict BLOCK — PASS.
- 2026-07-02 — gate.py norm() also maps curly quotes to straight
  quotes, symmetrically. Cause: live grill round 2, REP-3 quote failed
  on quote-mark style alone. Regression re-run: 4/4 surfaced — PASS.
  First live deployment (internal design doc, defender=sonnet): round 1
  BLOCK (CONF-3/LEAK-2/POW-4/REP-3 gaps — subgroup pooling nearly
  re-entered via a comparison table, caught by CONF-3); after doc
  fixes + EVOLUTION.md creation, round 2 verdict PASS 19/19.
