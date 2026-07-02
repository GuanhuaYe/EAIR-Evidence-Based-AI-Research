# Visual-Form Catalogue

Each form is defined by the **argument shape** it makes, not by its
chart type. Choose the form whose argument shape matches the claim;
then the chart type follows. Every entry lists the annotation that
typically does the arguing — a form deployed without its annotation
usually fails QC rule Q7.

Renderer key: `coder` = figure-coder (data-driven), `artist` =
Artist agent (drawn/schematic), `either` = depends on data density.

---

## contrast-pair

- **Argument shape:** "Without X, this breaks; with X, it doesn't."
- **Claims served:** `problem-exists`, `main-result` (qualitative).
- **Layout:** two panels, identical in every respect except the one
  manipulated variable. Same input, same axes, same scale — the eye
  should diff them instantly.
- **Annotation that argues:** a marker on the exact locus of failure
  in the left panel and its resolution in the right (circle, arrow,
  or red/green tick pair). Never make the reader hunt for the diff.
- **Renderer:** `either` (artist for example-driven pairs, coder for
  output-driven pairs).
- **Fails when:** the two panels differ in more than one variable,
  or the failure is subtle enough to need a paragraph to see.

## mechanism-schematic

- **Argument shape:** "Here is *why* the effect happens."
- **Claims served:** `mechanism`.
- **Layout:** the minimal causal path — inputs, the one component
  that matters, outputs. Everything not on the causal path of the
  claim is compressed or omitted. This is not an architecture
  inventory; boxes that merely exist do not belong.
- **Annotation that argues:** the causal edge is visually heavier
  than all other edges; a callout states what flows along it and
  what would go wrong without it.
- **Renderer:** `artist`.
- **Fails when:** it restates the method section symmetrically (all
  boxes equal weight) — that proves no claim and loses its slot.

## scaling-curve

- **Argument shape:** "The advantage grows (or holds) as Z scales."
- **Claims served:** `main-result`, `generality`.
- **Layout:** metric vs. scale variable (data, parameters, compute,
  problem size), one line per method, log axes when the variable
  spans decades. Seeds/variance shown as bands.
- **Annotation that argues:** the widening (or persistent) gap
  labeled at the rightmost point, and/or the crossover point marked
  where the proposed method overtakes the baseline.
- **Renderer:** `coder`.
- **Fails when:** only two scale points exist (that is a bar chart
  wearing a line costume), or the trend depends on one noisy point.

## ablation-ladder

- **Argument shape:** "Each component earns its keep; here is the
  contribution of each."
- **Claims served:** `ablation`, `mechanism`.
- **Layout:** ordered bars or a waterfall from baseline to full
  method, one rung per added component, sorted so the rungs tell a
  story (biggest contributor visually obvious).
- **Annotation that argues:** the largest single step labeled with
  its delta; the baseline and full-method levels drawn as reference
  lines spanning the ladder.
- **Renderer:** `coder`.
- **Fails when:** components interact so strongly that additive
  rungs are dishonest — use a small ablation table instead and
  spend the slot elsewhere.

## error-anatomy

- **Argument shape:** "The remaining/prior errors are of *this*
  kind — which is exactly what the method targets (or what future
  work must)."
- **Claims served:** `problem-exists`, `mechanism`, honest-limits.
- **Layout:** errors broken down by a meaningful taxonomy (error
  type, input regime, subgroup): stacked/grouped bars, a confusion
  matrix, or a small gallery of failure cases with category labels.
- **Annotation that argues:** the dominant error category
  highlighted, with a callout linking it to the mechanism claim
  ("this is the slice our module addresses").
- **Renderer:** `either`.
- **Fails when:** the taxonomy is post-hoc and unmotivated, or
  categories are too small for the differences to be real.

## budget-frontier

- **Argument shape:** "For any budget (compute, latency, memory,
  labels, dollars), we sit on the frontier."
- **Claims served:** `main-result` + `efficiency` jointly — the
  canonical shared-slot figure.
- **Layout:** quality on one axis, cost on the other, one point (or
  curve) per method; the Pareto frontier traced explicitly. Log the
  cost axis when costs span decades.
- **Annotation that argues:** the frontier line itself, plus an
  arrow or bracket showing the gap at a fixed budget ("same cost,
  +4.2") or fixed quality ("same quality, 3x cheaper").
- **Renderer:** `coder`.
- **Fails when:** cost is measured inconsistently across methods
  (different hardware, different tokenizers) — QC rule Q9 territory.

## distribution-split

- **Argument shape:** "The improvement is not an average artifact —
  the whole distribution moves (or the tail does)."
- **Claims served:** `main-result` robustness, `generality`.
- **Layout:** per-instance metric distributions per method: paired
  CDF/ECDF, violin, or slope-graph of per-instance deltas. The
  right form when means are close but tails differ.
- **Annotation that argues:** the tail region shaded and labeled
  ("worst 10% of cases: gap triples"), or the median lines drawn
  through both distributions.
- **Renderer:** `coder`.
- **Fails when:** n is small enough that the distribution shape is
  noise; report the raw points instead.

## coverage-matrix

- **Argument shape:** "It works across the whole grid of settings,
  not on a cherry-picked cell."
- **Claims served:** `generality`.
- **Layout:** settings x settings heatmap (datasets x metrics,
  domains x model sizes) of the delta vs. baseline; diverging
  colormap centered at zero.
- **Annotation that argues:** the count stated on the figure ("+ in
  23/24 cells"), and any negative cell honestly outlined rather
  than hidden — the outlier acknowledged is more convincing than a
  suspiciously uniform grid.
- **Renderer:** `coder`.
- **Fails when:** cells are not comparable (different scales per
  row) without per-row normalization — normalize or split.

## before-after-trace

- **Argument shape:** "Watch the internal quantity change when the
  mechanism engages."
- **Claims served:** `mechanism` (dynamic evidence).
- **Layout:** an internal signal over time/steps/depth (loss
  component, attention entropy, constraint violation, queue depth),
  with the intervention moment marked, method vs. baseline overlaid.
- **Annotation that argues:** a vertical line at the intervention
  point and a label on the divergence that follows it.
- **Renderer:** `coder`.
- **Fails when:** the trace is from one seed/run and the divergence
  is within run-to-run noise.

## qualitative-strip

- **Argument shape:** "Here is what the numbers look like in the
  world" — makes an already-proven quantitative claim visceral.
- **Claims served:** reinforces `main-result`; never carries it
  alone.
- **Layout:** a single row of examples (input, baseline output,
  ours, reference), sampled by a stated rule (e.g., "median-scoring
  cases"), never hand-picked best cases without saying so.
- **Annotation that argues:** per-example markers on the specific
  artifact/error the baseline commits and the method avoids.
- **Renderer:** `artist` (assembly), with panels from `coder`.
- **Fails when:** used as the *only* evidence for a claim, or when
  the sampling rule is unstated (reviewers assume cherry-picking).

---

## Choosing under a tie

When two forms fit the claim, prefer, in order:

1. the form whose annotation makes the takeaway visible with **zero
   reading** (a marked gap beats a legend lookup),
2. the form that shares a slot with a second claim (frontier over
   plain bars),
3. the form that survives grayscale and single-column width with
   the least redesign.
