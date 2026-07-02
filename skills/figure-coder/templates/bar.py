"""Grouped/stacked bar chart template — figure-coder.

Usage:
    python bar.py --data data.csv --out fig.pdf --style ../style/neurips.mplstyle
"""
import argparse, csv, pathlib
import numpy as np
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt


def load_csv(path: pathlib.Path):
    rows = list(csv.DictReader(path.open()))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--style", required=True)
    ap.add_argument("--xlabel", default="")
    ap.add_argument("--ylabel", default="")
    ap.add_argument("--group_col", default="group")
    ap.add_argument("--cat_col", default="category")
    ap.add_argument("--value_col", default="value")
    ap.add_argument("--err_col", default="std")
    ap.add_argument("--width", type=float, default=3.25)
    ap.add_argument("--height", type=float, default=2.0)
    ap.add_argument("--stacked", action="store_true")
    args = ap.parse_args()

    plt.style.use(args.style)
    np.random.seed(0)

    rows = load_csv(pathlib.Path(args.data))
    groups = sorted({r[args.group_col] for r in rows},
                    key=lambda x: list(dict.fromkeys(r[args.group_col] for r in rows)).index(x))
    cats = sorted({r[args.cat_col] for r in rows},
                  key=lambda x: list(dict.fromkeys(r[args.cat_col] for r in rows)).index(x))
    val = {(r[args.group_col], r[args.cat_col]): float(r[args.value_col])
           for r in rows}
    err = {(r[args.group_col], r[args.cat_col]):
           float(r.get(args.err_col, 0) or 0) for r in rows}

    n_groups = len(groups)
    n_cats = len(cats)
    x = np.arange(n_groups)

    fig, ax = plt.subplots(figsize=(args.width, args.height),
                           constrained_layout=True)

    if args.stacked:
        bottom = np.zeros(n_groups)
        for ci, cat in enumerate(cats):
            heights = np.array([val.get((g, cat), 0) for g in groups])
            errs = np.array([err.get((g, cat), 0) for g in groups])
            ax.bar(x, heights, bottom=bottom, label=cat, yerr=errs,
                   capsize=2, edgecolor="white", linewidth=0.3)
            bottom += heights
    else:
        bar_w = 0.8 / n_cats
        for ci, cat in enumerate(cats):
            heights = np.array([val.get((g, cat), 0) for g in groups])
            errs = np.array([err.get((g, cat), 0) for g in groups])
            ax.bar(x + (ci - (n_cats - 1) / 2) * bar_w, heights, bar_w,
                   label=cat, yerr=errs, capsize=2,
                   edgecolor="white", linewidth=0.3)

    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    if args.xlabel:
        ax.set_xlabel(args.xlabel)
    if args.ylabel:
        ax.set_ylabel(args.ylabel)
    if n_cats > 1:
        ax.legend(loc="best")

    fig.savefig(args.out)


if __name__ == "__main__":
    main()
