"""Heatmap template — figure-coder.

Default colormap: viridis (perceptually uniform, color-blind safe).
For divergent values centered on 0, switch to RdBu_r.

Usage:
    python heatmap.py --data data.csv --out fig.pdf --style ../style/neurips.mplstyle
"""
import argparse, csv, pathlib
import numpy as np
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt


def load_matrix(path: pathlib.Path):
    rows = list(csv.reader(path.open()))
    row_labels = [r[0] for r in rows[1:]]
    col_labels = rows[0][1:]
    M = np.array([[float(c) for c in r[1:]] for r in rows[1:]])
    return row_labels, col_labels, M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--style", required=True)
    ap.add_argument("--cmap", default="viridis")
    ap.add_argument("--diverging", action="store_true",
                    help="use RdBu_r centered on 0")
    ap.add_argument("--annot", action="store_true",
                    help="overlay numbers on cells")
    ap.add_argument("--width", type=float, default=3.25)
    ap.add_argument("--height", type=float, default=2.8)
    ap.add_argument("--cbar_label", default="")
    args = ap.parse_args()

    plt.style.use(args.style)
    np.random.seed(0)

    row_labels, col_labels, M = load_matrix(pathlib.Path(args.data))
    cmap = "RdBu_r" if args.diverging else args.cmap
    vmin, vmax = (None, None)
    if args.diverging:
        amax = float(np.abs(M).max())
        vmin, vmax = -amax, amax

    fig, ax = plt.subplots(figsize=(args.width, args.height),
                           constrained_layout=True)
    im = ax.imshow(M, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    if args.cbar_label:
        cbar.set_label(args.cbar_label)

    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)

    if args.annot:
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                val = M[i, j]
                color = "white" if (
                    not args.diverging and val > M.mean()
                ) else "black"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        color=color, fontsize=6)

    fig.savefig(args.out)


if __name__ == "__main__":
    main()
