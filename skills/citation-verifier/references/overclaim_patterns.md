# Overclaim patterns — Stage 2 high-priority flags

These patterns appear in claim sentences that frequently overclaim
the cited paper's actual contribution. Stage 2 should run Tier B
(full-PDF check) on any sentence matching these patterns, not just
Tier A (abstract check).

## Strength overclaims

| In-text phrase | Reality check |
|---|---|
| "[X] proved that ..." | Did X actually have a proof, or only empirical evidence? |
| "[X] showed that ..." (in theorem context) | Same — proof vs evidence |
| "[X] demonstrates that ..." | Demonstrate = empirical, not formal — but check direction |
| "[X] first ..." | Was X actually first, or were there prior works in the same year/earlier? |
| "[X] is the first ..." | Same |
| "[X] established ..." | Strong claim — check if X's paper actually establishes the relation |
| "[X] introduced ..." | Often correct but check; some "introduced" claims belong to earlier prior art |

## Direction reversals

| In-text phrase | Common error |
|---|---|
| "[X] outperforms [Y]" | Direction can be flipped if author confused which paper is which |
| "[X] is superior to [Y]" | Same |
| "[X] generalizes [Y]" | Check generalization direction; often the opposite |
| "[X] extends [Y]" | Same |

## Scope inflation

| In-text phrase | Common error |
|---|---|
| "[X] for all ..." | X may only apply in specific setting |
| "[X] in general ..." | Same |
| "[X] across domains ..." | X may have been evaluated on one domain only |
| "[X] always ..." | Almost never "always" — check qualifiers |

## Time / venue inflation

| In-text phrase | Common error |
|---|---|
| "recent work [X]" | "Recent" should be within ~2 years of submission; flag if >3 years old |
| "[X] (NeurIPS 2023)" inline | Check venue field on bibtex matches |

## Recommended Tier-B action

For every Stage 2 match of the above patterns, fetch the cited paper's
introduction + conclusion, run a keyword search for:
- The load-bearing verb's noun ("proved" → "Theorem", "Lemma")
- The comparison target ("[Y]" or its name)
- The scope qualifier ("all", "general", "always" → look for the
  paper's stated scope)

Return matching passages so the user can manually verify.
