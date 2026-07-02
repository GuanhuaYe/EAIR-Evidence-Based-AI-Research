# Rating scales and decision lexicon per CCF A venue

Confirm against current call for papers — venues update their scales
year-to-year.

## AI venues

### NeurIPS (1-10, ICLR-style)
| Score | Label |
|---|---|
| 10 | Top 5% of accepted papers |
| 8-9 | Top 50% of accepted papers (strong accept) |
| 6-7 | Marginally above acceptance threshold |
| 5 | Borderline / marginally below threshold |
| 3-4 | Reject (technical/empirical flaws) |
| 1-2 | Strong reject / desk reject |

Typical accept threshold: mean ≥6, no individual <4.
Confidence: 1-5 (1 = "you can question my evaluation"; 5 = "absolutely certain").

### ICML — same as NeurIPS 1-10 in practice
### ICLR — same as NeurIPS 1-10 in practice; uses OpenReview

### AAAI (1-7)
| Score | Label |
|---|---|
| 7 | Strong accept |
| 6 | Accept |
| 5 | Weak accept |
| 4 | Borderline |
| 3 | Weak reject |
| 2 | Reject |
| 1 | Strong reject |

### IJCAI (1-10) — similar to NeurIPS scale

### ACL/EMNLP/NAACL (Overall 1-5, plus Soundness 1-5)
| Score | Label |
|---|---|
| 5 | Best paper |
| 4 | Award level / strong accept |
| 3.5 | Recommend for acceptance |
| 3 | Borderline |
| 2.5 | Borderline lean reject |
| 2 | Reject |
| 1 | Strong reject |

ARR uses two axes: Overall and Soundness (1-5 each).

## CV venues

### CVPR/ICCV/ECCV (1-6 typical)
| Score | Label |
|---|---|
| 6 | Strong accept |
| 5 | Accept |
| 4 | Weak accept / borderline |
| 3 | Weak reject |
| 2 | Reject |
| 1 | Strong reject |

### ACM MM (1-5)
| 5 | Strong accept |
| 4 | Accept |
| 3 | Borderline |
| 2 | Reject |
| 1 | Strong reject |

## DB / Data venues

### SIGMOD (Research Track) — categorical decision
Categorical, not 1-N. Decisions:
- Accept (camera-ready as is)
- Accept with shepherd
- Minor revision
- Major revision (revise-and-resubmit)
- Reject

Reviewers also score on axes: technical merit, novelty, presentation,
reproducibility — typically 1-5 each, but the categorical decision
dominates.

### VLDB — rolling revision model
- Accept
- Minor revision
- Major revision (resubmit within N months)
- Reject

Similar axis scores as SIGMOD.

### ICDE — 1-7 typical
| 7 | Strong accept |
| 6 | Accept |
| 5 | Weak accept |
| 4 | Borderline |
| 3 | Weak reject |
| 2 | Reject |
| 1 | Strong reject |

## Information / Mining venues

### KDD (1-5)
| 5 | Strong accept |
| 4 | Accept |
| 3 | Borderline |
| 2 | Reject |
| 1 | Strong reject |

### SIGIR (1-5) — same shape as KDD
### WWW (1-5) — same shape as KDD

## Acceptance rates (approximate, recent cycles)

| Venue | Accept rate |
|---|---|
| NeurIPS | ~26% |
| ICML | ~28% |
| ICLR | ~32% |
| ACL/EMNLP | ~22% main, ~30% findings |
| CVPR | ~25% |
| ICCV/ECCV | ~25% |
| AAAI | ~23% |
| IJCAI | ~14% |
| SIGMOD | ~18% |
| VLDB | ~25% (over rolling cycle) |
| ICDE | ~20% |
| KDD | ~18% |
| SIGIR | ~20% |
| WWW | ~17% |
| ACM MM | ~25% |

AC must use these rates when calibrating. A panel mean that places
the paper outside the top-K% by score should not recommend ACCEPT.

## Decision lexicon (AC must use exactly)

OpenReview / discussion venues:
- "Accept (oral)", "Accept (spotlight)", "Accept (poster)",
  "Reject", "Withdraw recommended"

CMT venues:
- "Strong accept", "Accept", "Weak accept", "Borderline",
  "Weak reject", "Reject", "Strong reject"

SIGMOD/VLDB:
- "Accept", "Accept with shepherd", "Minor revision",
  "Major revision", "Reject"
