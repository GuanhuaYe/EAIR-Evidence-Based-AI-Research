#!/usr/bin/env python3
"""Knowledge tree CRUD for big-finding skill.

Usage:
    tree.py init <project_name>                # create tree.json
    tree.py status                              # summary of all nodes
    tree.py add-hypothesis --short '...' --falsifiable '...' --scope '...' --mechanism '...' --kill '...' [--parent H001]
    tree.py add-experiment --hypothesis H001 --bundle path/to/bundle.yaml [--code-hash sha256:...]
    tree.py set-status <node_id> <PROVEN|REFUTED|INSUFFICIENT|CONFOUNDED|PIVOTED|DEPRECATED> [--reason '...']
    tree.py promote <node_id> --finding F001  # add to catalogue if passes Nature-worthy test
    tree.py show <node_id>                      # detailed dump
    tree.py path <node_id>                      # ancestry chain
"""
import argparse, json, os, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path


def tree_path():
    """Find tree.json — current dir, then up to paper root."""
    cur = Path.cwd()
    for d in [cur, *cur.parents]:
        cand = d / "big_finding" / "tree.json"
        if cand.exists():
            return cand
    # Fallback: <paper_dir>/big_finding/tree.json relative to skill
    return Path.cwd() / "big_finding" / "tree.json"


def now():
    return datetime.now(timezone.utc).astimezone().isoformat()


def next_id(tree, prefix):
    existing = [k for k in tree.get("nodes", {}).keys() if k.startswith(prefix)]
    existing += [k for k in tree.get("experiments", {}).keys() if k.startswith(prefix)]
    nums = [int(k[1:]) for k in existing if k[1:].isdigit()]
    return f"{prefix}{(max(nums) + 1) if nums else 1:03d}"


def load_tree():
    p = tree_path()
    if not p.exists():
        return None
    return json.load(open(p))


def save_tree(tree):
    p = tree_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    json.dump(tree, open(tmp, "w"), indent=2)
    tmp.replace(p)


def cmd_init(args):
    p = Path.cwd() / "big_finding" / "tree.json"
    if p.exists():
        print(f"tree.json already exists at {p}", file=sys.stderr)
        return 1
    p.parent.mkdir(parents=True, exist_ok=True)
    tree = {
        "version": 1,
        "project": args.project_name,
        "created": now(),
        "nodes": {},
        "experiments": {},
        "findings_catalogue": [],
    }
    json.dump(tree, open(p, "w"), indent=2)
    print(f"Initialized tree.json for project '{args.project_name}' at {p}")
    return 0


def cmd_add_hypothesis(args):
    tree = load_tree()
    if tree is None:
        print("no tree.json — run `tree.py init <project>` first", file=sys.stderr)
        return 1
    hid = next_id(tree, "H")
    node = {
        "id": hid,
        "parent": args.parent,
        "type": "hypothesis",
        "status": "OPEN",
        "short": args.short,
        "falsifiable_form": args.falsifiable,
        "generalization_scope": args.scope,
        "mechanism_claim": args.mechanism,
        "alternatives_to_rule_out": [a.strip() for a in (args.alternatives or "").split(";") if a.strip()],
        "kill_criteria": args.kill,
        "created_at": now(),
        "modified_at": now(),
        "status_history": [{"at": now(), "status": "OPEN"}],
        "experiments": [],
        "children": [],
        "notes": [],
    }
    tree["nodes"][hid] = node
    if args.parent and args.parent in tree["nodes"]:
        tree["nodes"][args.parent].setdefault("children", []).append(hid)
        tree["nodes"][args.parent]["modified_at"] = now()
    save_tree(tree)
    print(f"Added hypothesis {hid}: {args.short}")
    return 0


def cmd_add_experiment(args):
    tree = load_tree()
    if tree is None:
        print("no tree.json", file=sys.stderr)
        return 1
    if args.hypothesis not in tree["nodes"]:
        print(f"hypothesis {args.hypothesis} not in tree", file=sys.stderr)
        return 1
    eid = next_id(tree, "E")
    exp = {
        "id": eid,
        "hypothesis_id": args.hypothesis,
        "bundle_path": args.bundle,
        "code_hash": args.code_hash,
        "data_hash": args.data_hash,
        "protocol_hash": args.protocol_hash,
        "arms": [],            # populated from bundle.yaml — caller can update
        "lineage_check_passed": False,  # set true after lineage_check.py
        "decision_rule": args.decision_rule,
        "run_window": {"start": None, "end": None},
        "hardware": args.hardware,
        "vllm_build": args.vllm_build,
        "result_path": None,
        "decision_path": None,
        "decision": "PENDING",
        "gpu_h_consumed": None,
    }
    tree["experiments"][eid] = exp
    tree["nodes"][args.hypothesis].setdefault("experiments", []).append(eid)
    tree["nodes"][args.hypothesis]["modified_at"] = now()
    save_tree(tree)
    print(f"Added experiment {eid} for hypothesis {args.hypothesis}, bundle {args.bundle}")
    return 0


