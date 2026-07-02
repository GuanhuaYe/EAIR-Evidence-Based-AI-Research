---
name: figure-designer
description: >-
  Plans a paper's figures as an information budget spent against its
  claims. Models the reviewer's 3-minute scan pass, forces a written
  10-second takeaway per figure before anything is drawn, allocates
  the venue-typical figure budget by marginal information per claim,
  and emits one machine-readable design spec per figure for
  downstream rendering (figure-coder for plots, an Artist agent for
  schematics), plus a computed severity-tagged QC gate. Use when
  deciding what figures a paper needs, how many, what each must show,
  or when auditing an existing figure plan against the paper's claims.
license: CC-BY-4.0
---

# Figure Designer — the Figure Information Budget

## Overview

Figures are not decoration; they are the highest-bandwidth channel a
paper has during the only reading most reviewers ever give it: a
single scan pass. This skill treats the figure set as a **budget** —
a small, fixed number of slots — to be **spent against the paper's
claims**, and refuses to design any figure that cannot state, in one
sentence written in advance, what a reader must take away from it in
ten seconds.

The output is not prose advice. It is:

1. a **budget table** mapping claims to figure slots,
2. one **structured JSON design spec per figure**, consumed by the
   `figure-coder` skill (data plots) or an Artist agent (schematics),
3. a **QC gate report**: a checklist computed rule-by-rule, each
   finding tagged with a severity.

## The reviewer scan model

Assume the marginal reviewer gives the paper one 3-minute pass:
title, then abstract, then **every figure in order**, then the
tables. Body text is consulted only to resolve confusion the figures
created. Two consequences drive everything below:

- **The 10-second test.** Within the scan, each figure gets roughly
  ten seconds of attention. Before a figure is designed, write down
  the one takeaway a reader must extract in those ten seconds. If
  the takeaway cannot be stated in a single declarative sentence,
  the figure has no right to exist — either split it into figures
  that each pass the test, or cut it.
- **Figures argue in sequence.** The figure captions, read in order
  with no body text, must reconstruct the paper's argument: problem,
  mechanism, evidence. A scan-pass reader who reads only captions
  should reach the same conclusion as a careful reader.

## When to use

- Planning the figure set for a new paper (ideally right after the
  claim structure is fixed, before any experiment plotting).
- A draft has figures but reviewers "didn't get it" — re-derive the
  budget and check which claims are visually unproven.
- Handing off to `figure-coder` or an Artist agent: they require a
  design spec; this skill produces it.
- Deciding whether a proposed figure earns its slot.

## When NOT to use

- Writing the actual plotting code — that is `figure-coder`.
- Generic charting outside a paper.
- The paper's claims are not yet articulated. Fix the claims first
  (use the paper-skeleton / claim-graph stage of the pipeline); a
  budget cannot be allocated against claims that do not exist.

## Procedure

### Step 1 — Collect the claim ledger

Input priority:

1. A claim graph, if the pipeline has one (claims with IDs,
   dependency edges, and the experiments that support each claim).
2. Otherwise, extract claims from the abstract and the contribution
   bullets, assign IDs `C1..Cn`, and confirm the list with the user.

For each claim record: `id`, `statement`, `kind`
(`problem-exists` | `mechanism` | `main-result` | `ablation` |
`generality` | `efficiency`), and `evidence_source` (which
experiment, dataset, or derivation backs it).

### Step 2 — Rank claims by load-bearing weight

A claim's weight is how much of the paper collapses if a reviewer
does not believe it. Score each claim 1-5:

- 5 — the headline: the paper is rejected if this is not believed.
- 4 — the mechanism: why the headline result happens.
- 3 — a differentiator against the closest baseline or prior work.
- 2 — supporting evidence (ablations, robustness, scaling behavior).
- 1 — nice-to-have (efficiency footnotes, qualitative color).

Ties are broken by novelty: the claim reviewers are least likely to
grant on trust ranks higher.

### Step 3 — Set the budget

