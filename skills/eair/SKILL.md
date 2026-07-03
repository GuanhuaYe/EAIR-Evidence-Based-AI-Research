---
name: eair
description: >-
  Front door for the EAIR research system. Routes a user request to the
  right layer: project scaffolding and the full pipeline (/eair start),
  hypothesis-driven discovery (/eair find), design interrogation
  (/eair grill), status reporting from the ledgers (/eair status), and
  the paper pipeline (/eair paper). Use when the user types /eair, or
  says "start a research project", "set up EAIR", "run the research
  pipeline", or asks what EAIR can do.
license: CC-BY-4.0
user-invocable: true
argument-hint: "<start|find|grill|status|paper> [args]"
---

# /eair — entry point

**You are the observer** (see `observer/SKILL.md`). `/eair` is how the
observer is invoked. You talk to the user; you do NOT become the conductor
and you do NOT dispatch workers yourself. Any subcommand that engages a
project runs the observer startup checklist — start the clock, bring up the
panel, then spawn the conductor as an unattended subagent — and from then
on you relay the conductor's escalations and drop the user's direction
changes as files at experiment boundaries.

One command, five subcommands. Parse the user's argument line; if it
doesn't match a subcommand, ask which one they meant and show the table:

| Command | What happens |
|---|---|
| `/eair start <topic>` | scaffold a project and run the full pipeline from idea triage |
| `/eair find <question or anomaly>` | big-finding discovery loop (bundles, preregistered verdicts, knowledge tree) |
| `/eair grill <path/to/design.md>` | evidence-gated interrogation of a design doc before anything expensive runs |
| `/eair status` | report pipeline state from the ledgers, read-only |
| `/eair paper` | enter the paper layer for a project with verified results |

## /eair start <topic>

