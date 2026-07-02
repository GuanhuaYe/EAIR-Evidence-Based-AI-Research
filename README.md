# EAIR — Evidence-Based AI Research

> An AI research lab that kills its own bad results.

Most AI-scientist projects optimize throughput: more ideas, more runs, more
papers per day. We kept hitting the opposite problem in our own lab — results
came fast, and a week later some of them fell apart under a second look. The
expensive part was never generating results; it was finding out which ones to
trust.

Evidence-based medicine dealt with this decades ago: preregistration,
mandatory controls, systematic review. EAIR applies that discipline to
AI-driven research. It runs on Claude Code as a set of skills plus a
multi-agent pipeline, and we use it daily on our own papers.

The design rule behind everything here: when a decision matters, don't let a
language model make it by feel. Write the rule down first, then compute the
verdict.

## What that means concretely

- Decision rules are preregistered. Before experiment code exists, the
  PROVEN / REFUTED / INSUFFICIENT / CONFOUNDED thresholds are written into a
  task file. After the run, the rule is applied as written. Nobody
  renegotiates thresholds after seeing the numbers, including the model.
- Single-arm experiments are rejected. Every run is a bundle: treatment,
  baseline, at least one ablation, a positive control and a negative
  control, all under one protocol hash and seed list.
- The model that writes code never reviews it. Production and audit go to
  different model families, and the auditor's job description is to attack.
- Experiment designs are interrogated before GPUs run. `grill-doc` makes a
  defender agent answer a fixed question manual using only verbatim quotes
  from the design doc; a script checks every quote against the file and
  computes PASS or BLOCK. A BLOCK means the runner is not dispatched.
- Dead ends are recorded. Each project keeps an append-only ledger
  (`EVOLUTION.md`) with exact conditions and metrics, plus a veto list of
  directions that were killed and the evidence that killed them. Gates read
  the veto list before approving anything.
- One experiment, one agent. Each bundle runs in a freshly spawned agent;
  results, decision and tree update are written to disk, then the agent is
  closed. The next experiment starts clean, rebuilt from the tree and
  ledger. A small fresh context keeps the model sharp, and an agent that
  never saw experiment N-1 can't steer experiment N toward consistency.
- The user never chats with the conductor. An observer agent answers the
  user from disk artifacts and injects changes only as protocol files at
  experiment boundaries — user remarks mid-run are the LLM version of
  experimenter demand effects. See
  [docs/supervision-topology.md](docs/supervision-topology.md).

## See the loop run

`examples/one-loop` walks the whole loop on a toy task in about five
minutes, offline, stdlib only, planted bug included. The buggy harness
reports +5.84pp and passes the preregistered bar (PROVEN). The audit report
catches a biased tie-break — 19 tie-decided questions out of 300, all 19
resolved toward the gold answer — the fix drops the effect to +2.84pp, and
the same frozen rule now reads INSUFFICIENT. Same data, same rule, opposite
verdict. The controls pass in both runs; only reading the code adversarially
catches this class of bug, which is the point of the audit step.

```bash
cd examples/one-loop && cat README.md
```

## How this compares

The systems below are good at what they optimize for. It just isn't the same
thing.

| | AI scientists (AI Scientist, Agent Laboratory, Kosmos, ...) | Rigor frameworks (Curie, ...) | EAIR |
|---|---|---|---|
| Optimizes | throughput | execution reliability | whether conclusions survive audit |
| Experiment | single run | controlled execution | bundle with mandatory controls |
| Verdict | model writes the conclusion | model interprets the result | preregistered rule, applied mechanically |
| Review | self-review, if any | same-family agent checks | cross-model, adversarial, by hard rule |
| Negative results | discarded | logged | veto list, read at every gate |

Kosmos reports 79.4% statement-level accuracy for its research reports —
they measured it, which is more than most. That remaining 20% is the
problem EAIR is built around.

## Install

Type this line to your agent:

```
Install https://github.com/GuanhuaYe/EAIR for me
```

It will clone the repo and run `./install.sh`, which symlinks the skills
into `~/.claude/skills`. No configuration needed.

By hand, if you prefer:

```bash
git clone https://github.com/GuanhuaYe/EAIR.git
cd EAIR && ./install.sh
./install.sh --check
```

Then, in Claude Code: "grill this experiment design", "evaluate this idea",
or "I want a real finding, not a paper" (starts big-finding).

Tier 2 — full pipeline on one machine. Copy `.env.example` to `.env` if you
want literature-search APIs and email notification; none of it is required.

Tier 3 — conductor on a CPU host, experiments on remote GPU machines over
SSH. This is how we run it; see [docs/advanced.md](docs/advanced.md). Tiers
1–2 don't need any of it.

## Skills

Science layer:

| Skill | What it does | Status |
|---|---|---|
| `big-finding` | hypothesis-driven discovery loop: bundles, preregistered verdicts, append-only knowledge tree | Stable |
| `grill-doc` | evidence-gated design interrogation; quotes machine-checked; the GPU ignition gate | Stable |
| `idea-evaluator` | triage ideas by how cheaply they can be killed; novelty as attackable search queries | Stable |

Execution layer:

| Skill | What it does | Status |
|---|---|---|
| `maestro` | the conductor: dispatch-only orchestration, hard rules, gates, ledgers | Stable |
| `agents/` | role cards for the 12 specialists (Coder, Auditor, Engineer, Runner, ...) | Stable |
| `supervisor` | gate decisions and checkpoint logic | Stable |
| `research-autonomy-contract` | when the pipeline may proceed alone vs must ask a human | Beta |

Paper layer (for when a finding is ready to ship):

| Skill | What it does | Status |
|---|---|---|
| `tech-paper-template` | paper skeleton as a graph of claims, each with an evidence artifact | Stable |
| `benchmark-paper-template` | audits a benchmark as a measurement instrument | Stable |
| `intro-drafter` | intro outline built from predicted reviewer objections | Stable |
| `figure-designer` | one claim per figure, 10-second test, computed QC | Stable |
| `figure-coder` | venue-aware figure code from the designer's specs | Stable |
| `pre-submission-reviewer` | five evidence-cited sweeps + regression re-audit of revisions | Stable |
| `citation-verifier` | do the cited papers exist, and do they say what the text claims | Stable |
| `venue-aware-polishing` | prose pass per venue family | Stable |
| `reviewer-panel` | three-persona + AC dry run | Stable |
| `rebuttal-drafter` | triage table → rebuttal within venue budget | Stable |
| `data-card` | reproducibility checklist / datasheet / AE package | Stable |

## FAQ

**Is this just prompts?** The skill files are prompts. The verdicts aren't:
grill-doc's gate is a script that substring-checks every quote against the
source file, and PASS/BLOCK is computed from the tag table. Same for the
file registry and the demo's verdict step.

**Do I need a GPU cluster?** No. Tier 1 is markdown only, and the science
layer works on purely offline analyses.

**Why cross-model review?** Because same-model self-review rubber-stamps.
We tried it. The planted bug in the demo is the kind of thing a hostile
second family catches and a friendly self-review doesn't.

**Why keep a veto list?** Because pipelines re-walk dead ends. A direction
killed with evidence stays killed until new causal-grade evidence shows up;
the list is read at every gate.

## Contributing, credits, license

Contribution rules: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).
Inspirations: [docs/ACKNOWLEDGMENTS.md](docs/ACKNOWLEDGMENTS.md).
Code is Apache-2.0, skill documents CC-BY-4.0
([LICENSE](LICENSE), [docs/LICENSE-DOCS.md](docs/LICENSE-DOCS.md)).
Citation info: [CITATION.cff](CITATION.cff).
