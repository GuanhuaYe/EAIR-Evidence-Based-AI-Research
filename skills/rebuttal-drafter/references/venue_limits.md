# Rebuttal/Response Hard Limits per Venue

These are the **author-response budgets** for the rebuttal/discussion
phase. Confirm against the current call for papers — limits drift
year-to-year. Last verified for 2025-2026 cycles where noted; otherwise
treat as a planning baseline and ask the user to verify.

| Venue | Format | Per-reviewer cap | Total cap | Common response | Notes |
|---|---|---|---|---|---|
| NeurIPS | OpenReview comments | ~6000 chars/reviewer | — | None official | Multi-turn discussion encouraged |
| ICML | OpenReview comments | ~5000 chars/reviewer | — | None official | Same as NeurIPS in practice |
| ICLR | OpenReview comments | ~5000 chars/reviewer | — | None official | Multi-turn discussion is the norm |
| ACL/EMNLP/NAACL | Single response PDF/text | — | ~1000 words | — | ARR cycle: single response, all reviewers |
| AAAI | CMT/single PDF | — | 1 page | Optional | Often 1 column / 1 page |
| IJCAI | Single response | — | ~1000 words | — | One round |
| CVPR/ICCV/ECCV | CMT, per-reviewer + common | ~3500 chars/reviewer | — | ≤1 page | Common response shared across reviewers |
| ACM MM | Single text | — | ~2 pages | Optional | One round |
| SIGMOD/VLDB | Revision letter (post-decision) | — | No hard cap (be terse) | N/A | Letter + revised PDF; expect 5-15 pages of letter |
| ICDE | Same as SIGMOD | — | No hard cap | N/A | Letter style |
| KDD | Single response | — | ~1 page / ~600 words | — | One round |
| SIGIR | Single response | — | ~1 page | — | One round |
| WWW | Single response | — | ~1 page | — | One round |

## Discussion-style venues (OpenReview)

NeurIPS/ICML/ICLR allow multi-turn discussion. Strategy:
1. First comment: full triage response per Stage 4.
2. Reserve ~30% of budget for follow-up after reviewers reply.
3. If a reviewer raises a NEW concern in follow-up, treat it as a new
   row and re-triage. Do NOT defend reflexively in the same turn.

## Revision-letter venues (SIGMOD/VLDB/ICDE)

These come AFTER a "revise" decision, not in a rebuttal window.
Format:
- Top: summary table mapping reviewer concern → revised section/page.
- Body: per reviewer, full quote → response → pointer to revised
  passage in the revised PDF (highlight changes).
- No hard char cap, but reviewers reward concise letters. Target
  6-12 pages of letter for a typical revise round.

## NEW-EXPERIMENT feasibility windows

| Venue | Rebuttal window | Realistic experiment budget |
|---|---|---|
| NeurIPS/ICML/ICLR | 7-14 days | 1-2 GPU-week, can do new ablations |
| ACL/EMNLP/NAACL (ARR) | 14-21 days | 1 GPU-week |
| CVPR/ICCV/ECCV | 5-7 days | <1 GPU-week, mostly re-runs |
| SIGMOD/VLDB | months | full re-experiments OK |

If user requests a NEW-EXPERIMENT that exceeds the window, refuse and
recommend a written-defense alternative.
