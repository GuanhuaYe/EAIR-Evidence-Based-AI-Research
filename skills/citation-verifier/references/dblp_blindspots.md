# DBLP blindspots — venues to suppress LIKELY-HALLUCINATED for

DBLP indexes most CCF venues, but some legitimate publication
channels are not in DBLP or are indexed late. Treat papers in these
channels as "exists" if Semantic Scholar OR arXiv confirms them,
even when DBLP returns nothing.

## Workshops at major venues

- NeurIPS workshops (most years)
- ICML workshops (most years)
- ICLR workshops (some indexed, many not)
- ACL workshops (BlackBoxNLP, REPL4NLP, etc.)
- Some EMNLP workshops

## OpenReview-only venues

- TMLR (Transactions on Machine Learning Research)
- Some MLSys workshop papers
- Some ACL ARR-rejected-but-cited papers

## Recent papers (DBLP lag)

DBLP can lag by 1-3 months for some venues. If a 2025-2026 paper is
not in DBLP but is on Semantic Scholar with a known venue name,
treat as `RECENT-DBLP-LAG` not LIKELY-HALLUCINATED.

## Industry / arXiv-only foundational works

- Most foundation model technical reports (GPT-4 system card, Claude
  technical reports, Gemini reports, etc.) are arXiv-only or company
  reports. Use `@misc` with URL, no venue claim. Skip Stage 2 claim
  support (no abstract on DBLP).

## Suppression rule

If a bibtex entry's venue field matches any of the blindspot patterns
above, AND the paper is found on Semantic Scholar OR arXiv:
- Stage 1: do not flag LIKELY-HALLUCINATED.
- Stage 1: flag DBLP-MISSING-NORMAL (informational, not blocker).
- Stage 2: still run claim-support against SS abstract.
