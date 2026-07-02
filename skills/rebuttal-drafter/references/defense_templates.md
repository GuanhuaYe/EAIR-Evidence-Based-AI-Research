# Defense templates — concession-objection-evidence

Templates are scaffolds, not fill-in-the-blanks. Adapt every clause
to the actual concern; never paste verbatim.

## Template A — Methodology objection with paper evidence

```
We agree that {short concession of the surface point — ≤15 words}.
However, {refutation in one clause, citing evidence}: see {§X.Y / 
Table N / Figure N / Appendix Z}, which shows {quantified result, 
e.g., +X.X% over baseline B with std σ}.
Additionally, {one secondary support if budget allows}.
```

Length: 60-90 words. Use for severity-3 MAJOR-DEFEND.

## Template B — Methodology objection requiring new evidence

```
The reviewer's concern about {X} is well-taken. To address it
directly, we ran {one new experiment, described in ≤20 words}.
Results: {number ± std} on {dataset}, indicating {one-line interpretation}.
The full ablation is in {appendix/new section} of the revised PDF.
```

Length: 50-80 words. Use ONLY when NEW-EXPERIMENT has landed.
Never use this template with placeholders; if the run is not done,
move the row to Stage 5 backlog.

## Template C — Misunderstanding

```
We respectfully clarify {what the reviewer read} vs {what the paper
actually claims}. Specifically, {quote ≤8 words from paper} (§X.Y,
line N) means {disambiguation}, not {what the reviewer assumed}.
We will reword §X.Y in the camera-ready to make this explicit.
```

Length: 40-70 words. Use for MAJOR-MISUNDERSTANDING.
End with a concrete commitment to rewording — this is rewarded by
reviewers.

## Template D — Minor acknowledgment (bullet form)

```
- {R-id} Typo on line N: fixed.
- {R-id} Missing citation [Smith 2024]: added in §X.
- {R-id} Clarify notation σ_t vs σ^t: revised in §3.
```

≤20 words per bullet. Group all MINOR-ACK rows under a single
"Minor revisions" heading at the end of the per-reviewer response.

## Template E — Out-of-scope, polite refusal

```
{X} is an interesting direction beyond this paper's stated scope
of {one-line scope re-anchor}. We have added a forward-pointer in
§Discussion §N.N noting this as future work, and a one-paragraph
discussion of {why orthogonal, in 1 clause}.
```

Length: 30-50 words. ≤1 per reviewer. If you have more than one
OUT-OF-SCOPE per reviewer, you are mis-classifying — at least one
is actually MAJOR-DEFEND.

## Common-response template (CVPR family)

```
We thank all reviewers for their constructive feedback. Three
concerns appeared across reviewers and we address them here.

**C1 ({concern title}).** {Template A or B body, ≤120 words.}

**C2 ({concern title}).** {body}

**C3 ({concern title}).** {body}

Per-reviewer responses below address remaining individual concerns.
```

Length: ≤1 page (~600 words). Use only for shared concerns; do NOT
duplicate per-reviewer prose here.

## Revision-letter template (SIGMOD/VLDB)

```
# Response to {Editor / Shepherd}

We thank the reviewers for {one-line acknowledgment}. The major
revisions, summarized by reviewer concern, are:

| Concern | Reviewer | Revised section | Change summary |
|---|---|---|---|
| {C1} | R1 | §X | {≤15 words} |
| ... |

## Reviewer 1

### R1.1 {short title}
> {≤30 words quoted concern}

{Response body using Template A/B/C as appropriate, with explicit
pointer to revised PDF page/section/line.}

### R1.2 {short title}
...
```

Letter-style is verbose by design — reviewers want to see every
concern individually addressed with a paper pointer. Budget per
concern: 100-300 words.
