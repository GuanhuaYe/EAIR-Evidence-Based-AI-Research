# Banned tokens for venue-aware polishing

Mirrors `pre-submission-reviewer` and `rebuttal-drafter` for
consistency. Stage 2 must strip all of these.

## AI-tone / hype (case-insensitive whole word)

- novel, novelty, first of its kind, paradigm shift, groundbreaking,
  cutting-edge, delve, intricate, multifaceted, seamless,
  state-of-the-art (if not literally an SOTA claim),
  notably, importantly, crucially, intriguingly, remarkably,
  significantly (if unquantified)
- "comprehensive" — allowed only if literally exhaustive
- "robust" / "robustly" — must have a quantitative anchor adjacent
  (within ±10 words) or be deleted

## Em-dash

- `—` (U+2014) — always remove. Replace with `;`, `,`, parens, or
  sentence split based on local syntax.
- `--` LaTeX en-dash and triple-dash variants used for em-dash — same.

## Hedges (per profile — venue family decides)

For `ml-formal` and `db-engineering`, strip from claims:
- may, might, could, possibly, perhaps, somewhat, fairly, rather,
  more or less, to some extent

For `nlp-narrative` and `mining-applied`, allow in analysis but strip
from claim sentences:
- "we believe", "we think", "we hope", "we feel"

For all families, strip:
- "arguably", "in some sense", "in a way", "kind of", "sort of"

## Overclaim / handwave

- obviously, clearly, evidently, trivially, simply, straightforwardly,
  "it is clear that", "naturally"

## Padding

- "in order to" → "to"
- "due to the fact that" → "because"
- "a number of" → "several" or specific count
- "at the present time" → "now" or delete
- "in light of the fact that" → "because"
- "it is worth noting that" → delete
- "as previously mentioned" → delete

## L2-English markers (Chinglish — Stage 4)

See `chinglish_patterns.md` for the full list.

## Quantification mandate

Every comparative adjective ("better", "faster", "more accurate",
"larger") MUST have a number within ±15 words. Stage 2 fails if any
survives without a number.

Exception: limitations and future-work sections may use comparatives
without numbers when explicitly framed as hypotheses.
