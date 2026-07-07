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

## What counts as evidence

Evidence-based medicine's central instrument is the hierarchy of evidence:
a claim is only as strong as the study design behind it, and anecdotes
don't outrank trials no matter how confident the storyteller. EAIR runs
research on the same instrument. Every number in the system sits at a
level, and every mechanism in this repo exists to move claims up the
ladder — or kill them on the way:

| Level | In medicine | In EAIR | May enter |
|---|---|---|---|
| 0 | anecdote | a model's claim in chat; a heartbeat line; any unaudited number | nowhere — observability only |
| 1 | case report | a worker's structured output (self-tested, not yet audited) | the conductor's decisions |
| 2 | controlled study | a result that survived cross-model adversarial audit | discussion, flagged exploratory |
| 3 | preregistered trial | an audited **bundle** (treatment + baseline + ablation + controls) judged by a rule frozen before the code existed | the ledger (`EVOLUTION.md`, `tree.json`) |
| 4 | systematic review | a level-3 finding reproduced across models / domains / seeds | the findings catalogue — what a paper may claim |

Two consequences run through everything below: numbers cannot skip levels
(an unaudited result never reaches the ledger, however good it looks), and
a claim's wording is capped by its level — "we find evidence of" at level
2 is not "we show" at level 3.

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
  experimenter demand effects. Details below.

## How it's organized

```
user ── observer     talks to the user; reads ledgers and briefs,
          │          never disturbs a running experiment
          ▼
      conductor      unattended; its context holds protocol + disk
          │          state and nothing else; never writes code,
          │          never runs experiments, never self-reviews
          ▼
      workers        Coder → Auditor (different model family) →
                     Engineer → [design gate] → Runner → Writer ...
                     one experiment = one fresh agent
```

The layering is not about division of labor. It's about keeping the
conductor's context sterile. A conductor that chats with the user mid-run
absorbs casual scope changes and — worse — hints about which result the
user would like. Models are sycophantic; "I feel like the effect should be
bigger" is often enough to bend an analysis. Behavioral science calls the
human version experimenter demand effects. Preregistration protects
verdicts from data-driven bias; keeping the user out of the conductor's
context protects them from user-driven bias.

So the user talks to the observer, and three channel rules apply:

1. **Read without disturbing.** The observer answers questions from disk
   artifacts (briefs, ledgers, the knowledge tree); the conductor never
   learns the question was asked.
2. **Influence enters as files, at boundaries.** A change of direction
   becomes an amended task file or config on disk, picked up when the next
   fresh agent rebuilds its context — never injected into a running
   agent's conversation.
3. **Correct by respawn, not conversation.** On a protocol violation the
   misbehaving agent is killed and a fresh one dispatched with a tightened
   task file. The only direct message allowed is a content-free wake
   signal ("the run you were waiting on finished").

Each layer holds only what its decisions need, which keeps every layer in
the short-context regime where models are sharpest:

| Layer | Decision horizon | Context contains |
|---|---|---|
| observer | the whole program + user intent | briefs, ledgers, verdicts |
| conductor | one pipeline | protocol + pipeline state, no transcripts |
| worker | one experiment | one task file + pointers, fresh every time |

Every hop between layers is a file with a schema, not a conversation.
Workers push completion notices to the conductor (control flow needs
latency); the observer only polls the disk (watching doesn't — and an
observer nobody knows about can never contaminate anything). Files carry
trust levels: workers write heartbeats and structured outputs; the
conductor writes dispatch logs and briefs; the scientific ledger
(`EVOLUTION.md`, `tree.json`) is written by the conductor alone, and only
after the audit passes. These are the evidence levels from the table
above, enforced by protocol and checked by the observer: unaudited
numbers never enter the ledger.

Depth scales with risk: a typo fix needs one agent. Add a conductor when
one context can't hold a pipeline; add the observer when the pipeline runs
unattended for hours and you still want to watch and steer safely.

### Escalations work over email

When the conductor hits a stop condition (budget overrun, repeated audit
failures, anything irreversible), it writes an escalation to disk and
stops. The observer relays it to you — including by email:
`conductor/scripts/mail_bridge.py send` mails the decision brief with a
one-time confirmation code (24h lifetime). You reply from any account and
copy the code into your reply text. `mail_bridge.py poll` verifies the
code over IMAP — quoted text is stripped first, so merely echoing the
original mail does not authenticate — and lands your reply as a file the
conductor reads at the next experiment boundary. Your words never touch a
running context, even by email.

### The clock never hallucinates

LLMs have no internal clock. Any timestamp, ETA, or "I'll check back in
ten minutes" they produce without an external anchor is fabrication. So
time is not an LLM job here. `conductor/scripts/pulse.py` is a plain cron
process that ticks every two minutes: it records observed liveness to
`PULSE.jsonl` (newest file mtimes per experiment, GPU utilization, tmux
sessions — measured, not self-reported) and checks a ledger of deadlines
in `alarms/pending/` that any agent registers when it dispatches long
work. Overdue or gone-stale expectations get a line in `ALARMS.jsonl`,
which wakes whoever is watching. The split is strict: the clock records
and fires but never decides; the agents decide but never estimate time.
It also saves tokens — a cron tick is free, so no LLM ever burns a
context re-read just to poll.

