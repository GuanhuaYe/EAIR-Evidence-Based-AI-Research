# Red-flag catalogue: named anti-patterns in claim graphs

Each entry gives the detection rule (mechanical, runnable against
the JSON payload), why reviewers punish it, and the minimal repair.
The four cardinal flags come first; the rest are secondary flags
worth reporting when found.

## Cardinal flags

### 1. Orphan module

- **Detect:** an alignment-matrix row (or a `MECHANISM` component)
  whose Challenge cell is empty; equivalently, a module that no
  `CAUSE`-traceable obstacle demands.
- **Why it kills papers:** reviewers read an unmotivated module as
  complexity added to look substantial. It invites "did you ablate
  this?" — and the ablation usually shows it does nothing.
- **Repair:** either surface the real challenge it defeats (then
  bind an ablation and a figure to it), or delete the module and
  simplify the method. Deletion is a valid, often correct, outcome.

### 2. Unsupported claim

- **Detect:** any `RESULT` node with status `MISSING`.
- **Why it kills papers:** the abstract will promise a payoff that
  no experiment in the paper can show. Reviewers quote the promise
  back verbatim in the rejection.
- **Repair:** specify the experiment precisely (metric, dataset,
  comparison, expected direction) to promote the node to `PLANNED`,
  or demote the claim out of the paper's promises.

### 3. Insight-free paper

- **Detect:** a `MECHANISM` node with no `INSIGHT` ancestor anywhere
  in the graph.
- **Why it kills papers:** "we tried X and it worked" gives
  reviewers nothing to learn. They can believe every number and
  still reject: the paper transfers no understanding, so nothing
  generalizes beyond the specific X.
- **Repair:** articulate the observation that predicted X would work
  before it was tried — there usually is one, unstated. If genuinely
  none exists, the project needs an analysis phase, not a writing
  phase.

### 4. Diagnosis gap

- **Detect:** a `GAP` node with no `CAUSE` child.
- **Why it kills papers:** attacking a symptom means a competing
  paper that finds the cause will both explain your gains and
  supersede your fix. Reviewers who suspect the real cause will ask
  for the analysis you skipped.
- **Repair:** add the `CAUSE` node with an analysis experiment or a
  citation to prior diagnosis. If the cause is honestly unknown and
  the fix still works, say so explicitly in the paper — an admitted
  open diagnosis beats an implied false one.

## Secondary flags

### 5. Hanging insight

- **Detect:** an `INSIGHT` node with no `MECHANISM` descendant.
- **Meaning:** an observation the paper announces but never
  exploits. Reviewers ask why it is there; competitors thank you.
- **Repair:** exploit it, move it to future work, or cut it.

### 6. Result island

- **Detect:** a `RESULT` node with no `MECHANISM` parent.
- **Meaning:** a number in the experiments section that no part of
  the method claims credit for. Usually a leftover from an earlier
  project phase.
- **Repair:** connect it to the mechanism that produces it, or drop
  the experiment.

### 7. Unclosed loop

- **Detect:** a `GAP` node from which no directed path reaches any
  `RESULT`.
- **Meaning:** the introduction motivates a problem the experiments
  never revisit. The reader's opening question is never answered.
- **Repair:** add the closing experiment, or stop motivating with
  that gap.

### 8. Evidence laundering

- **Detect:** a node whose evidence artifact, even if it existed,
  could not settle the statement — a citation offered where only an
  experiment could decide, a proxy metric offered for an end-to-end
  claim, a qualitative example offered for a quantitative statement.
- **Meaning:** the status column looks green while the argument is
  hollow. This is the flag that keeps statuses honest.
- **Repair:** downgrade the status to `MISSING` and name an artifact
  of the right kind.

### 9. Load-bearing yellow

- **Detect:** every path from the positioning's center-of-mass
  burden to a `RESULT` passes exclusively through `PLANNED` nodes —
  the paper's hardest-to-prove claim rests on zero `VERIFIED`
  evidence.
- **Meaning:** the skeleton is fine but the project is all promise.
  Fine early; alarming near a deadline.
- **Repair:** prioritize executing the artifacts on that path before
  any drafting effort is spent elsewhere.

### 10. Fused granularity

- **Detect:** an alignment-matrix row where one module answers two
  challenges, or one challenge requires two modules — the 1:1:1:1
  discipline fails not by emptiness but by fan-out.
- **Meaning:** the method decomposition is at the wrong altitude;
  sections and ablations will fight the structure for the whole
  drafting process.
- **Repair:** split the module (or merge the challenges) until every
  row binds exactly one of each; re-run the scan.
