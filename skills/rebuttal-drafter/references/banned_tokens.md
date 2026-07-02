# Banned tokens in rebuttal prose

This list mirrors `pre-submission-reviewer` plus rebuttal-specific
additions. Tokens are matched case-insensitively as whole words unless
otherwise noted. Stage 3 must fail if any survives.

## AI-tone / hype (shared with paper)
- novel, novelty, first of its kind, paradigm shift, groundbreaking,
  cutting-edge, state-of-the-art (if not literally an SOTA claim),
  delve, intricate, multifaceted, comprehensive (if not literally
  exhaustive), seamless, robustly (if unquantified), notably,
  importantly, crucially, intriguingly

## Hedge tokens (rebuttal-specific — never hedge under reviewer pressure)
- we believe, we think, we hope, we feel, it is our hope,
  arguably, perhaps, possibly, maybe, somewhat, fairly, rather,
  more or less, to some extent, in some sense

## Overclaim / handwave
- obviously, clearly, evidently, it is clear that, trivially,
  straightforwardly, naturally, simply

## Defensive / antagonistic
- the reviewer is incorrect, the reviewer misunderstood,
  the reviewer fails to, this comment is unfair, this is not a
  valid criticism, we strongly disagree

Acceptable: "We respectfully clarify that ...", "We note that ...",
"To address this, ...", "The reviewer raises a fair point about X;
however, ..."

## Format
- em-dash (—). Replace with semicolon, comma, or parentheses.
- "etc." in technical defenses (be specific or drop).

## Lexicon for concession openings (vetted)

Pick one per MAJOR-DEFEND row; do not reuse the same opener twice per
reviewer.

- "We agree that X is an important concern."
- "The reviewer correctly notes X; we now ..."
- "We thank the reviewer for raising X. To address this, ..."
- "X is a fair point. We have ..."
- "We acknowledge the limitation around X. Our justification is ..."

## Quantification mandate

Every "improved", "better", "faster", "more accurate" MUST have a
number attached. If no number exists in the paper or run logs, the
sentence must be rewritten or deleted. The skill should reject prose
that contains comparative adjectives without adjacent numerics
(within ±15 words).
