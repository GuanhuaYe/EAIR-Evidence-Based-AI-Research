# Color-blind-safe palettes

Default palette for figure-coder: Wong (Okabe-Ito 8-color). Verified
color-blind-safe (protanopia, deuteranopia, tritanopia).

## Wong 8-color (default)

| # | Name | Hex |
|---|---|---|
| 0 | Black | #000000 |
| 1 | Orange | #E69F00 |
| 2 | Sky Blue | #56B4E9 |
| 3 | Bluish Green | #009E73 |
| 4 | Yellow | #F0E442 |
| 5 | Blue | #0072B2 |
| 6 | Vermillion | #D55E00 |
| 7 | Reddish Purple | #CC79A7 |

Use in matplotlib via:
```python
WONG = ["#000000", "#E69F00", "#56B4E9", "#009E73",
        "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
plt.rcParams["axes.prop_cycle"] = plt.cycler(color=WONG)
```

## ColorBrewer8 (alternative qualitative)

For categorical data, ≤8 categories:
- Set1: #E41A1C, #377EB8, #4DAF4A, #984EA3, #FF7F00, #FFFF33, #A65628, #F781BF
- Set2: #66C2A5, #FC8D62, #8DA0CB, #E78AC3, #A6D854, #FFD92F, #E5C494, #B3B3B3

Note: Set1's red+green can be confused by some color-blind viewers;
prefer Wong unless Set1 is required for consistency with prior paper.

## Sequential (for heatmaps)

- viridis: perceptually uniform, color-blind safe — preferred default
- cividis: optimized for color-blind viewers — use if exclusively B/W
  legibility matters
- magma / inferno: good for high-contrast emphasis on high values

## Diverging (for residuals / errors centered on 0)

- RdBu_r: red-blue diverging, color-blind safe in moderation
- BrBG: brown-blue-green, more color-blind safe than RdBu
- PiYG: pink-yellow-green

## NEVER USE

- jet (rainbow): not perceptually uniform, not color-blind safe
- hsv (rainbow): same
- rainbow: same
- nipy_spectral: not color-blind safe

The Stage 4 audit fails if any of these appear in the produced figure.

## Marker shapes (B/W printing)

Distinct marker shapes per series so figure is legible in B/W:
`o`, `s`, `^`, `v`, `D`, `P`, `X`, `<`, `>`, `*`, `h`, `p`

Use the same shape across panels of one figure for one series.

## Line styles

When series count ≤4, all solid lines OK if colors distinct.
When series count ≥5, use `-`, `--`, `:`, `-.` cycling alongside
colors, so legend remains parseable in B/W print.