### Watch it live

<img width="1139" height="1150" alt="image" src="https://github.com/user-attachments/assets/b84290b2-7333-4b9a-9571-21d32979b150" />



`conductor/scripts/panel.py` serves a single-page console (stdlib only,
zero tokens), polled every 3 s and organized by a bottom tab bar that
mirrors the supervision topology:

- **agent** — one pane per layer. The observer pane shows its status
  chips and context bar, the conversation, and an input box pinned to
  the bottom; messages land in `PANEL_INBOX.jsonl`, which the observer
  tails. The conductor pane is detected among dispatched subagents by
  its role prompt and keeps a scrollable history of everything it has
  reported. The workers table lists every other dispatched agent with
  its context occupancy and latest output, labels read from transcript
  heads so long-running agents never go anonymous.
- **nvitop** — one compact row per GPU (model, temperature, power,
  colored UTL/MEM bars), a utilization history line for all cards, and
  an nvitop-style compute-process table: GPU, PID, user, elapsed time,
  VRAM, command — so you can tell your run from a colleague's at a
  glance.
- **log** — the knowledge tree, experiment verdicts, clock alarms, and
  the progress log.

A second-precision clock sits in the header next to the observer's
context bar. Panes drag to reorder and resize; layout and active tab
persist in the browser. Bind it to a private interface — a tailnet
address or `127.0.0.1` behind an SSH tunnel — never a public one; the
bind address is the only access control:

```
panel.py --project-dir <project> --bind <tailnet-ip> --port 8377 [--gpu-host <alias>]
```

### Language

The observer speaks your language (it's the first setup question, and it
only affects how the system talks to you). Everything below the observer —
conductor, workers, every on-disk artifact — stays in English, where
models are strongest and where the record remains readable to any future
agent regardless of who the user was.

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
Install https://github.com/GuanhuaYe/EAIR-Evidence-Based-AI-Research for me
```

It will clone the repo and run `./install.sh`, which symlinks the skills
into `~/.claude/skills`. No configuration needed.

By hand, if you prefer:

```bash
git clone https://github.com/GuanhuaYe/EAIR-Evidence-Based-AI-Research.git EAIR
cd EAIR && ./install.sh
./install.sh --check
```

Then, in Claude Code:

```
/eair start a multilingual reasoning research project
/eair find  does X actually cause Y in my results?
/eair grill experiments/E01/design.md
/eair status
/eair paper
```

`/eair` is the front door; every skill is also directly invocable by name
(`/big-finding`, `/grill-doc`, `/idea-evaluator`, ...), and plain phrases
like "grill this experiment design" work too.

Your first `/eair start` runs a one-round setup interview: reporting
language first (it only affects how the system talks to you), then a local
GPU probe (`nvidia-smi`) and optional remote cluster, literature-search
API keys, the email loop described above, git backup with a commit at
every experiment boundary, dedicated data/model directories, and whether
the project-intent grilling questions go to the agent (fast) or to you
(strongest intent alignment). Answers land in `.env` and are never asked
again.

Tier 2 — full pipeline on one machine. Copy `.env.example` to `.env` if you
want literature-search APIs and email notification; none of it is required.

Tier 3 — conductor on a CPU host, experiments on remote GPU machines over
SSH. This is how we run it; see [docs/advanced.md](docs/advanced.md). Tiers
1–2 don't need any of it.

## Skills

Entry point:

| Skill | What it does | Status |
|---|---|---|
| `eair` | the front door: routes `start` / `find` / `grill` / `status` / `paper` to the right layer | Stable |

Science layer:

| Skill | What it does | Status |
|---|---|---|
| `big-finding` | hypothesis-driven discovery loop: bundles, preregistered verdicts, append-only knowledge tree | Stable |
| `grill-doc` | evidence-gated design interrogation; quotes machine-checked; the GPU ignition gate | Stable |
| `idea-evaluator` | triage ideas by how cheaply they can be killed; novelty as attackable search queries | Stable |

Execution layer:

| Skill | What it does | Status |
|---|---|---|
| `conductor` | dispatch-only orchestration: hard rules, gates, ledgers | Stable |
| `agents/` | role cards for the specialist agents (Coder, Auditor, Engineer, Runner, ...) | Stable |
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

**Do I need a GPU cluster?** The system is designed for AI research labs
with GPU clusters — that's where the full pipeline (training runs, the GPU
ignition gate, remote runners) earns its keep. Without one you can still do
real work: inference-only experiments through LLM APIs, offline analyses of
existing outputs, and the whole science layer (preregistration, bundles,
audits) applies unchanged.

**Does this require Claude?** The skills never call a model API — they are
protocol documents plus stdlib Python, and the only binding is the harness:
anything that reads markdown skills, spawns subagents, and has file/shell
tools can run them. Claude Code is what we test on. DeepSeek exposes an
Anthropic-compatible API endpoint, so pointing Claude Code at it via
`ANTHROPIC_BASE_URL` should work — untested by us so far. The protocol
itself assumes workers are unreliable regardless of vendor (gates, audits,
and the clock exist for exactly that), so a weaker brain degrades step
quality, not system correctness. As experiment *subjects*, models are
just weights under vLLM — DeepSeek, Qwen, gemma, Llama all alike.

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
