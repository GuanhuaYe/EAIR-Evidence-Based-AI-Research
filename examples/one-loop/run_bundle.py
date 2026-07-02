#!/usr/bin/env python3
"""H001 experiment bundle: does majority voting over k=15 noisy samplers
beat a single sampler?

Per the big-finding protocol, every arm runs on the SAME questions and the
SAME sampler draws (fixed seeds):

  treatment         vote@15    plurality vote over all 15 samplers
  baseline          single     mean per-sampler accuracy (same draws)
  ablation          vote@5     plurality vote over the first 5 samplers
  negative_control  shuffled   treatment predictions vs. random labels (~chance)
  positive_control  noiseless  vote over 15 error-free samplers (must be 1.0)

Default run writes results.json.  --fixed switches the vote tie-break to a
seeded random choice among tied answers and writes results_v2.json.
"""
import argparse
import json
import os
import random
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20260702
N_Q = 300            # questions
K = 15               # samplers
N_OPT = 5            # answer options per question (1 gold + 4 distractors)
SYS_FRAC = 0.72      # fraction of questions with systematic (clustered) errors
CLUSTER_P = 0.83     # on systematic questions, wrong answers hit one distractor
P_SYS = (0.42, 0.49) # per-question correctness prob, systematic questions
P_IND = (0.93, 0.99) # per-question correctness prob, independent-error questions
N_BOOT = 2000        # bootstrap resamples (preregistered)


def build_questions():
    rng = random.Random(SEED)
    qs = []
    for i in range(N_Q):
        opts = ["q%03d_opt%d" % (i, j) for j in range(N_OPT)]
        sys_err = rng.random() < SYS_FRAC
        lo, hi = P_SYS if sys_err else P_IND
        qs.append({"gold": opts[0], "opts": opts, "p": rng.uniform(lo, hi),
                   "sys": sys_err, "cluster": opts[1 + rng.randrange(N_OPT - 1)]})
    return qs


def sample_answers(qs):
    rng = random.Random(SEED + 1)
    table = []
    for q in qs:
        wrong = [o for o in q["opts"] if o != q["gold"]]
        row = []
        for _ in range(K):
            if rng.random() < q["p"]:
                row.append(q["gold"])
            elif q["sys"] and rng.random() < CLUSTER_P:
                row.append(q["cluster"])
            else:
                row.append(wrong[rng.randrange(len(wrong))])
        table.append(row)
    return table


def vote(row, mode, rng=None):
    """Plurality vote over one row of sampler answers."""
    counts = Counter(row)
    if mode == "default":
        # sort by count desc, then by answer id, so results are reproducible
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    top = max(counts.values())
    tied = sorted(a for a, c in counts.items() if c == top)
    if mode == "reversed":  # audit probe: the opposite deterministic tie-break
        return tied[-1]
    # mode == "fixed": seeded random choice among tied answers
    return tied[0] if len(tied) == 1 else tied[rng.randrange(len(tied))]


def accuracy(preds, qs):
    return sum(p == q["gold"] for p, q in zip(preds, qs)) / len(qs)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fixed", action="store_true",
                    help="use corrected seeded-random tie-break; write results_v2.json")
    args = ap.parse_args()
    mode = "fixed" if args.fixed else "default"

    qs = build_questions()
    table = sample_answers(qs)

    # treatment: vote@15, with tie diagnostics
    tie_rng = random.Random(SEED + 2)
    treat = []
    ties = {"n_tie_questions": 0, "n_ties_containing_gold": 0,
            "n_ties_resolved_to_gold": 0}
    for q, row in zip(qs, table):
        counts = Counter(row)
        top = max(counts.values())
        tied = sorted(a for a, c in counts.items() if c == top)
        pick = vote(row, mode, tie_rng)
        if len(tied) > 1:
            ties["n_tie_questions"] += 1
            if q["gold"] in tied:
                ties["n_ties_containing_gold"] += 1
                if pick == q["gold"]:
                    ties["n_ties_resolved_to_gold"] += 1
        treat.append(pick)

    # treatment accuracy under every tie-break rule (auditors probe this)
    rng_sr = random.Random(SEED + 2)
    by_tb = {
        "lex_smallest": accuracy([vote(r, "default") for r in table], qs),
        "lex_largest": accuracy([vote(r, "reversed") for r in table], qs),
        "seeded_random": accuracy([vote(r, "fixed", rng_sr) for r in table], qs),
    }

    # baseline: mean per-sampler accuracy on the same draws
    single_rate = [sum(a == q["gold"] for a in row) / K
                   for q, row in zip(qs, table)]
    base_acc = sum(single_rate) / N_Q

    # ablation: vote@5 (first five samplers)
    abl_rng = random.Random(SEED + 5)
    abl_acc = accuracy([vote(row[:5], mode, abl_rng) for row in table], qs)

    # negative control: score treatment predictions against shuffled labels
    rng_neg = random.Random(SEED + 3)
    shuf_gold = [q["opts"][rng_neg.randrange(N_OPT)] for q in qs]
    neg_acc = sum(p == g for p, g in zip(treat, shuf_gold)) / N_Q

    # positive control: 15 noiseless samplers -> vote must be exactly 1.0
    pos_rng = random.Random(SEED + 6)
    pos_acc = accuracy([vote([q["gold"]] * K, mode, pos_rng) for q in qs], qs)

    # paired bootstrap CI95 on delta = acc(vote@15) - acc(single)
    t_corr = [1.0 if p == q["gold"] else 0.0 for p, q in zip(treat, qs)]
    d = [t - s for t, s in zip(t_corr, single_rate)]
    delta = sum(d) / N_Q
    rng_b = random.Random(SEED + 4)
    boots = sorted(sum(d[rng_b.randrange(N_Q)] for _ in range(N_Q)) / N_Q
                   for _ in range(N_BOOT))
    ci95 = [boots[int(0.025 * N_BOOT)], boots[int(0.975 * N_BOOT) - 1]]

    res = {
        "hypothesis": "H001", "seed": SEED, "n_questions": N_Q, "k": K,
        "mode": mode,
        "tie_break": "sorted-(count desc, answer id)" if mode == "default"
                     else "seeded random among tied",
        "arms": {"treatment_vote15": round(accuracy(treat, qs), 4),
                 "baseline_single": round(base_acc, 4),
                 "ablation_vote5": round(abl_acc, 4),
                 "negative_control": round(neg_acc, 4),
                 "positive_control": round(pos_acc, 4)},
        "delta": round(delta, 4),
        "ci95": [round(ci95[0], 4), round(ci95[1], 4)],
        "diagnostics": dict(ties, treatment_acc_by_tiebreak={
            k2: round(v, 4) for k2, v in by_tb.items()}),
    }
    out = os.path.join(HERE, "results_v2.json" if args.fixed else "results.json")
    with open(out, "w") as f:
        json.dump(res, f, indent=2)

    print("bundle mode: %s (tie-break: %s)" % (mode, res["tie_break"]))
    for arm, val in res["arms"].items():
        print("  %-18s %6.2f%%" % (arm, 100 * val))
    print("  delta (vote@15 - single) = %+.2fpp, CI95 [%+.2f, %+.2f]pp"
          % (100 * delta, 100 * ci95[0], 100 * ci95[1]))
    print("  ties: %d questions decided by tie-break (%d contained gold)"
          % (ties["n_tie_questions"], ties["n_ties_containing_gold"]))
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
