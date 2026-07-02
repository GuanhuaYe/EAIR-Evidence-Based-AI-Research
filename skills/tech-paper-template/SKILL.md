---
name: tech-paper-template
description: >-
  Builds a Claim-Graph Skeleton for a technical paper before any prose
  is drafted: a directed acyclic graph of typed claims (GAP, CAUSE,
  INSIGHT, MECHANISM, RESULT), each carrying a one-sentence statement,
  a named evidence artifact, and a computed status. Emits the graph, a
  1:1:1:1 alignment matrix (challenge : module : experiment : figure),
  a red-flag report of named structural defects, a contribution
  spectrum position, and a machine-readable JSON payload for
  downstream drafting agents. Use for pre-drafting paper structuring,
  logic audits of a planned paper, or when asked for a "claim graph",
  "paper skeleton", or "argument structure".
license: CC-BY-4.0
---

# Tech Paper Template — Claim-Graph Skeleton

## Overview

A technical paper is not a form to fill in; it is an argument. This
skill models the argument explicitly as a directed acyclic graph of
typed claims connected by "therefore" edges. Every claim must name
the artifact that would prove it, and every claim gets a status that
is computed from that artifact's existence — never asserted from
optimism. The skeleton is falsifiable by construction: a reviewer
(or a downstream agent) can walk the graph and see exactly which
links hold, which are promises, and which are holes.

Run this skill after the idea has been vetted and before any section
prose is written. Its outputs are consumed by two downstream
consumers:

- an introduction-drafting step, which turns the graph's spine into
  an Introduction paragraph plan;
- a Writer agent, which uses the alignment matrix and JSON payload
  to keep sections, experiments, and figures in lockstep while
  drafting.

The skill does not draft prose and does not evaluate whether the
idea is good. It evaluates whether the argument, as planned, is
structurally sound and fully evidenced.

## When to use

- The idea is settled and drafting is about to begin.
- A draft-in-progress feels like a pile of parts; you need to audit
  the argument before rewriting.
- A collaborator asks "what exactly does this paper claim, and what
  proves each claim?"
- You need a machine-readable structure for downstream drafting
  automation.

## When not to use

- The idea itself is still in doubt — vet it first with an
  idea-evaluation step.
- You need Introduction prose or a paragraph-by-paragraph outline —
  run this skill first, then the intro-drafting step on its output.
- The artifact is a benchmark or dataset paper — its argument
  structure (coverage, construction validity, baseline sweep) needs
  a different graph grammar than the one defined here.

## The claim graph

### Node types

| Type | Question it answers | Typical evidence artifact |
|---|---|---|
| `GAP` | What is broken or missing in prior work? | Citations to the works that exhibit the failure; a reproduction |
| `CAUSE` | Why is it broken? The diagnosis, not the symptom. | An analysis experiment, an ablation of prior work, or a proof |
| `INSIGHT` | What one non-obvious observation makes a fix possible? | A pilot measurement, a counterexample, a derivation |
| `MECHANISM` | What technical move exploits the insight? | The implemented module; its design rationale in the method section |
| `RESULT` | What measured payoff does the mechanism deliver? | A specific experiment with metric, dataset, and comparison |

### Node fields

Every node carries exactly three fields:

1. **statement** — one declarative sentence. If it takes two
   sentences, it is two nodes. If it cannot be phrased as something
   a skeptic could deny, it is not a claim and does not belong in
   the graph.
2. **evidence** — the named artifact that would settle the claim:
   an experiment ID, a citation, or a proof/derivation. "The
   experiments section" is not a name; "E3: latency vs. batch size
   on setup X" is.
3. **status** — computed, never vibed:
   - `VERIFIED` (green) — the evidence artifact exists and has been
     inspected in this session or is a published citation.
   - `PLANNED` (yellow) — the artifact is specified precisely enough
     to execute (what is run, on what, measuring what) but does not
     exist yet.
   - `MISSING` (red) — no artifact is named, or the named artifact
     could not confirm the statement even if it existed.