Default budget: **6-8 figure slots** in the main body (venue-typical
for an 8-9 page paper; adjust down for short papers, up only if the
venue's page style genuinely accommodates it). Tables are budgeted
separately and are the right medium for dense exact numbers; do not
spend a figure slot on what a table does better.

### Step 4 — Allocate by marginal information

Walk the ranked claim list and assign slots greedily by **marginal
information**: the next slot goes to the claim whose visual proof
adds the most reviewer belief not already delivered by an earlier
figure or a table. Rules:

- **Every figure names the claim it proves.** The spec field `claim`
  is mandatory and must reference a ledger ID.
- **Claims may share a figure** when one visual form proves both
  (e.g., a frontier plot proving both `main-result` and
  `efficiency`). List all claim IDs.
- **A figure proving no claim is cut.** No slot for "architecture
  diagrams because papers have them" — an overview schematic must
  earn its slot by proving a `mechanism` claim.
- **Diminishing returns are real.** A second figure for an
  already-proven claim must add a genuinely new axis of evidence
  (different dataset family, different failure regime), or the slot
  goes to the highest-weight unproven claim.
- Claims left without a slot are recorded in the budget table as
  `coverage: table` or `coverage: text`, so nothing is silently
  unproven.

### Step 5 — Write the per-figure design spec

For each allocated slot, in figure order, fill this spec **starting
with the takeaway** — the takeaway is written before the visual form
is chosen, never reverse-engineered from a plot that already exists:

```json
{
  "figure_id": "fig3",
  "claim": ["C2", "C5"],
  "ten_second_takeaway": "One declarative sentence.",
  "visual_form": "ablation-ladder",
  "data_source": "runs/ablation_grid.csv (columns: variant, metric, seed)",
  "annotations_that_do_the_arguing": [
    "arrow from full-model bar to best-ablation bar labeled with the gap",
    "shaded band marking the baseline ceiling"
  ],
  "caption_first_sentence": "States the takeaway; remaining caption text explains how to read the figure.",
  "renderer": "figure-coder",
  "size": "single-column",
  "notes": "anything the renderer must not get wrong"
}
```

Field rules:

- `visual_form` — choose from the catalogue in
  `references/visual-forms.md` (contrast pair, mechanism schematic,
  scaling curve, ablation ladder, error anatomy, budget/frontier
  plot, and others). The catalogue entry gives the argument shape
  each form makes and the annotation that typically carries it;
  justify any form used outside its stated argument shape.
- `annotations_that_do_the_arguing` — mandatory and non-empty. A
  figure where the takeaway is not physically pointed at (arrow,
  highlight, labeled gap, reference line) fails QC rule Q7. The
  data is the evidence; the annotation is the argument.
- `caption_first_sentence` — states the takeaway as a finding
  ("X halves error on Y"), not a description ("Comparison of X
  and Y"). It must be readable with zero body text.
- `renderer` — `figure-coder` for anything data-driven; `artist`
  for schematics, mechanism drawings, and mixed icon/text panels.
- `data_source` — a concrete file or experiment run identifier, or
  `"pending: <experiment>"` if the run does not exist yet. Never
  invent data; a spec with pending data is a valid output and tells
  the pipeline which experiment blocks which figure.

### Step 6 — QC gate (computed checklist)

The gate is **computed, not vibed**: each rule is checked
mechanically against the spec (and against the rendered image, when
one is provided for audit — load it with the Read tool first). Rules
that require seeing pixels are marked *(image)* and reported as
`UNCHECKED — needs rendered figure` in spec-only mode.

| ID  | Rule                                                             | Severity |
|-----|------------------------------------------------------------------|----------|
| Q1  | Every axis has a label **and units** (or is explicitly unitless) | CRITICAL |
| Q2  | Colorbar/legend integrity: every encoded channel is decodable; no legend entry without a mark; no color-only distinction between series | CRITICAL |
| Q3  | Legible at final column width *(image)*: minimum text ~8pt after scaling; test by viewing at 100% of final size | CRITICAL |
| Q4  | Survives grayscale *(image)*: takeaway still readable when colors are removed | MAJOR |
| Q5  | Caption is self-contained: first sentence states the takeaway; a reader with no body text can decode the figure | MAJOR |
| Q6  | No chartjunk: no 3D effects, no decorative gradients, no redundant gridlines/borders that compete with data ink | MAJOR |
| Q7  | The takeaway is visually dominant: the annotation from the spec exists and points at it; the key result is not buried in a uniform grid of subplots | CRITICAL |
| Q8  | Notation consistent with the body: symbols, method names, and colors match the text and the other figures (one color = one method, everywhere) | MAJOR |
| Q9  | Honest encoding: axis ranges do not exaggerate gaps; broken axes are marked; error bars or seeds are shown where variance exists | CRITICAL |
| Q10 | Budget discipline: the figure's `claim` field is non-empty and the claim is in the ledger | CRITICAL |

Report every rule as `PASS` / `FAIL` / `UNCHECKED`, with a one-line
reason for each `FAIL`. Any `CRITICAL` failure blocks handoff to the
renderer until the spec is amended.

### Step 7 — Emit output

Three artifacts, in this order:

**1. Budget table**

| Slot | Figure | Claims | Weight | Visual form | Renderer | Data status |
|------|--------|--------|--------|-------------|----------|-------------|

Followed by the unallocated claims and their `coverage` (table/text).

**2. Design specs** — the JSON objects from Step 5, one per figure,
in figure order (this is the machine-readable handoff; keep it valid
JSON, one array).

**3. QC report** — per figure, the Q1-Q10 results with severities,
plus a summary line: `n CRITICAL, m MAJOR, k UNCHECKED`.

## Handoff contract

- `figure-coder` consumes the spec directly: `visual_form` maps to
  its chart types, `size` to its column geometry, `data_source` to
  its data input, and `caption_first_sentence` seeds the caption.
- The Artist agent consumes `renderer: "artist"` specs: the
  takeaway, the annotation list, and the catalogue entry's layout
  notes are its drawing brief.
- Re-run only the QC gate (Step 6) on rendered images to audit
  them; the budget does not need re-derivation unless claims change.

## Failure modes to refuse

- **Takeaway written after the plot.** If the user brings a finished
  figure and asks for a takeaway, run the process in reverse openly:
  derive the takeaway, then check whether the figure is the best
  spend of that slot — often it is not.
- **The subplot lattice.** A 3x4 grid of equally-weighted panels is
  a budget violation dressed as thoroughness: it spends one slot to
  prove nothing dominantly. Promote the one panel that carries the
  takeaway; demote the rest to the appendix.
- **The unearned overview.** A pipeline schematic that merely
  restates the method section proves no claim. It earns a slot only
  when it shows *why* the mechanism produces the headline result.

## Acknowledgments

The pipeline role of this skill — a figure-design checkpoint between
paper planning and figure rendering — was inspired by HKUSTDial's
Supervisor-Skills. The framework implemented here (the Figure
Information Budget: reviewer scan model, 10-second test, claim-based
budget allocation, and computed QC gate) is an independent redesign.
