---
name: figure-coder
description: >-
  Generates publication-grade figure code (matplotlib / TikZ /
  Plotly / R-ggplot2) for top-tier venues, with venue-aware defaults:
  column widths, font sizes, color-blind-safe palettes, vector
  output (PDF / EPS), no rasterized text. Complements
  figure-designer — figure-designer decides 'what to draw',
  figure-coder produces 'the actual code that draws it'. Use when
  the user says 'plot this', 'draw this figure', 'matplotlib code
  for ...', 'TikZ for ...', 'fix this figure', 'make this figure
  publication ready'. Different from running generic matplotlib —
  this enforces venue conventions, paper-quality typography, and
  reproducibility.
license: CC-BY-4.0
---

# Figure Coder

## Overview

`figure-designer` advises on figure choice and layout but stops at
giving prose guidance. The actual matplotlib/TikZ code still gets
written ad-hoc, which produces inconsistent typography, wrong column
widths, raster fonts, and color-blind-unfriendly palettes. This skill
emits venue-aware figure code with the following enforced
properties:

- Vector PDF / EPS output (no PNG in paper)
- Column-width-aware (single-column vs double-column vs full page)
- Font size matches venue body text (no shrinking past 7pt)
- Color-blind-safe palette by default
- No rasterized text in figures
- Reproducible: deterministic seed, fixed style sheet, no
  display-dependent rendering
- One Python or R file per figure, callable as `python figN.py` or
  `Rscript figN.R`, output: `figN.pdf`

## When to invoke

- User says "plot this", "draw figure N", "matplotlib code for X",
  "TikZ for Y", "make this publication ready".
- After figure-designer has decided what to draw.
- When existing paper figures need a venue-style refresh (different
  venue submission).

Do NOT invoke for diagrams that are inherently structural (system
architectures with mixed text + icons + arrows) — those belong in
draw.io / Figma / inkscape; use figure-designer for those.

## Operating procedure

### Stage 0 — Detect venue + figure spec

Required inputs:
- Venue (from `PIPELINE_STATE.json` or ask)
- Figure type (one of):
  - `bar` — grouped or stacked
  - `line` — over training steps / epochs / dataset size
  - `scatter` — including pairs plot
  - `heatmap` — confusion matrix, attention map, ablation grid
  - `box` / `violin` — distribution per group
  - `cdf` / `ecdf` — for runtime / latency distributions
  - `radar` — multi-axis comparison (rare; advise against for ≥5 axes)
  - `table-as-figure` — when a table needs visual emphasis
  - `architecture` — escalate to figure-designer + draw.io / Inkscape
  - `tikz` — for math diagrams, lattices, FSMs
- Data: CSV / JSON / inline values
- Caption (optional, but the layout assumes a caption exists)

Load venue spec from `references/venue_geometry.md`:
- Column width (mm)
- Font family + size
- Output format (PDF preferred; EPS for some legacy submissions)
- Margin rules

### Stage 1 — Style sheet selection

Three style sheet options, chosen by venue family:

| Family | Style sheet |
|---|---|
| ml-formal | `templates/mpl_neurips.mplstyle` |
| nlp-narrative | `templates/mpl_acl.mplstyle` |
| db-engineering | `templates/mpl_sigmod.mplstyle` |
| cv-visual | `templates/mpl_cvpr.mplstyle` |
| mining-applied | `templates/mpl_kdd.mplstyle` |

Each style sheet:
- Sets font family (Times / Computer Modern / Helvetica per venue)
- Sets default font size (typically 8-9pt, with axis labels +1)
- Sets figure size to single / double-column width
- Sets line width 1.0pt, axis line width 0.8pt
- Sets color cycle to color-blind-safe (Wong palette / Okabe-Ito /
  ColorBrewer8)
- Enables vector backend, disables aliased rendering

### Stage 2 — Template instantiation