Status computation rule: read only the evidence field. If the user
says "we're confident this will work" but names no artifact, the
status is `MISSING`. Confidence is not a data source.

### Edges

Edges are directed "therefore" links: `A -> B` asserts "given A,
therefore B." The canonical spine is

```
GAP -> CAUSE -> INSIGHT -> MECHANISM -> RESULT
```

but real papers have multiple GAPs, branching MECHANISMs, and
several RESULTs. The graph must be acyclic and every edge must pass
the **adversarial reading test**: imagine the most hostile competent
reviewer reading "A, therefore B." If they can interpose a plausible
"or, alternatively..." that breaks the inference, the edge is weak
— either add the missing intermediate node or delete the edge and
accept the consequences in the red-flag scan.

Well-formedness constraints:

- A `MECHANISM` must have at least one `INSIGHT` ancestor.
- A `CAUSE` must have at least one `GAP` parent.
- A `RESULT` must have at least one `MECHANISM` parent.
- Back-edges (e.g., `RESULT -> INSIGHT`) are forbidden; if a result
  motivated the insight historically, that is fine — the graph
  records the argument, not the discovery order.

## Procedure

### Step 1: Harvest candidate claims

From the user's notes, idea document, or conversation, extract every
sentence that a skeptic could deny. Rewrite each as a single
declarative statement. Discard motivation-flavored filler ("X is an
important area") — importance claims that no one would deny carry no
argumentative load.

### Step 2: Type and connect

Assign each claim a node type. Then draw the "therefore" edges,
applying the adversarial reading test to each. Where the test fails,
either elicit the missing intermediate claim from the user or record
the hole. Verify acyclicity and the well-formedness constraints.

### Step 3: Compute statuses

For each node, demand the evidence field, then compute the status
from the rules above. Do not let the user set a status directly;
they supply artifacts, the skill supplies colors.

### Step 4: Build the alignment matrix

For each `MECHANISM` node, identify the **challenge** it defeats:
the specific obstacle, traceable to a `CAUSE` node, that makes the
naive exploitation of the `INSIGHT` fail. Then enforce the 1:1:1:1
discipline — each row of the matrix binds exactly:

| Challenge | Mechanism module | Experiment | Figure |
|---|---|---|---|

one challenge, to one mechanism module, to one experiment that
demonstrates the module earns its keep (usually an ablation), to one
figure or table that a reader will actually see. An empty cell in
any column is a defect, reported in Step 5. A module serving two
challenges, or a challenge needing two modules, means the
decomposition is at the wrong granularity — split or merge until
rows are 1:1:1:1.

### Step 5: Red-flag scan

Scan the graph and matrix for the named anti-patterns in
`references/red-flag-catalogue.md`. The four cardinal flags:

- **Orphan module** — a mechanism module bound to no challenge. It
  exists because it was built, not because the argument needs it.
- **Unsupported claim** — a `RESULT` node with status `MISSING`.
  The paper promises a payoff no planned artifact can show.
- **Insight-free paper** — a `MECHANISM` with no `INSIGHT` ancestor.
  The paper reads as "we tried X and it worked": reviewers can
  accept the numbers and still reject the paper.
- **Diagnosis gap** — a `GAP` with no `CAUSE` child. The paper
  attacks a symptom; a competing paper with the diagnosis will
  obsolete it.

Every flag is reported with the node/row it implicates and the
minimal repair (add a node, name an artifact, delete a module, run
an analysis experiment).

### Step 6: Position on the contribution spectrum

Locate the contribution's **center of mass** on a four-stop
spectrum, and state in one sentence what the paper must therefore
prove hardest:

| Center of mass | The paper's heaviest burden of proof |
|---|---|
| **New problem** | That the problem is real, well-posed, and not already solved under another name |
| **New diagnosis** | That the identified cause — not a confound — actually produces the observed failure |
| **New mechanism** | That the mechanism beats the strongest fair baseline and each module earns its keep |
| **New capability** | That the capability is demonstrated end-to-end, not extrapolated from a proxy |

A paper can have mass at several stops, but its center sits at one.
The center of mass determines which nodes must reach `VERIFIED`
before submission and which experiments are load-bearing.

### Step 7: Emit

Produce the four human-readable deliverables (graph table +
adjacency, alignment matrix, red-flag report, positioning) followed
by the JSON payload. Statuses appear as `VERIFIED` / `PLANNED` /
`MISSING` with the green/yellow/red legend stated once.

## Output format

### 1. Claim graph

Nodes:

| ID | Type | Statement | Evidence | Status |
|---|---|---|---|---|
| G1 | GAP | ... | [cite] Smith et al. 2025 | VERIFIED |
| C1 | CAUSE | ... | E1: failure-mode ablation | PLANNED |
| I1 | INSIGHT | ... | E2: pilot measurement | VERIFIED |
| M1 | MECHANISM | ... | Sec. 4.1 module | PLANNED |
| R1 | RESULT | ... | E3: main benchmark run | PLANNED |

Adjacency (therefore-edges): `G1 -> C1`, `C1 -> I1`, `I1 -> M1`,
`M1 -> R1`, ...

Legend: VERIFIED = green (artifact exists), PLANNED = yellow
(artifact specified, not yet run), MISSING = red (no artifact).

### 2. Alignment matrix

| # | Challenge | Mechanism module | Experiment | Figure |
|---|---|---|---|---|
| 1 | ... | M1 (Sec 4.1) | E4 ablation | Fig. 3 |

Orphans (empty cells) listed beneath the table as defects.

### 3. Red-flag report

One line per flag: `<flag name> — <implicated node/row> — <minimal
repair>`. If none: "No red flags; skeleton is submission-shaped."

### 4. Positioning

- Center of mass: `<new problem | new diagnosis | new mechanism |
  new capability>`
- Hardest thing to prove: `<one sentence>`

### 5. JSON payload (for downstream agents)

```json
{
  "nodes": [
    {"id": "G1", "type": "GAP", "statement": "...",
     "evidence": {"kind": "citation|experiment|proof", "ref": "..."},
     "status": "VERIFIED|PLANNED|MISSING"}
  ],
  "edges": [
    {"from": "G1", "to": "C1", "relation": "therefore"}
  ],
  "alignment_matrix": [
    {"challenge": "...", "module": "M1", "experiment": "E4",
     "figure": "Fig. 3", "orphan_columns": []}
  ],
  "red_flags": [
    {"flag": "diagnosis-gap", "implicates": ["G2"],
     "repair": "..."}
  ],
  "positioning": {
    "center_of_mass": "new_problem|new_diagnosis|new_mechanism|new_capability",
    "hardest_proof": "..."
  }
}
```

The JSON must round-trip: every table row above appears in the
payload and vice versa. Downstream agents treat the payload as the
source of truth; the tables are its human projection.

## House rules

- **Falsifiability first.** A statement no skeptic could deny is not
  a claim; cut it or sharpen it until denial is possible.
- **Every claim names its evidence.** No node ships with an empty
  evidence field — an empty field means status `MISSING`, and the
  node stays in the graph so the hole is visible.
- **Statuses are computed, not vibed.** The only inputs to a status
  are the evidence artifact's existence and its ability to settle
  the statement. Enthusiasm, deadlines, and advisor pressure are not
  inputs.
- **The graph outranks the prose.** When drafting later reveals a
  claim the graph does not license, the fix is a graph revision run
  through this skill again — not a quietly hedged sentence.

## Acknowledgments

The pipeline role of this skill — structuring a technical paper's
argument before drafting, feeding an introduction-drafting step and
a Writer agent — is inspired by HKUSTDial's Supervisor-Skills
project. The Claim-Graph Skeleton framework, its node grammar,
alignment discipline, red-flag catalogue, and output contract are an
independent redesign.
