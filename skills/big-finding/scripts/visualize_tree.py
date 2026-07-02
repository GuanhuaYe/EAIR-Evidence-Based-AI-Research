#!/usr/bin/env python3
"""ASCII visualization of knowledge tree.

Usage:
    visualize_tree.py [--status FILTER] [--root NODE_ID] [--show-experiments]
"""
import argparse, json, sys
from pathlib import Path


def tree_path():
    cur = Path.cwd()
    for d in [cur, *cur.parents]:
        cand = d / "big_finding" / "tree.json"
        if cand.exists():
            return cand
    return None


STATUS_GLYPH = {
    "OPEN":         "○",
    "PROVEN":       "✓",
    "REFUTED":      "✗",
    "INSUFFICIENT": "?",
    "CONFOUNDED":   "≅",
    "PIVOTED":      "→",
    "DEPRECATED":   "⊘",
}


def color(status):
    """ANSI color per status."""
    return {
        "PROVEN":       "\033[32m",   # green
        "REFUTED":      "\033[31m",   # red
        "OPEN":         "\033[33m",   # yellow
        "INSUFFICIENT": "\033[33m",
        "CONFOUNDED":   "\033[35m",   # magenta
        "PIVOTED":      "\033[36m",   # cyan
        "DEPRECATED":   "\033[90m",   # grey
    }.get(status, "")


RESET = "\033[0m"


def print_subtree(tree, node_id, prefix="", is_last=True, args=None):
    node = tree["nodes"].get(node_id)
    if not node:
        return
    if args.status and node["status"] not in args.status:
        # skip but still recurse to print children of OPEN ancestors
        for cid in node.get("children", []):
            print_subtree(tree, cid, prefix, True, args)
        return

    glyph = STATUS_GLYPH.get(node["status"], "·")
    col = color(node["status"]) if args.color else ""
    branch = "└── " if is_last else "├── "
    short = node["short"][:80] + ("…" if len(node["short"]) > 80 else "")
    print(f"{prefix}{branch}{col}{glyph} {node_id} [{node['status']}] {short}{RESET if col else ''}")

    sub_prefix = prefix + ("    " if is_last else "│   ")

    if args.show_experiments:
        for eid in node.get("experiments", []):
            exp = tree["experiments"].get(eid, {})
            dec = exp.get("decision", "?")
            print(f"{sub_prefix}  exp {eid}: {dec}")

    if node.get("falsifiable_form") and args.verbose:
        print(f"{sub_prefix}  falsifiable: {node['falsifiable_form'][:100]}")
    if node.get("notes") and args.verbose:
        for n in node["notes"][:3]:
            print(f"{sub_prefix}  note: {n[:80]}")

    children = node.get("children", [])
    for i, cid in enumerate(children):
        print_subtree(tree, cid, sub_prefix, i == len(children) - 1, args)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--status", help="comma-separated filter, e.g., PROVEN,OPEN")
    ap.add_argument("--root", help="start from specific node id")
    ap.add_argument("--show-experiments", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--no-color", dest="color", action="store_false")
    ap.set_defaults(color=sys.stdout.isatty())
    args = ap.parse_args()

    if args.status:
        args.status = set(args.status.split(","))

    p = tree_path()
    if not p:
        print("no tree.json found in cwd or ancestors", file=sys.stderr)
        sys.exit(1)
    tree = json.load(open(p))

    print(f"Project: {tree.get('project')} ({len(tree.get('nodes', {}))} nodes, "
          f"{len(tree.get('experiments', {}))} experiments, "
          f"{len(tree.get('findings_catalogue', []))} findings)")
    print()

    nodes = tree.get("nodes", {})
    if args.root:
        roots = [args.root]
    else:
        # find roots: nodes with no parent
        roots = [k for k, v in nodes.items() if not v.get("parent")]

    if not roots:
        print("(empty tree)")
        return

    for i, rid in enumerate(roots):
        print_subtree(tree, rid, "", True, args)
        if i < len(roots) - 1:
            print()

    # Findings catalogue
    findings = tree.get("findings_catalogue", [])
    if findings:
        print()
        print("=" * 60)
        print("FINDINGS CATALOGUE")
        print("=" * 60)
        for f in findings:
            print(f"  {f.get('finding_id')}  ←  {f.get('node_id')}  {f.get('statement', '')[:80]}")


if __name__ == "__main__":
    main()