Each figure type has a template under `templates/` that takes data +
caption and emits a runnable script. Template enforces:

- Title: omit (caption carries title in papers)
- Legend: top-right inside axes if it fits without overlap, else
  outside-right
- Axis labels: with units in parens, e.g., "Latency (ms)"
- Tick formatting: no scientific notation under 1e4; SI suffixes
  for >1e4
- Grid: light grey, behind data, only on major ticks
- Colors: assigned in order from the color-blind-safe palette
- Bar/line markers: distinct shapes per series for B/W printing
- Error bars: 95% CI by default (assert input has std or CI columns);
  fail if comparing across groups without error bars
- Annotations: pointer-style for callouts, with leader line

### Stage 3 — Reproducibility wrapper

Every emitted script starts with:

```python
import numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
mpl.use("Agg")  # no GUI dependency
plt.style.use("../style/<venue>.mplstyle")
np.random.seed(0)  # only matters if any random sampling in plotting
```

And ends with:

```python
fig.tight_layout()
fig.savefig("<output>.pdf", bbox_inches="tight", pad_inches=0.02)
```

PDF output, no PNG. `bbox_inches="tight"` to avoid wasted whitespace.

### Stage 4 — Audit

Before delivering, run an automated audit:
- Open the produced PDF, extract text + image bounding boxes
- Check: text size ≥7pt, no rasterized text, color palette matches
  selected style sheet
- Check: figure dimensions match column width spec
- Check: error bars or CIs present for any group-comparison figure
- Output `figure_audit.json` per figure

### Stage 5 — Output

```
figures/
├── figN.py                  (matplotlib script)
├── figN.pdf                 (vector output)
├── figN.csv                 (data, archived)
├── figure_audit.json
└── style/
    └── <venue>.mplstyle     (copied for self-containment)
```

For TikZ figures: emit `figN.tex` with standalone document class +
caller include snippet for the main document.

For R/ggplot2: emit `figN.R` with venue style theme inline.

## Venue-specific quirks

- NeurIPS: PDF, Times font (LaTeX), single-column 3.25in /
  double-column 6.75in. Color OK but B/W printable required.
- ICML / ICLR: PDF, similar dims, Color-OK.
- ACL ARR: PDF, single-column ~3.1in / double-column ~6.3in, Times.
- SIGMOD: PDF, narrower columns (~3.33in / 7.0in), Times, B/W
  printability matters.
- VLDB: PDF, two-column, ~3.33in / 7.0in.
- CVPR / ICCV: PDF, two-column ~3.25in / 6.875in, sans-serif
  acceptable but Times standard.
- KDD: PDF, two-column ~3.33in / 7.0in.

## Cross-skill interactions

- `figure-designer` — INVOKE FIRST. figure-coder requires a designed
  spec, not an "I want a chart". If user goes straight to figure-coder
  without designing, ask 2-3 clarifying questions (what to compare,
  what story, what data source).
- `venue-aware-polishing` — coordinate font / column-width via shared
  PIPELINE_STATE venue.
- `pre-submission-reviewer` — runs after figures land; checks caption
  formatting and figure-text contrast.
- `data-card` — if a figure includes raw user data, datasheet must
  document.

## Constraints

- Never use jet / rainbow colormaps — fail the audit.
- Never use ≥6 colors in a single figure — split into subplots.
- Never produce raster output (PNG / JPG) for the paper body. PNG is
  OK only for screenshots / qualitative examples explicitly labeled
  as such.
- Font sizes: body 9pt, axis labels 8pt, tick labels 7pt minimum.
- Aspect ratio: prefer 1.5:1 to 2:1 for line / bar; 1:1 for scatter /
  heatmap.

## References

- `references/venue_geometry.md` — column widths and font specs
- `references/palette_choices.md` — color-blind-safe palettes
- `references/template_index.md` — which template per figure type
- `templates/` — actual style sheets and Python / TikZ template
  starting points
