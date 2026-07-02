#!/usr/bin/env python3
"""Mechanical verdict for H001.

Reads prereg.json (frozen before any experiment code existed) and the newest
results file, applies the preregistered decision rule with zero judgment
calls, prints the verdict, and records the outcome in the knowledge tree
(hypothesis.json).

Prefers results_v2.json (post-audit). Falls back to results.json with a loud
warning, because pre-audit results are advisory only.
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(HERE, name)) as f:
        return json.load(f)


def pick_results_file():
    if os.path.exists(os.path.join(HERE, "results_v2.json")):
        return "results_v2.json"
    if os.path.exists(os.path.join(HERE, "results.json")):
        print("!" * 68)
        print("! WARNING: results_v2.json not found; falling back to results.json.")
        print("! These results have NOT passed the adversarial audit.")
        print("! Per prereg.json audit_requirement this verdict is ADVISORY ONLY.")
        print("!" * 68)
        return "results.json"
    sys.exit("no results file found -- run: python3 run_bundle.py")


def decide(prereg, res):
    th = prereg["thresholds"]
    arms = res["arms"]
    delta, ci = res["delta"], res["ci95"]
    lo_band, hi_band = th["negative_control_band"]

    if arms["positive_control"] != th["positive_control_exact"]:
        return "PROTOCOL_BROKEN", (
            "positive control %.4f != %.1f: the harness cannot even score a "
            "perfect sampler" % (arms["positive_control"],
                                 th["positive_control_exact"]))
    if not lo_band <= arms["negative_control"] <= hi_band:
        return "PROTOCOL_BROKEN", (
            "negative control %.4f outside chance band [%.2f, %.2f]: "
            "possible label leakage" % (arms["negative_control"],
                                        lo_band, hi_band))
    if delta >= th["min_delta"] and ci[0] > 0:
        return "PROVEN", (
            "delta %+.2fpp >= %.0fpp margin and CI95 [%+.2f, %+.2f]pp "
            "excludes 0" % (100 * delta, 100 * th["min_delta"],
                            100 * ci[0], 100 * ci[1]))
    if delta <= 0:
        return "REFUTED", "delta %+.2fpp <= 0" % (100 * delta)
    reasons = []
    if delta < th["min_delta"]:
        reasons.append("delta %+.2fpp is below the preregistered %.0fpp margin"
                       % (100 * delta, 100 * th["min_delta"]))
    if ci[0] <= 0:
        reasons.append("CI95 [%+.2f, %+.2f]pp includes 0"
                       % (100 * ci[0], 100 * ci[1]))
    return "INSUFFICIENT", " and ".join(reasons)


def main():
    prereg = load("prereg.json")
    rfile = pick_results_file()
    res = load(rfile)
    verdict, why = decide(prereg, res)

    print()
    print("VERDICT: %s   (hypothesis %s, file %s, tie-break: %s)"
          % (verdict, res["hypothesis"], rfile, res["tie_break"]))
    print("rationale: %s" % why)

    hyp = load("hypothesis.json")
    hyp["status"] = verdict
    hyp.setdefault("history", []).append({
        "date": datetime.date.today().isoformat(),
        "results_file": rfile,
        "audited": rfile == "results_v2.json",
        "tie_break": res["tie_break"],
        "delta_pp": round(100 * res["delta"], 2),
        "ci95_pp": [round(100 * res["ci95"][0], 2),
                    round(100 * res["ci95"][1], 2)],
        "verdict": verdict,
        "rationale": why,
    })
    with open(os.path.join(HERE, "hypothesis.json"), "w") as f:
        json.dump(hyp, f, indent=2)
        f.write("\n")
    print("knowledge tree updated: hypothesis.json status -> %s" % verdict)


if __name__ == "__main__":
    main()
