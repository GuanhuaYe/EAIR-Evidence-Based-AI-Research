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

1. Ask (once, batched) anything genuinely missing: target venue or "no
   venue, discovery only"; compute available (none / local GPU / remote
   over SSH); rough time budget.
2. Scaffold the project root:
   ```
   <project>/
     tree.json           # empty knowledge tree {nodes:{}, experiments:{}}
     EVOLUTION.md        # ledger header + comparability rules + empty veto list
     MAESTRO_LOG.json    # {"entries": []}
     HEARTBEAT.jsonl     # empty
     experiments/
   ```
3. Fill an autonomy contract with the user (see
   `research-autonomy-contract` skill) so unattended stretches have
   defined escalation rules.
4. Hand control to the conductor protocol: read `maestro/SKILL.md` and run
   Stage 1 (idea triage via `idea-evaluator`, kill-cheap first), then the
   mandatory experiment chain. Every experiment goes through `big-finding`
   bundle rules — no single-arm runs, verdict rules preregistered.

## /eair find <question>

Skip venue concerns. Read `big-finding/SKILL.md` and execute the loop
directly: formulate the falsifiable hypothesis, preregister the decision
rule, design the bundle, dispatch one fresh agent per experiment, apply
the verdict mechanically, update the tree. Report PROVEN / REFUTED /
INSUFFICIENT / CONFOUNDED with the numbers, not a narrative.

## /eair grill <doc>

Read `grill-doc/SKILL.md` and run it on the given file. Output is the
gate verdict (PASS / BLOCK) plus the gap list. If the user gives no path,
ask for one — grilling requires a document, not a conversation.

## /eair status

Observer behavior, strictly read-only: read `MAESTRO_LOG.json`,
`SUPERVISOR_BRIEF.md` (if present), `tree.json`, the tail of
`HEARTBEAT.jsonl`, and the latest `EVOLUTION.md` entry. Summarize: current
stage, last verdict, running work, blockers. Do not dispatch anything, do
not write anything.

## /eair paper

Requires a project with at least one audited, tree-recorded result.
Run the paper layer in order: `tech-paper-template` (claim graph) →
`intro-drafter` → Writer agent per section → `citation-verifier` →
`figure-designer` / `figure-coder` → `pre-submission-reviewer` →
`reviewer-panel`. Producer and reviewer are different model families.
If the project has no audited results, say so and point to `/eair find`.

## Rules that apply to every subcommand

- The individual skills are also directly invocable (`/big-finding`,
  `/grill-doc`, `/idea-evaluator`, ...); this command is a router, not a
  replacement.
- Follow the supervision topology (`docs/supervision-topology.md` in the
  repo): fresh agent per experiment, structured files between layers,
  unaudited numbers never enter `EVOLUTION.md`.
- When a subcommand needs a long-running unattended conductor, offer it
  explicitly ("run unattended and report at gates?") rather than assuming.

## Acknowledgments

Part of EAIR (Evidence-Based AI Research). See the repo's
`docs/ACKNOWLEDGMENTS.md` for inspirations.