1. **First-run interview** (skip questions already answered in `.env` /
   `~/.eair/config`; batch the rest into ONE round, don't drip-feed):
   - **Language — always the first question**: which language should
     user-facing reporting use? Ask it in the language the user is
     already typing, and say explicitly that this choice affects ONLY
     how the system talks to them (the observer) — the research pipeline
     itself (conductor, workers, all on-disk protocol artifacts) runs in
     English regardless, where models perform best. Then conduct the
     rest of the interview in their choice.
   - **Compute**: probe local GPUs first (`nvidia-smi`), report what you
     found, then ask about a remote GPU cluster (ssh alias, test it with
     `ssh <alias> nvidia-smi`). No GPU at all is fine — offer API-only
     mode (inference experiments through LLM APIs).
   - **Literature APIs**: Semantic Scholar / SerpAPI keys for novelty
     checks and citation verification (optional, degrade gracefully).
   - **Email loop**: progress notifications wanted? If yes, collect SMTP
     settings, send a test mail via
     `conductor/scripts/mail_bridge.py send`, and explain the reply-back
     channel: escalation mails carry a one-time confirmation code (24h
     TTL); the user replies from any account and copies the code into
     the reply text; `mail_bridge.py poll` (cron or watcher) verifies
     the code (quoted text stripped) and lands the reply in
     `<project>/escalations/<token>-reply.md`, where the conductor
     reads it at the next experiment boundary. Human decisions arrive
     as files, never as chat.
   - **Git**: use git for backup and rollback? If yes: init the project
     repo, commit at every experiment boundary (post-verdict), tag
     decision points so any experiment state can be recovered.
   - **Paths**: dedicated directories for datasets and model weights
     (shared mounts, scratch disks) instead of the home directory —
     record as `MODELS_DIR` / `DATA_DIR`.
   - **Intent grilling mode**: before the pipeline starts, the project
     intent gets grilled. Default: the agent answers the interrogation
     from the user's inputs (fast). Option: the questions go to the USER
     directly — slower, but buys the strongest human-AI intent alignment.
     Offer the choice explicitly.
   - Also ask: target venue or "no venue, discovery only"; rough time
     budget. Write everything to `.env` + the project config, so the
     interview never repeats.
2. Scaffold the project root:
   ```
   <project>/
     tree.json           # empty knowledge tree {nodes:{}, experiments:{}}
     EVOLUTION.md        # ledger header + comparability rules + empty veto list
     CONDUCTOR_LOG.json    # {"entries": []}
     HEARTBEAT.jsonl     # empty
     experiments/
   ```
3. Fill an autonomy contract with the user (see
   `research-autonomy-contract` skill) so unattended stretches have
   defined escalation rules.
4. Run the observer startup checklist (see `observer/SKILL.md`) — you are
   the observer, not the conductor:
   a. **Start the clock**: install `conductor/scripts/pulse.py` on cron
      (every 2 min) for the project so time is machine-anchored, not
      LLM-guessed; confirm it writes `PULSE.jsonl`.
   b. **Bring up the panel**: `conductor/scripts/panel_ctl.sh switch
      <project-dir>`, then report the tailnet URL.
   c. **Spawn the conductor** as an unattended background subagent whose
      context is sterile (protocol + disk state only): its prompt tells it
      to read `conductor/SKILL.md` and run Stage 1 (idea triage via
      `idea-evaluator`, kill-cheap first), then the mandatory experiment
      chain. Every experiment goes through `big-finding` bundle rules — no
      single-arm runs, verdict rules preregistered. You do NOT become the
      conductor; you relay its escalations to the user and drop direction
      changes as files at experiment boundaries.

## /eair find <question>

Skip venue concerns. Run the observer checklist (clock, panel, conductor),
then the spawned conductor drives the `big-finding/SKILL.md` loop:
formulate the falsifiable hypothesis, preregister the decision rule, design
the bundle, dispatch one fresh worker per experiment, apply the verdict
mechanically, update the tree. As observer you relay each verdict to the
user — PROVEN / REFUTED / INSUFFICIENT / CONFOUNDED with the numbers, not a
narrative — and pass new questions to the conductor as files. (For a quick
one-off hypothesis with no running pipeline, you may drive the loop
inline; but anything long-running or unattended goes through the
conductor subagent so your context stays the observer's.)

## /eair grill <doc>

Read `grill-doc/SKILL.md` and run it on the given file. Output is the
gate verdict (PASS / BLOCK) plus the gap list. If the user gives no path,
ask for one — grilling requires a document, not a conversation.

## /eair status

Observer behavior, strictly read-only: read `CONDUCTOR_LOG.json`,
`SUPERVISOR_BRIEF.md` (if present), `tree.json`, the tail of
`HEARTBEAT.jsonl`, and the latest `EVOLUTION.md` entry. Summarize: current
stage, last verdict, running work, blockers. Do not dispatch anything, do
not write anything.

## /eair paper

Requires a project with at least one audited, tree-recorded result. Run
the observer checklist, then the spawned conductor drives the paper layer
in order: `tech-paper-template` (claim graph) → `intro-drafter` → Writer
worker per section → `citation-verifier` → `figure-designer` /
`figure-coder` → `pre-submission-reviewer` → `reviewer-panel`. Producer and
reviewer are different model families. As observer you relay gate outcomes
to the user; you do not draft sections yourself.
If the project has no audited results, say so and point to `/eair find`.

## Rules that apply to every subcommand

- The individual skills are also directly invocable (`/big-finding`,
  `/grill-doc`, `/idea-evaluator`, ...); this command is a router, not a
  replacement.
- **Every subcommand that engages a project (`start`, `find`, `paper`, or
  resuming/switching work) runs the observer startup checklist** (see
  `observer/SKILL.md`): start the clock (`pulse.py` cron), bring up the
  panel (`panel_ctl.sh switch <project-dir>`, report the URL), then spawn
  the conductor as an unattended subagent. The clock and frontend follow
  the active project automatically; the observer never has to be asked "is
  the clock/frontend up?". `status` is read-only and may skip the checklist.
- Follow the supervision topology (README, "How it's organized"): fresh agent per experiment, structured files between layers,
  unaudited numbers never enter `EVOLUTION.md`.
- When a subcommand needs a long-running unattended conductor, offer it
  explicitly ("run unattended and report at gates?") rather than assuming.

## Acknowledgments

Part of EAIR (Evidence-Based AI Research). See the repo's
`docs/ACKNOWLEDGMENTS.md` for inspirations.