def cmd_set_status(args):
    tree = load_tree()
    if tree is None:
        return 1
    if args.node not in tree["nodes"]:
        print(f"node {args.node} not in tree", file=sys.stderr)
        return 1
    node = tree["nodes"][args.node]
    node["status"] = args.status
    node["modified_at"] = now()
    node.setdefault("status_history", []).append({
        "at": now(),
        "status": args.status,
        "reason": args.reason,
    })
    save_tree(tree)
    print(f"{args.node}: {args.status}" + (f" — {args.reason}" if args.reason else ""))
    return 0


def cmd_status(args):
    tree = load_tree()
    if tree is None:
        print("no tree.json", file=sys.stderr)
        return 1
    nodes = tree.get("nodes", {})
    counts = {}
    for n in nodes.values():
        counts[n["status"]] = counts.get(n["status"], 0) + 1
    print(f"Project: {tree.get('project')} (created {tree.get('created')})")
    print(f"Nodes: {len(nodes)} hypotheses, {len(tree.get('experiments', {}))} experiments")
    print(f"Findings catalogue: {len(tree.get('findings_catalogue', []))}")
    print("Status distribution:")
    for s, c in sorted(counts.items()):
        print(f"  {s:15}  {c}")
    return 0


def cmd_show(args):
    tree = load_tree()
    if tree is None:
        return 1
    if args.node in tree.get("nodes", {}):
        print(json.dumps(tree["nodes"][args.node], indent=2))
    elif args.node in tree.get("experiments", {}):
        print(json.dumps(tree["experiments"][args.node], indent=2))
    else:
        print(f"node/experiment {args.node} not found", file=sys.stderr)
        return 1
    return 0


def cmd_path(args):
    tree = load_tree()
    if tree is None:
        return 1
    if args.node not in tree.get("nodes", {}):
        print(f"node {args.node} not in tree", file=sys.stderr)
        return 1
    chain = []
    cur = args.node
    while cur:
        chain.append(cur)
        cur = tree["nodes"][cur].get("parent")
    chain.reverse()
    for i, nid in enumerate(chain):
        node = tree["nodes"][nid]
        prefix = "  " * i + ("└── " if i > 0 else "")
        print(f"{prefix}{nid} [{node['status']}] {node['short']}")
    return 0


def cmd_promote(args):
    tree = load_tree()
    if tree is None:
        return 1
    node = tree["nodes"].get(args.node)
    if not node:
        return 1
    if node["status"] != "PROVEN":
        print(f"refusing — {args.node} is {node['status']}, not PROVEN", file=sys.stderr)
        return 1
    tree.setdefault("findings_catalogue", []).append({
        "finding_id": args.finding,
        "node_id": args.node,
        "promoted_at": now(),
        "statement": node["short"],
    })
    save_tree(tree)
    print(f"Promoted {args.node} → {args.finding} in findings catalogue")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("init")
    s.add_argument("project_name")
    s.set_defaults(func=cmd_init)

    s = sp.add_parser("status")
    s.set_defaults(func=cmd_status)

    s = sp.add_parser("add-hypothesis")
    s.add_argument("--short", required=True)
    s.add_argument("--falsifiable", required=True)
    s.add_argument("--scope", required=True)
    s.add_argument("--mechanism", required=True)
    s.add_argument("--kill", required=True)
    s.add_argument("--alternatives", help="semicolon-separated alternatives")
    s.add_argument("--parent")
    s.set_defaults(func=cmd_add_hypothesis)

    s = sp.add_parser("add-experiment")
    s.add_argument("--hypothesis", required=True)
    s.add_argument("--bundle", required=True)
    s.add_argument("--code-hash")
    s.add_argument("--data-hash")
    s.add_argument("--protocol-hash")
    s.add_argument("--decision-rule")
    s.add_argument("--hardware", default="datacenter-80gb")
    s.add_argument("--vllm-build", default="0.21")
    s.set_defaults(func=cmd_add_experiment)

    s = sp.add_parser("set-status")
    s.add_argument("node")
    s.add_argument("status", choices=["OPEN", "PROVEN", "PROVEN_SINGLE_SPLIT",
                                       "REFUTED", "INSUFFICIENT",
                                       "CONFOUNDED", "PIVOTED", "DEPRECATED"])
    s.add_argument("--reason")
    s.set_defaults(func=cmd_set_status)

    s = sp.add_parser("show")
    s.add_argument("node")
    s.set_defaults(func=cmd_show)

    s = sp.add_parser("path")
    s.add_argument("node")
    s.set_defaults(func=cmd_path)

    s = sp.add_parser("promote")
    s.add_argument("node")
    s.add_argument("--finding", required=True)
    s.set_defaults(func=cmd_promote)

    args = p.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
