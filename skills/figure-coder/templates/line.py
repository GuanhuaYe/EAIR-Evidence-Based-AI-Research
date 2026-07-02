"""Line chart template — figure-coder.

Distinct color + marker + linestyle per series so figure remains
legible in B/W print.

Usage:
    python line.py --data data.csv --out fig.pdf --style ../style/neurips.mplstyle
"""
import argparse, csv, pathlib
import numpy as np
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt


MARKERS = ["o", "s", "^", "v", "D", "P", "X", "<", ">", "*"]
LINESTYLES = ["-", "--", ":", "-."]


def load_csv(path: pathlib.Path):
    return list(csv.DictReader(path.open()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--style", required=True)
    ap.add_argument("--xlabel", default="")
    ap.add_argument("--ylabel", default="")
    ap.add_argument("--series_col", default="series")
    ap.add_argument("--x_col", default="x")
    ap.add_argument("--y_col", default="y")
    ap.add_argument("--err_col", default="std")
    ap.add_argument("--width", type=float, default=3.25)
    ap.add_argument("--height", type=float, default=2.0)
    ap.add_argument("--logx", action="store_true")
    ap.add_argument("--logy", action="store_true")
    args = ap.parse_args()

    plt.style.use(args.style)
    np.random.seed(0)

    rows = load_csv(pathlib.Path(args.data))
    series = list(dict.fromkeys(r[args.series_col] for r in rows))

    fig, ax = plt.subplots(figsize=(args.width, args.height),
                           constrained_layout=True)

    for si, s in enumerate(series):
        rs = [r for r in rows if r[args.series_col] == s]
        x = np.array([float(r[args.x_col]) for r in rs])
        y = np.array([float(r[args.y_col]) for r in rs])
        e = np.array([float(r.get(args.err_col, 0) or 0) for r in rs])
        order = np.argsort(x)
        x, y, e = x[order], y[order], e[order]
        ax.plot(x, y, label=s,
                marker=MARKERS[si % len(MARKERS)],
                linestyle=LINESTYLES[si % len(LINESTYLES)] if len(series) >= 5 else "-",
                markersize=4)
        if e.any():
            ax.fill_between(x, y - e, y + e, alpha=0.15)

    if args.logx:
        ax.set_xscale("log")
    if args.logy:
        ax.set_yscale("log")
    if args.xlabel:
        ax.set_xlabel(args.xlabel)
    if args.ylabel:
        ax.set_ylabel(args.ylabel)
    if len(series) > 1:
        ax.legend(loc="best")

    fig.savefig(args.out)


if __name__ == "__main__":
    main()
