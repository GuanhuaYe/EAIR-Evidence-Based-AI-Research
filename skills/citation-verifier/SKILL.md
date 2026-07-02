---
name: citation-verifier
description: >-
  Verifies that every \cite{} in a paper draft is (a) a real
  publication with a canonical bibtex entry, and (b) actually
  supports the in-text claim that cites it. Cross-checks bibtex
  against DBLP / Semantic Scholar / arXiv, normalizes keys to a
  consistent scheme, and flags hallucinated citations, wrong
  attributions, and overclaim ("X et al. showed Y" when X only
  claimed weaker Y'). Use when the user says 'verify citations',
  'check references', 'audit bibtex', 'do these cites exist', 'is
  this citation real', or before a submission deadline.
license: CC-BY-4.0
---

# Citation Verifier

## Overview

Fabricated and misattributed citations are a known reviewer kill at
top venues. LLM-assisted writing has made this risk worse — a
plausible-sounding "Smith et al. 2023 showed that ..." can be entirely
hallucinated, or attached to a real paper that does not actually make
the claim. This skill runs two independent passes: a bibtex verification
pass and a claim-support pass.

## When to invoke

- After any LLM-assisted section drafting (Writer agent, intro-drafter,
  rebuttal-drafter that introduces new cites).
- 1-2 weeks before a submission deadline as a standalone audit.
- When user says "verify citations", "audit references", "do these
  cites exist", "check the bibtex".

Do NOT invoke for venue-formatting checks (use `pre-submission-reviewer`)
or for selecting which papers to cite (that is a literature-search task,
outside this skill's scope).

## Operating procedure

### Stage 0 — Inputs

Required:
- LaTeX source directory (default: `<paper>/latex/`)
- Bibtex file(s) (default: glob `<paper>/latex/*.bib`)
- Optional: paper PDFs or arXiv IDs for cited works, used in Stage 2.

Detect via:
```bash
grep -rho '\\cite[ptn]\?{[^}]*}' <paper>/latex/ | sort -u
```

### Stage 1 — Bibtex verification pass (control host, no GPU)

For every `@inproceedings` / `@article` / `@misc` entry, verify:

1. **Existence**: query DBLP or Semantic Scholar for the title.
   - DBLP API: `https://dblp.org/search/publ/api?q={title}&format=json&h=3`
   - Semantic Scholar API: `https://api.semanticscholar.org/graph/v1/paper/search?query={title}`
   - If no match within Levenshtein ≤5 of the bibtex title → flag as
     LIKELY-HALLUCINATED.

2. **Author/venue/year consistency**: compare bibtex author/venue/year
   against the matched DBLP/SS record.
   - Flag mismatches: AUTHOR-MISMATCH, VENUE-MISMATCH, YEAR-MISMATCH.

3. **arXiv normalization**: if bibtex points to arXiv but a published
   venue version exists (DBLP found it), prefer the venue version.
   Flag PREFER-VENUE-VERSION.

4. **Key scheme**: normalize to `lastname{Year}{firstword}` (configurable
   in `references/key_scheme.md`). Flag KEY-NONCONFORMANT and produce
   a rename map.

5. **Duplicates**: flag any two entries that resolve to the same DBLP/SS
   record. Produce a merge plan.

Output: `bibtex_audit.json` with one row per bibtex entry.

### Stage 2 — Claim-support pass (selective, more expensive)

For each `\cite{}` in the text, extract the claim sentence and verify
the cited paper actually supports it. Two tiers:

**Tier A — Fast (default)**: use the cited paper's abstract from DBLP/SS.
- Extract the in-text claim (the sentence containing the cite, plus
  the previous sentence for context).
- Compare against abstract. Three possible labels:
  - `SUPPORTED`: claim is in the abstract or a clear implication
  - `WEAKER-THAN-CITED`: the paper claims something weaker than the
    in-text sentence asserts (common overclaim)
  - `NOT-IN-ABSTRACT`: claim is not in abstract; need Tier B
- Flag SUPPORTED-MAYBE if Tier A returns NOT-IN-ABSTRACT but the
  claim is a methodological detail that might be in the body.

**Tier B — Deep (opt-in, slower)**: fetch the full PDF, run a
keyword search for the claim's load-bearing nouns, return the
matching passages. Use this only for high-stakes cites (intro
contributions, related-work differentiators, theorem citations).

Identifying high-stakes cites:
- Cites in §1 (intro)
- Cites in claim sentences with comparative words: "first", "best",
  "showed", "proved", "demonstrates", "outperforms"
- Cites in theorem statements, proof preludes, or assumption
  declarations

Output: `claim_support.json` with one row per cite occurrence (not
per bibtex entry, since same key can be cited differently).

### Stage 3 — Report

Synthesize Stage 1 + Stage 2 into a single Markdown audit:

```
# Citation audit — {paper}

## SUMMARY
- Total cites: N
- LIKELY-HALLUCINATED: K (BLOCKER if K>0)
- WEAKER-THAN-CITED: K (MAJOR if K>0)
- AUTHOR/VENUE/YEAR mismatches: K (MAJOR)
- Other format issues: K (MINOR)

## BLOCKERS
{LIKELY-HALLUCINATED rows, full evidence}

## MAJOR
{WEAKER-THAN-CITED + mismatches, with suggested rewrites or
alternative cites}

## MINOR
{key renames, format issues}

## DELIVERABLES
- bibtex_audit.json
- claim_support.json
- bibtex_renames.sh (optional, if KEY-NONCONFORMANT rows exist)
- bibtex_dedup.sh (optional, if duplicates exist)
```

## Network access

- All API calls run on the control host (CLAUDE-side). DBLP and Semantic Scholar
  are accessible from the control host; do NOT route through gpu-host
  (its outbound network access may be restricted).
- Use `curl` with `--max-time 10`, single-threaded (be polite to DBLP).
- Cache responses in `<paper>/.citation_cache/` keyed by query hash.

## Rate limits

- DBLP: ~1 req/sec sustained, no key needed.
- Semantic Scholar: ~1 req/sec without key, higher with API key. If
  user provides `$S2_API_KEY` env var, use it.
- arXiv: no formal rate limit but ~1 req/3sec polite.

## Cross-skill interactions

- Writer agent / `intro-drafter` / `rebuttal-drafter` — invoke
  citation-verifier on any newly drafted section before merging.
- `pre-submission-reviewer` — citation-verifier is a prerequisite;
  pre-submission-reviewer assumes citations are clean.
- `reviewer-panel` — R1/R3 will flag bad cites during simulation;
  run citation-verifier before panel.
- Local literature KB (if you maintain one) — if a cite is
  LIKELY-HALLUCINATED but the user wants to cite something in that
  area, query your KB or Semantic Scholar for a real alternative.

## Failure modes and overrides

- **Pre-print only**: some valid cites are arXiv-only, not in DBLP.
  Mark `--allow-arxiv-only` to suppress the PREFER-VENUE-VERSION flag.
- **Workshop / non-DBLP venues**: some valid venues (e.g., NeurIPS
  workshops, OpenReview-only) may not be in DBLP. Maintain
  `references/dblp_blindspots.md` and suppress flags for those.
- **Misc cite of a tool / dataset**: `@misc` entries for software or
  datasets do not need claim-support. Skip Stage 2 for `@misc`.

## References

- `references/key_scheme.md` — canonical bibtex key format and
  override rules
- `references/dblp_blindspots.md` — venues not indexed by DBLP,
  to suppress false LIKELY-HALLUCINATED flags
- `references/overclaim_patterns.md` — common overclaim phrases
  ("first to", "proved", "demonstrated") with weaker-than-cited
  examples
