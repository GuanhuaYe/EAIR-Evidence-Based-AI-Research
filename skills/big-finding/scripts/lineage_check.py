#!/usr/bin/env python3
"""Verify that a bundle.yaml's arms share controlled protocol — same
code_hash, same data partition, same seeds, same eval protocol, with
explicit varied_params accounting for every config difference.

Usage:
    lineage_check.py <bundle.yaml>

Exit code 0 if passes, 1 if any check fails (do not launch bundle
on non-zero exit).
"""
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def sha256_dir(path, exclude_globs=None):
    """Hash all files under path (sorted) to a single digest."""
    h = hashlib.sha256()
    p = Path(path)
    exclude_globs = exclude_globs or ["__pycache__", "*.pyc", ".git"]
    files = []
    for f in sorted(p.rglob("*")):
        if not f.is_file():
            continue
        if any(eg in str(f) for eg in exclude_globs):
            continue
        files.append(f)
    for f in files:
        h.update(str(f.relative_to(p)).encode())
        with open(f, "rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                h.update(chunk)
    return "sha256:" + h.hexdigest()


def check_required_arms(bundle, errors, warnings):
    arms = bundle.get("arms", {})
    purposes = {name: spec.get("purpose", "") for name, spec in arms.items()}
    varied = bundle.get("varied_params", []) or []

    has_treatment = any("treatment" in name.lower() or
                        "test the hypothesis" in p.lower() for name, p in purposes.items())
    has_baseline = any("baseline" in name.lower() or
                       "minimal" in p.lower() or
                       "floor" in p.lower() for name, p in purposes.items())
    has_ablation = sum(1 for name in arms if "ablation" in name.lower())
    has_neg_control = any("negative" in name.lower() or
                          "null result" in p.lower() or
                          "control_neg" in name.lower() for name, p in purposes.items())

    if not has_treatment:
        errors.append("missing treatment arm (purpose containing 'test the hypothesis' or name containing 'treatment')")
    if not has_baseline:
        errors.append("missing baseline arm (purpose 'minimal/floor' or name containing 'baseline')")
    if not has_neg_control:
        errors.append("missing negative control arm (purpose 'null result' or name containing 'negative')")

    # 1-variable strict mechanism tests (single varied_params key with ≥3 levels)
    # rely on the treatment↔baseline contrast to BE the ablation; a separate
    # ablation arm would duplicate the treatment. Waive both the ablation and
    # 4-arm requirements in that case. All other bundles must have ≥1 ablation
    # arm and ≥4 arms total.
    is_strict_1var = (len(varied) == 1 and
                      isinstance(varied[0], dict) and
                      len(next(iter(varied[0].values()), [])) >= 3)

    if not is_strict_1var:
        if has_ablation < 1:
            errors.append(f"insufficient ablation arms — need ≥1, found {has_ablation}")
        if len(arms) < 4:
            errors.append(f"bundle has only {len(arms)} arms — minimum 4 (treatment+baseline+ablation+neg_control)")
    else:
        if len(arms) < 3:
            errors.append(f"strict 1-variable bundle has only {len(arms)} arms — minimum 3 (treatment+baseline+neg_control)")
        warnings.append(f"strict 1-variable bundle: ablation waived — treatment↔baseline contrast IS the ablation (varied={varied})")


def check_shared_protocol(bundle, errors, warnings):
    arms = bundle.get("arms", {})
    if not arms:
        return

    # Each arm should NOT independently specify seed_list / eval_protocol / hardware
    # These are bundle-level invariants.
    if "seed_list" not in bundle:
        errors.append("bundle missing top-level `seed_list`")
    if "eval_protocol" not in bundle:
        errors.append("bundle missing top-level `eval_protocol`")
    if "hardware" not in bundle:
        warnings.append("bundle missing top-level `hardware` — recommend specifying datacenter-80gb / consumer-24gb")

    # No arm should override seed_list
    for name, spec in arms.items():
        overlay = spec.get("config_overlay", {}) or {}
        if "seed_list" in overlay or "seeds" in overlay:
            errors.append(f"arm `{name}` overrides seed_list — bundle invariant violated")
        if "eval_protocol" in overlay:
            errors.append(f"arm `{name}` overrides eval_protocol — bundle invariant violated")


def check_varied_params_completeness(bundle, errors, warnings):
    arms = bundle.get("arms", {})
    varied = bundle.get("varied_params", [])
    if not varied:
        warnings.append("bundle missing `varied_params` — recommend enumerating every cross-arm difference")
        return

    # Collect all config_overlay keys touched by ANY arm
    touched_keys = set()
    for spec in arms.values():
        touched_keys |= set((spec.get("config_overlay") or {}).keys())

    # Each key in varied_params should be a real difference
    varied_keys = set()
    if isinstance(varied, list):
        for entry in varied:
            if isinstance(entry, dict):
                varied_keys |= set(entry.keys())
            elif isinstance(entry, str):
                varied_keys.add(entry)

    untracked = touched_keys - varied_keys
    if untracked:
        errors.append(f"config diff between arms is not in `varied_params`: {sorted(untracked)} — every cross-arm config difference must be documented")


def check_decision_rule(bundle, errors, warnings):
    rule = bundle.get("decision_rule", {}) or {}
    required = ["PROVEN_if", "REFUTED_if"]
    optional = ["CONFOUNDED_if", "PROTOCOL_BROKEN_if", "INSUFFICIENT_if"]
    for k in required:
        if k not in rule:
            errors.append(f"decision_rule missing `{k}` — pre-registration is required before launch")
    if "CONFOUNDED_if" not in rule:
        warnings.append("decision_rule has no CONFOUNDED_if — recommend specifying confound conditions")


def check_hashes(bundle, errors, warnings):
    if "code_hash" not in bundle:
        warnings.append("bundle missing `code_hash` — recommend hashing code dir before launch")
    if "data_hash" not in bundle:
        warnings.append("bundle missing `data_hash` — recommend hashing data partition before launch")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", help="path to bundle.yaml")
    ap.add_argument("--code-dir", help="if set, compute code_hash of this dir and compare to bundle")
    args = ap.parse_args()

    if not os.path.exists(args.bundle):
        print(f"bundle file not found: {args.bundle}", file=sys.stderr)
        sys.exit(1)

    bundle = yaml.safe_load(open(args.bundle))
    errors, warnings = [], []

    check_required_arms(bundle, errors, warnings)
    check_shared_protocol(bundle, errors, warnings)
    check_varied_params_completeness(bundle, errors, warnings)
    check_decision_rule(bundle, errors, warnings)
    check_hashes(bundle, errors, warnings)

    if args.code_dir and "code_hash" in bundle:
        actual = sha256_dir(args.code_dir)
        if actual != bundle["code_hash"]:
            errors.append(f"code_hash mismatch: bundle says {bundle['code_hash'][:24]}…, actual is {actual[:24]}…")

    print("=" * 60)
    print(f"Lineage check: {args.bundle}")
    print("=" * 60)
    print(f"  Arms: {list(bundle.get('arms', {}).keys())}")
    if errors:
        print(f"  ❌ {len(errors)} ERRORS:")
        for e in errors:
            print(f"     • {e}")
    if warnings:
        print(f"  ⚠️  {len(warnings)} warnings:")
        for w in warnings:
            print(f"     • {w}")
    if not errors and not warnings:
        print("  ✅ all checks passed")

    if errors:
        print()
        print("BUNDLE REJECTED — fix errors before launching")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
