---
name: pre-submission-reviewer
description: >-
  Regression-aware submission audit for research papers. Runs five
  evidence-gated sweeps (claims-vs-evidence, numbers, compliance,
  language, figures/tables) over a draft, or re-audits a revised
  draft against a previous report to catch unfixed and regressed
  defects. Emits structured JSON findings with computed severities
  for a Writer agent to consume. Use when asked to audit a draft
  before submission, re-check a revision, or verify that earlier
  review findings were actually fixed.
license: CC-BY-4.0
---

# Regression-Aware Submission Audit

## Purpose

Most papers are not sunk by one bad idea; they are sunk by drift.
The abstract promises what Section 5 no longer delivers. A number
was updated in Table 3 but not in the conclusion. An acknowledgment
paragraph survives into the anonymized PDF. And the deadliest drift
of all: a defect that was found and fixed in round two quietly
returns in round four, because nobody re-checked old findings
against the new draft.

This skill audits a draft in two modes:

- **Mode A (full audit)** runs five independent sweeps over the
  whole draft and emits a machine-readable finding list.
- **Mode B (regression re-audit)** takes a *previous audit report*
  plus the *revised draft*, verifies the disposition of every prior
  finding (FIXED / UNFIXED / REGRESSED), and sweeps only the
  changed material for new issues.

The output is an audit, not a rewrite. Findings feed a downstream
Writer agent (or a human author), which applies fixes and sends the
revision back through Mode B. The Mode A → Writer → Mode B loop is
the intended steady state in the days before a deadline.

## The evidence gate (house rule)

**A finding without a verbatim quote and a location is invalid and
must be discarded before output.** Every finding carries:

- `verbatim_quote`: the exact offending text as it appears in the
  source (or, for visual issues, the exact caption/label text plus
  a description of the visual defect). Never paraphrased, never
  reconstructed from memory. If you cannot produce the exact string,
  you have not found anything yet.
- `location`: section number, page, figure/table number, or source
  file and line — the most precise locator available from the input.

Severities are **computed, not felt**. Apply the rules in
`references/severity-rulebook.md`; do not escalate or downgrade on
taste. If two rules match one finding, the higher severity wins.

## Inputs

- **Mode A**: the draft (LaTeX source preferred; PDF text
  acceptable), the target venue name, and if available the venue's
  formatting/anonymity rules and page limit.
- **Mode B**: everything in Mode A, plus the previous audit report
  (the JSON from a prior run) and, if available, a diff between the
  audited and revised drafts. If no diff is provided, construct one
  (e.g., `latexdiff` on sources, or a section-by-section comparison)
  before starting; Mode B without any change map degrades to Mode A
  plus finding-disposition checks.

If the user supplies a prior report, default to Mode B. Otherwise
run Mode A. State the chosen mode before starting.

## Mode A — Full audit

Run all five sweeps. Sweeps are independent; run them in order but
never let one sweep's outcome suppress another's findings.

### Sweep 1: Claims vs. evidence

Extract every claim sentence from the abstract and introduction
(and the contribution list, if separate). For each claim:

1. **Trace it.** Identify the section, table, figure, or theorem
   that is supposed to substantiate it. Record that anchor in the
   finding's `trace` field. A claim with no locatable anchor is an
   **unsupported claim** (CRITICAL).
2. **Grade the verb against the evidence** using the overclaiming
   ladder, strongest to weakest:

   | Verb tier | Requires |
   |---|---|
   | prove / guarantee | a theorem with a complete proof |
   | demonstrate / show | direct experimental results in this paper |
   | find / observe | measured results, possibly narrow in scope |
   | suggest / indicate | indirect or partial evidence |
   | hypothesize / conjecture | no evidence required, framing only |

   A claim whose verb sits **above** its evidence tier is an
   **overclaim** (MAJOR; CRITICAL if it is a headline contribution).
   A verb one or more tiers *below* the evidence is an underclaim —
   report it as MINOR, since it wastes earned credit but harms
   nothing.
