# Severity Rulebook

Severities are computed by matching a finding against the rules
below. Rules are deterministic on purpose: the same defect must get
the same severity in every round, or Mode B disposition tracking
becomes meaningless.

General principles:

1. If multiple rules match one finding, the **highest** severity
   wins.
2. A rule may reference occurrence counts; count occurrences over
   the whole document (Mode A) or the changed material (Mode B
   Step 2).
3. In Mode B, any REGRESSED finding is escalated one level above
   its original severity (CRITICAL stays CRITICAL).
4. Nothing outside this rulebook may raise a severity. If a defect
   feels worse than its computed level, propose a rulebook change
   in the digest instead of overriding.

Severity meanings:

- **CRITICAL** — submission-blocking. The verdict is BLOCK while
  any CRITICAL finding is open.
- **MAJOR** — a competent reviewer will likely notice and penalize.
- **MINOR** — polish; fix if time permits.

## Sweep 1: Claims vs. evidence

| Rule | Condition | Severity |
|---|---|---|
| C1 | Claim in abstract/intro with no locatable evidence anchor anywhere in the paper | CRITICAL |
| C2 | Overclaim (verb above evidence tier) on a headline contribution (abstract or contribution list) | CRITICAL |
| C3 | Overclaim on a non-headline claim | MAJOR |
| C4 | Universal-scope quantifier backed by a strict subset of that scope | MAJOR |
| C5 | Underclaim (verb below evidence tier) | MINOR |
| C6 | Claim anchor exists but is in the appendix only, while the claim reads as a main-body result | MAJOR |

## Sweep 2: Numbers

| Rule | Condition | Severity |
|---|---|---|
| N1 | Stale number: prose value disagrees with the current table/figure value | CRITICAL |
| N2 | Wrong derived arithmetic (ratio, percentage, delta) relative to raw table values | CRITICAL |
| N3 | Orphan number in the **abstract** | CRITICAL |
| N4 | Orphan number in intro/conclusion | MAJOR |
| N5 | Condition drift: value matches but dataset/metric/baseline/setting differs from what prose states | MAJOR |
| N6 | Inconsistent precision for the same quantity (e.g., "92.4" and "92.40" for one result) | MINOR |

## Sweep 3: Compliance

| Rule | Condition | Severity |
|---|---|---|
| P1 | Any anonymization leak (acknowledgments/funding section, de-anonymizing self-citation phrasing, identifying URL, PDF metadata, embedded identifying file path) | CRITICAL, always, per occurrence |
| P2 | Over the venue page limit | CRITICAL |
| P3 | Required venue checklist missing, or a checklist answer contradicts the paper body | CRITICAL |
| P4 | Dead citation: unresolved bibkey or `[?]` in the rendered output | MAJOR |
| P5 | Bibliography style inconsistency (mixed formats, arXiv entries for formally published papers) affecting ≥ 3 entries | MAJOR |
| P6 | Bibliography style inconsistency affecting 1–2 entries | MINOR |
| P7 | Within the page limit but only via manual spacing hacks that visibly violate the venue style (negative vspace, shrunken margins) | MAJOR |

## Sweep 4: Language

| Rule | Condition | Severity |
|---|---|---|
| L1 | Machine-flavor pattern (any family in the catalogue) with ≥ 5 occurrences document-wide | MAJOR |
| L2 | Machine-flavor pattern with 1–4 occurrences | MINOR |
| L3 | Grammar fault that inverts or obscures the sentence's technical meaning (dangling modifier attaching to the wrong noun, ambiguous pronoun over two possible antecedents in a claim sentence) | MAJOR |
| L4 | Grammar fault that is noticeable but meaning-preserving | MINOR |
| L5 | Any single sentence exhibiting ≥ 3 catalogued patterns simultaneously | MAJOR |
| L6 | Machine-flavor pattern occurring in the abstract | one level above its count-based severity (MINOR→MAJOR; MAJOR stays MAJOR) |

## Sweep 5: Figures and tables

| Rule | Condition | Severity |
|---|---|---|
| F1 | Cross-reference resolves to the wrong float, or the body text's description contradicts what the float shows | CRITICAL |
| F2 | Unresolved float reference (`??` in rendered output) | CRITICAL |
| F3 | Float never referenced from the body text | MAJOR |
| F4 | Smallest text in a figure below ~6 pt at final print size | MAJOR |
| F5 | Caption is a bare title (does not state data shown and what to notice) | MAJOR |
| F6 | Notation/units/baseline-name mismatch between a float and the body text | MAJOR |
| F7 | Cosmetic inconsistency across floats (fonts, capitalization of headers, decimal alignment) | MINOR |

## Verdict computation

- `BLOCK` — at least one open CRITICAL finding (Mode A), or any
  CRITICAL that is UNFIXED/REGRESSED or newly found (Mode B).
- `PASS_WITH_FIXES` — no CRITICAL, at least one MAJOR.
- `PASS` — MINOR findings only, or none.
