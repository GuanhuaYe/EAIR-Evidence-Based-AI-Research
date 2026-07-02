# Template index — figure type → template file

| Figure type | Template | Default aspect ratio | Notes |
|---|---|---|---|
| bar | `templates/bar.py` | 1.6:1 | Grouped + stacked variants |
| line | `templates/line.py` | 1.8:1 | Training curves, scaling laws |
| scatter | `templates/scatter.py` | 1:1 | With optional regression line |
| heatmap | `templates/heatmap.py` | 1:1 | Confusion / attention / ablation |
| box | `templates/box.py` | 1.5:1 | Distribution per group |
| violin | `templates/violin.py` | 1.5:1 | Replaces box when N is small |
| cdf | `templates/cdf.py` | 1.5:1 | For latency / runtime distributions |
| radar | `templates/radar.py` | 1:1 | Use sparingly, max 5 axes |
| table-as-figure | `templates/table_as_figure.py` | n/a | Use when emphasis required |
| tikz-lattice | `templates/lattice.tex` | n/a | For poset / Hasse diagrams |
| tikz-fsm | `templates/fsm.tex` | n/a | For automaton / state machine |

## Multi-panel figures

When more than 2 series should be compared on multiple axes, prefer
multi-panel (subplots) over over-stacked single panel:

```python
fig, axes = plt.subplots(1, 3, figsize=(double_col_width, 2.5),
                         sharey=True, constrained_layout=True)
```

Panel labels: (a), (b), (c) in upper-left corner of each axes,
boldface, font size matching body.

## When to abandon code-generation

For diagrams that are inherently:
- Heavy text + icons + arrows (system architectures)
- Custom visual metaphors (running examples with mixed elements)
- Pipeline diagrams with branching

Do NOT use figure-coder. Escalate to figure-designer + draw.io /
Inkscape / Figma. figure-coder is for *data-driven* figures only.
