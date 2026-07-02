# Power-Trap Catalog

Evidence-economics failure patterns for Axis E of Kill-Cheap Triage.
Each entry: the pattern, how to detect it from the idea document alone,
and the repair a RESHAPE directive should name. Raise the `POWER-TRAP`
flag when a pattern matches; raise `UNDERPOWERED` when the numeric MDE
comparison fails regardless of pattern.

## Quick MDE arithmetic (use these, write the numbers down)

- **Accuracy-type metric, single system:** standard error ≈
  sqrt(p(1-p)/n). At p≈0.5, n=100 → SE ≈ 5 points; n=1,000 → ≈ 1.6;
  n=10,000 → ≈ 0.5. A two-system *paired* comparison does better than
  2×SE (item pairing cancels shared variance), but only if the idea
  actually plans paired evaluation — check.
- **AUROC:** with n_pos positives and n_neg negatives, the standard
  error is dominated by min(n_pos, n_neg). Fewer than ~50 minority-class
  items makes AUROC differences under ~0.05 unresolvable. Fewer than
  ~20 makes the headline number essentially a coin-flip decoration.
- **Training-run comparisons:** seed-to-seed variance on modern
  fine-tuning setups is routinely 0.5–2 points on the final metric.
  A claimed gain must exceed the seed spread; the seed spread cannot be
  known from one seed.

## The traps

### T1 — Small-n AUROC / accuracy headline

**Pattern:** the decisive claim is an AUROC or accuracy figure computed
on double-digit n (e.g. "our probe achieves 0.91 AUROC" on 50 examples).
These numbers collapse toward chance when the test set grows, because
the small sample sat in a lucky region of item space.
**Detect:** any headline classification metric where the document's own
numbers imply n < ~200, or where n is conspicuously unstated.
**Repair:** name the specific larger evaluation set (a full public
split, not "more data") and recompute the MDE at its size.

### T2 — Seed count of one

**Pattern:** "method beats baseline by 1.2 points" from one training run
per side. The difference is inside typical seed variance; the sign can
flip on rerun.
**Detect:** any training-based comparison whose budget arithmetic only
affords one run per condition.
**Repair:** either 3+ seeds per condition (recompute budget), or switch
the kill experiment to a no-training probe where seed variance does not
apply.

### T3 — Headline moved by one item

**Pattern:** the test set is small enough that relabeling or dropping a
single item changes the reported number by more than the claimed margin.
Common in hand-curated "hard subsets" of 20–100 items.
**Detect:** claimed margin (in points) < 100/n for accuracy-type
metrics.
**Repair:** grow n until one item moves the metric by less than a fifth
of the claimed margin, or state the claim at coarser granularity
("majority of categories improve") that the n can support.

### T4 — Subgroup fishing

**Pattern:** the effect only appears in a subgroup discovered *after*
looking at results ("on multi-hop questions specifically, we gain 6
points"). With k subgroups inspected, the effective false-positive rate
multiplies by k.
**Detect:** the idea's motivating evidence is a subgroup result and the
document does not say the subgroup was chosen in advance.
**Repair:** preregister the subgroup in the kill experiment's
`kill_condition`, and require the effect on a *fresh* sample of that
subgroup.

### T5 — Ceiling/floor compression

**Pattern:** baseline sits at 95%+ (or under 5%), so the remaining
headroom is smaller than the measurement noise; any "gain" is
unresolvable and any "gap" is saturation artifact.
**Detect:** baseline metric within ~2×SE of the metric's boundary.
**Repair:** move to a harder split or a metric with headroom; if none
exists, the claim class is really *analysis* ("task X is saturated"),
which re-triggers the Axis C floor check.

### T6 — Correlated evaluation units

**Pattern:** n looks large but units share provenance — 1,000 questions
generated from 40 documents, 500 outputs from 10 prompts × 50
paraphrases. Effective n is closer to the source count; the naive SE is
optimistic by a factor of sqrt(cluster size).
**Detect:** the data-construction sentence mentions expansion,
paraphrasing, templating, or per-document question generation.
**Repair:** compute MDE at the cluster count, not the item count; or
diversify sources until cluster count ≈ item count.

### T7 — Budget mirage

**Pattern:** the envelope technically covers the *first* experiment but
not the comparisons reviewers will demand (baselines, ablations, second
dataset), so the idea ships underpowered by construction even if the
pilot passes.
**Detect:** budget arithmetic covers < 3× the kill experiment's cost.
**Repair:** either shrink the claim to what the budget can defend, or
flag `BUDGET-SHORTFALL` and let the verdict table decide.

## Reporting

For every matched trap, the triage output must state: trap ID, the
sentence or number in the idea document that triggered detection, the
arithmetic (one line), and the repair. A trap match without the
arithmetic is a vibe, and vibes are banned.
