# one-loop: the core research loop in five minutes

A fully offline, deterministic demo (python3 stdlib only, fixed seeds) of the
loop this repo runs at scale: **hypothesis → preregistered rule → bundle →
adversarial audit → fix → mechanical verdict → knowledge-tree update.**

Toy question: *does majority voting over k=15 noisy classifiers beat a single
classifier?* The simulator plants a twist — on 72% of questions the wrong
answers cluster on the same distractor (systematic errors), which caps what
voting can fix. And the harness ships with a planted bug for the audit to catch.

## Step 0 — read the hypothesis and the frozen rule

```
cat hypothesis.json
cat prereg.json
```

`hypothesis.json` is a knowledge-tree node: falsifiable form, kill criteria,
`"status": "OPEN"`. `prereg.json` was frozen *before* the experiment code was
written: PROVEN needs delta ≥ 3pp **and** bootstrap CI95 excluding 0, with a
positive control at exactly 100% and a negative control at chance. Nobody gets
to renegotiate these numbers after seeing results.

## Step 1 — run the bundle

```
python3 run_bundle.py
```

Expected output:

```
  treatment_vote15    67.00%
  baseline_single     61.16%
  ...
  delta (vote@15 - single) = +5.84pp, CI95 [+1.78, +9.64]pp
  ties: 19 questions decided by tie-break (19 contained gold)
```

**What just happened:** one BUNDLE, five arms, same 300 questions and same
seeds: treatment (vote@15), baseline (single sampler), ablation (vote@5),
negative control (shuffled labels → must be ~chance), positive control
(noiseless samplers → must be exactly 100%). Delta +5.84pp clears the 3pp bar
with CI excluding 0. Looks PROVEN. (Note the ablation *beating* vote@15: with
correlated errors, more voters converge more reliably on the same wrong answer.)

## Step 2 — try to cash it in early

```
python3 verdict.py
```

You get a wall of `!!!` warnings — no audited `results_v2.json` exists — then,
advisory only: `VERDICT: PROVEN`. **What just happened:** the verdict is
mechanical, but the protocol says unaudited results cannot be acted on. The
knowledge tree records a PROVEN entry flagged `"audited": false`.

## Step 3 — the adversarial audit lands

```
cat audit_round1.md
```

**What just happened:** a different-model auditor read the harness code, not
the numbers. It found that plurality ties are broken by *lexicographically
smallest answer id* — and the generator encodes gold as `opt0`, which always
sorts first. 19/19 ties went to gold (fair expectation ≈ 9.5, p ≈ 2e-6). Its
reversal test: flipping the tie-break alone swings the treatment arm from
67.00% to 60.67% — more than the whole 3pp decision margin. **FAIL, CRITICAL.**

## Step 4 — apply the required fix and rerun

```
python3 run_bundle.py --fixed
```

Expected output:

```
  treatment_vote15    64.00%
  ...
  delta (vote@15 - single) = +2.84pp, CI95 [-0.96, +6.73]pp
```

**What just happened:** same data, same seeds, one change — ties now resolve
by seeded random choice among the tied answers. Ten of the 19 ties go to gold
instead of 19. Three points of "effect" evaporate; they were scoring leakage,
not voting.

## Step 5 — the mechanical verdict

```
python3 verdict.py
```

```
VERDICT: INSUFFICIENT   (hypothesis H001, file results_v2.json, ...)
rationale: delta +2.84pp is below the preregistered 3pp margin and CI95
[-0.96, +6.73]pp includes 0
```

**What just happened:** `verdict.py` prefers the audited `results_v2.json`,
applies the frozen rule, and prints the only verdict the numbers permit. No
discussion, no "but it's still positive".

## Step 6 — the knowledge tree remembers

`cat hypothesis.json` — status is now `INSUFFICIENT`, and `history` holds both
entries, the unaudited PROVEN and the audited INSUFFICIENT. Both stay in the
record permanently.

## Takeaways

+5.84pp with a clean CI, passing controls, deterministic seeds — this would
sail into most papers. It was wrong, and *nothing in the results could show
that*: the controls pass because the leak only fires on ties, which noiseless
and shuffled-label arms never exercise decisively. Only reading the code
adversarially caught it.

Preregistration is what made the ending mechanical. Because "≥ 3pp AND CI
excludes 0" was frozen before any code ran, the buggy run is PROVEN and the
fixed run is INSUFFICIENT *by rule* — no room to argue that +2.84pp "basically
counts". The bundle did its part too: the positive control certifies the
scorer, the negative control bounds ordinary label leakage, and the odd
vote@5 > vote@15 ablation flagged the correlated-error structure. H001 stays
alive but unproven; its kill criteria already say what happens next.