3. **Check scope.** Flag universal quantifiers ("across all
   settings", "for any distribution") whose supporting experiments
   cover a strict subset of that scope.

### Sweep 2: Numbers

Every number that appears in the abstract, introduction, or
conclusion must reappear in a table or figure **with the same value
under the same conditions** (same dataset, metric, baseline, and
setting). Build the full number inventory first, then reconcile:

- **Orphan number**: appears in prose, never in any table/figure.
  MAJOR (CRITICAL if it is a headline result in the abstract).
- **Stale number**: the table/figure value changed in revision but
  the prose kept the old value, or prose and table simply disagree.
  CRITICAL — this is the single most common late-stage defect.
- **Condition drift**: the value matches but the stated conditions
  do not (prose says "on average", table shows best-case; prose
  cites the wrong baseline). MAJOR.
- Also verify derived arithmetic quoted in prose ("a 2.3×
  speedup", "reducing error by 41%") against the raw table values.
  A wrong derivation is CRITICAL.

### Sweep 3: Compliance

Venue mechanics. Check, at minimum:

- **Page limit**: body pages vs. the venue cap, and whether
  references/appendix are excluded per the venue's rules.
- **Anonymization leaks** (each occurrence is CRITICAL, always):
  - a surviving acknowledgments or funding section;
  - self-citation phrasing that de-anonymizes ("as we showed in
    [12]", "our prior system");
  - repository, project-page, or institutional URLs that identify
    the authors;
  - PDF metadata (author, creator fields) and embedded file paths
    (`/home/username/...` strings in included figures);
  - author-identifying artifact names in supplementary files.
- **Reference format**: consistent bibliography style, no raw
  "arXiv preprint" entries for papers that have published venues,
  no dead placeholder citations (`[?]`, missing bibkeys).
- **Checklist forms**: if the venue requires a reproducibility /
  ethics / broader-impact checklist, verify it exists and that no
  answer contradicts the paper body (e.g., checklist says "code
  released" while the paper never links code).

### Sweep 4: Language

Scan the full text for prose patterns that read as machine-flavored
or non-native, plus recurrent grammar faults. The pattern catalogue
with detection cues and rewrite templates is in
`references/language-patterns.md`. The four machine-flavor families:

1. **Uniform sentence openings** — runs of consecutive sentences
   opening with the same scaffold ("Moreover, ... Furthermore, ...
   Additionally, ...", or three sentences in a row starting "This").
2. **Hedging stacks** — two or more hedges guarding one clause
   ("could potentially", "may possibly suggest that it might").
3. **Empty intensifiers** — adjectives and adverbs that add zero
   information and would survive deletion unnoticed ("significantly
   novel", "extremely comprehensive", "truly remarkable").
4. **List-itis** — prose flattened into enumerations where an
   argument is owed: three or more consecutive paragraphs that are
   each a bullet list, or "First, ... Second, ... Third, ..."
   sequences that never draw a conclusion.

Grammar findings follow the same evidence gate: quote the exact
sentence, name the pattern from the catalogue, propose the minimal
rewrite. Do not report style opinions that match no catalogued
pattern; extend the catalogue instead if a genuinely new pattern
recurs three or more times.

### Sweep 5: Figures and tables

For every figure and table:

- **Print legibility**: estimate the smallest text (tick labels,
  legend entries) at final column width; below approximately 6 pt
  effective size is MAJOR. Illegible = unpublishable.
- **Caption self-containedness**: a reader who sees only the float
  and its caption must learn what is shown, on what data, and what
  to notice. Captions that are bare titles ("Results on dataset X.")
  are MAJOR.
- **Cross-reference integrity**, both directions:
  - every figure/table is referenced at least once from the body
    text (an unreferenced float is MAJOR);
  - every `\ref`/`\autoref` resolves to an existing float, and the
    reference's claim matches what the float actually shows
    (a reference pointing at the wrong float is CRITICAL).
- Consistency of notation between floats and body text (same symbol
  names, same units, same baseline names).

## Mode B — Regression re-audit

Mode B exists because revision rounds reintroduce old defects: a
Writer agent regenerates a paragraph and the stale number comes
back; a section is restored from an earlier version and the
anonymization leak returns with it. Never trust a revision to be
monotone improvement.

### Step 1: Disposition of every prior finding

For **each** finding in the previous report, locate the
corresponding text in the revised draft and assign a disposition:

- **FIXED** — the offending text is gone or corrected, and the fix
  did not merely move the defect elsewhere. Quote the replacement
  text as evidence of the fix.
- **UNFIXED** — the offending text survives (identically or
  trivially rephrased with the defect intact). Quote it again from
  the *revised* draft.
- **REGRESSED** — the finding was fixed in an intermediate round
  (per the prior report's own disposition history, if present) and
  the defect is now back, or the "fix" introduced a strictly worse
  variant of the same defect. Quote the regressed text.

No prior finding may be silently dropped. If the surrounding
section was deleted wholesale, disposition is FIXED with note
`section removed`.

### Step 2: Diff-scoped sweep

Run all five Mode A sweeps, but **only over changed material**:
added or modified paragraphs, retitled sections, and any
table/figure whose contents changed — plus, for Sweep 2, every
prose number whose anchoring table changed (a table edit can create
stale numbers in *unchanged* prose, so the number inventory for
changed tables must be reconciled against the whole document).
New findings get fresh IDs; do not renumber prior findings.

### Step 3: Regression table

The Mode B report leads with a regression table:

| prior ID | sweep | severity | disposition | evidence (verbatim, revised draft) |
|---|---|---|---|---|

followed by the new-findings list from Step 2. Any REGRESSED item
is escalated one severity level above its original (CRITICAL stays
CRITICAL) — recurrence proves the fix process is unreliable and the
item needs a structural fix, not another patch.

## Finding schema and JSON output

Every finding, in both modes, is this object:

```json
{
  "id": "A-017",
  "sweep": "numbers",
  "severity": "CRITICAL",
  "location": "Section 1, para 3 / Table 2 row 4",
  "verbatim_quote": "improves accuracy by 4.1 points",
  "trace": "Table 2 reports +3.6 on the same benchmark",
  "fix": "Update the introduction to +3.6, or restore the Table 2 value if 4.1 is the current result."
}
```

`sweep` ∈ {`claims`, `numbers`, `compliance`, `language`,
`figures`}. `severity` ∈ {`CRITICAL`, `MAJOR`, `MINOR`} per the
rulebook. `trace` is required for claims/numbers findings, optional
elsewhere. `fix` is a concrete, minimal edit — never "rewrite this
section".

Top-level report objects:

```json
// Mode A
{
  "mode": "full_audit",
  "draft_id": "<filename or commit>",
  "venue": "<venue name>",
  "summary": {"critical": 3, "major": 11, "minor": 9},
  "verdict": "BLOCK",          // BLOCK if any CRITICAL, else PASS_WITH_FIXES, else PASS
  "findings": [ ... ]
}

// Mode B
{
  "mode": "regression_audit",
  "draft_id": "<revised draft id>",
  "previous_report_id": "<prior report id>",
  "dispositions": [
    {"prior_id": "A-017", "disposition": "REGRESSED",
     "severity": "CRITICAL",
     "evidence": "improves accuracy by 4.1 points",
     "location": "Section 1, para 3"}
  ],
  "regression_summary": {"fixed": 14, "unfixed": 3, "regressed": 2},
  "new_findings": [ ... ],
  "verdict": "BLOCK"           // any UNFIXED/REGRESSED CRITICAL, or new CRITICAL, forces BLOCK
}
```

Emit the JSON verbatim in a fenced block, preceded by a short
human-readable digest: verdict, counts, and the three highest-impact
fixes. The Writer agent consumes the JSON; the digest is for the
human.

## Operating notes

- **Coverage honesty.** If the draft is too long to sweep in one
  pass, chunk it and say so in the digest, listing which sections
  each sweep actually covered. Never imply full coverage you did
  not perform.
- **No invented text.** If a quote cannot be located verbatim in
  the input, the finding is void. This is the whole contract.
- **Don't fix while auditing.** Mode A/B never edits the draft;
  fixes flow through the Writer. Auditing your own edits defeats
  the regression loop.
- **When not to use this skill**: the draft is still being
  structured or written (use a drafting skill first); the user
  wants a scientific-merit opinion (this skill audits execution,
  not the quality of the idea).

## References

- `references/severity-rulebook.md` — the complete computed-severity
  rules per sweep, plus tie-breaking and escalation rules.
- `references/language-patterns.md` — the machine-flavor and grammar
  pattern catalogue with detection cues and rewrite templates.

## Acknowledgments

The pipeline role of this skill — a pre-submission audit whose
findings loop back to a Writer agent — is inspired by HKUSTDial's
Supervisor-Skills project. The audit framework itself (the
sweep-based taxonomy, the regression re-audit mode, the evidence
gate, and the computed-severity rulebook) is an independent
redesign, and all text here is original.
