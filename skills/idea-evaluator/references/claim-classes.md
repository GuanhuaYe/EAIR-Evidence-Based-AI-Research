# Claim-Class Rubric

Axis C of Kill-Cheap Triage classifies the idea's *central* claim into
exactly one of four classes. Classification matters because the house
floor (default: `method | mechanism-with-fix` for top venues) is
enforced on the class, and because RESHAPE directives often work by
upgrading the class.

## The four classes

### method

"Doing X makes metric M better under matched conditions."

- The deliverable is a procedure someone else can run.
- The kill experiment is almost always an ablation or a matched
  baseline comparison.
- Litmus: if the paper's main table disappeared, would there be a
  paper left? For a method claim, no.

### mechanism

"Phenomenon P happens because of Z."

Two sub-forms with very different standing:

- **mechanism-with-fix** — the causal story yields an intervention
  ("because attention sinks absorb X, pruning them recovers Y").
  Clears the default house floor: the fix makes the mechanism
  falsifiable twice (once observationally, once interventionally).
- **bare mechanism** — the causal story with no derived intervention.
  Treated as *analysis* for floor purposes unless the causal evidence
  is interventional (controlled perturbation, not correlation across
  models).

Litmus: the claim contains "because", and removing the "because" clause
would gut the contribution.

### benchmark

"Here is a task/dataset/protocol that measures something existing
suites do not."

- The falsifiable core is the *discriminative validity* claim: the new
  benchmark must rank or separate systems differently from existing
  suites, or measure a capability they saturate on. A benchmark whose
  scores correlate ~1.0 with an existing suite has no delta.
- Kill experiment: score 3–5 existing systems on the new benchmark and
  on the nearest incumbent; kill_condition is rank correlation above a
  stated threshold.

### analysis

"Here is a characterization of existing systems."

- No new method, no fix, no new measurement instrument.
- Not worthless — but flag `CLAIM-BELOW-FLOOR` under the default house
  rule and force the caller to either accept the flag consciously
  (workshop, tech report, internal memo) or upgrade the class.

## Boundary cases

| Looks like | Actually is | Why |
|---|---|---|
| "We propose a taxonomy of failure modes" | analysis | A taxonomy is a characterization unless it drives a fix or a benchmark |
| "We show models fail at X and propose a dataset to measure it" | benchmark | The dataset is the deliverable; the failure observation is motivation |
| "We show models fail at X because of Z, and patching Z helps" | mechanism-with-fix | The fix is derived from the causal story, not bolted on |
| "We combine A and B and it wins" | method | Combination claims are method claims; novelty pressure lands on Axis D, not Axis C |
| "We prove bound B for algorithm A" | method (theoretical) | The deliverable is still a runnable/checkable artifact; the kill experiment is a counterexample search or a tightness check |
| "Survey of the area" | out of scope | Nothing to falsify; triage does not apply |

## Class-upgrade paths (for RESHAPE directives)

A RESHAPE that clears `CLAIM-BELOW-FLOOR` must name one concrete
upgrade:

- **analysis → mechanism-with-fix**: pick the strongest observed
  regularity, state a causal candidate, and design an intervention that
  the causal candidate predicts and rival explanations do not.
- **analysis → benchmark**: freeze the analysis's measurement procedure
  into a reusable protocol + dataset, and show discriminative validity
  against the nearest incumbent suite.
- **bare mechanism → mechanism-with-fix**: derive the intervention the
  causal story implies; if no intervention is derivable even in
  principle, the mechanism claim was likely unfalsifiable — send it
  back to Axis K.

An upgrade path is only a valid RESHAPE directive if its added cost
still fits the budget envelope from Axis E. Otherwise the honest
verdict is KILL.
