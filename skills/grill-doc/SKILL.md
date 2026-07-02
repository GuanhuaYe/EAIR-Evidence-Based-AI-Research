---
name: grill-doc
description: >-
  Evidence-gated interrogation of a research document (idea doc, experiment
  design, SUPERVISOR_BRIEF) BEFORE expensive execution. A griller asks
  fixed-manual methodology questions; a defender agent answers ONLY by
  quoting the document (verbatim quote + file), with forced NOT-IN-DOC
  admissions; a code gate (scripts/gate.py) validates every quote against
  the source files and computes the verdict — no LLM holistic judgment.
  Use before dispatching Runner (GPU ignition), before Stage 1 Gate1, or
  whenever the user asks to 'grill this design', 'stress-test this doc',
  'find gaps before we run'.
license: CC-BY-4.0
---

# Grill-Doc — Evidence-Gated Design Interrogation

## Why this shape (do not regress)

This skill deliberately does NOT use free-form adversarial debate
(griller vs defender arguing). That paradigm fails structurally: a
defense role always finds "we'll refine it / it's delegated / it runs
in parallel" excuses, judges get swayed by rhetoric, and prompt-tuning
the judge does not converge. What does converge is **triage + fixed
interrogation manual**: triage → per-category deep interrogation via a
fixed decision-tree manual → evidence gate → verdict computed by code.
This skill is that paradigm applied to research documents.

Iron rules (structural, not prompt-level):

1. **Defender never defends.** Its ONLY job: answer each question by
   quoting the doc verbatim, or declare `NOT-IN-DOC`. Rationalization,
   "future work", "will do later", "to be decided", "should be fine"
   → auto-GAP.
2. **Evidence gate is programmatic.** Every quote is substring-checked
   against the actual file by `scripts/gate.py`. Fabricated or
   non-resolving quotes invalidate the answer (→ HAND-WAVED), no appeal.
3. **Verdict by code.** PASS/BLOCK is computed from the tag table by
   gate.py rules. No LLM ever "weighs the overall picture".
4. **No new exception routes.** The gate's acceptance criteria may be
   tightened, never loosened (lesson: reconciliation routes may only be
   removed, never added; adding one escape route collapsed a score of 81
   to 0).
5. **Cross-model.** When dispatched as agents, defender model ≠ griller
   model (the conductor cross-model rule).
6. **Watch traces on small batches.** First runs on a new project: read
   the full Q&A transcript, don't trust the summary. Never blind-tune
   on the full set.

## Protocol

### Step 0 — Inputs

- `doc_files`: the document(s) under interrogation. Typically
  `SUPERVISOR_BRIEF.md`, an experiment design doc, or an idea JSON/md.
  The doc must be self-contained: the defender sees ONLY these files.
- `mode`: `idea` (Stage 1, lighter — categories C1 C4 C5 C6) or
  `design` (Stage 2, full — all six categories). Default `design`.

### Step 1 — Triage (griller, inline)

Read the doc. For each manual category (see `manual.md`), decide
applicable / not-applicable with one line of justification. A category
may only be skipped if structurally impossible (e.g. C1 pooling when
there is provably a single population). When in doubt → applicable.

### Step 2 — Interrogation (defender = separate agent)

Dispatch ONE defender agent with:
- the doc files (contents inlined or paths),
- the applicable questions from `manual.md` (include each question's
  qid, text, and follow-up rules),
- the defender contract below, verbatim.

**Defender contract (paste into the agent prompt):**

```
You are the Defender. You answer interrogation questions about the
attached document. HARD RULES:
- You may use ONLY the attached document as your source. No outside
  knowledge, no inference beyond what is written, no charitable
  completion of what the authors "probably meant".
- For each question, either:
  (a) answer with status "ANSWERED", giving 1-3 verbatim quotes
      (each >= 8 characters, copied EXACTLY from the doc, no
      paraphrase, no ellipsis inside a quote) plus the file each
      quote comes from; or
  (b) answer with status "NOT-IN-DOC" if the document does not
      contain the information. This is the REQUIRED answer whenever
      evidence is absent. Declaring NOT-IN-DOC is correct behavior,
      not failure.
- FORBIDDEN: defending the design, arguing a gap doesn't matter,
  promising future work, answering from your own expertise. Any such
  content in an answer voids it.
- Output: JSON only, schema:
  {"qa":[{"qid":"...","status":"ANSWERED"|"NOT-IN-DOC",
          "answer":"<=60 words, factual restatement of what the doc says",
          "evidence":[{"file":"...","quote":"verbatim"}]}]}
```

The griller applies the manual's follow-up rules (decision tree): a
follow-up fires only when its parent condition is met by the doc's
answer. One extra defender round max for follow-ups.

### Step 3 — Gate (code)

```
python3 scripts/gate.py --qa qa.json --docs <doc_files...> --manual manual.md \
    --out grill_report.md --json grill_result.json
```

gate.py assigns per-question tags:
- `ANSWERED-WITH-EVIDENCE`: status ANSWERED, all quotes resolve
  (whitespace-normalized substring of the named file, length >= 8).
- `HAND-WAVED`: status ANSWERED but zero quotes, any quote fails to
  resolve, or answer contains a forbidden escape phrase
  (future work / TBD / will be addressed / to be decided ...; the
  detection list in gate.py also includes Chinese equivalents such as
  后续 / 待定 / 应该 for bilingual docs).
- `GAP`: status NOT-IN-DOC.

Verdict rules (computed, fixed):
- any `critical` question tagged GAP or HAND-WAVED → **BLOCK**
- else any question tagged GAP or HAND-WAVED → **PASS-WITH-NOTES**
- else → **PASS**

### Step 4 — Routing (griller, inline)

For each non-ANSWERED item, route (this is triage of consequences, not
re-judging the tag):
- `DOC-GAP` — the team likely knows the answer but the doc doesn't say
  it → Supervisor updates SUPERVISOR_BRIEF / design doc.
- `DESIGN-FLAW` — the doc reveals the design genuinely lacks this
  control → Coder/Engineer revise the design.
- `USER-ESCALATION` — genuinely open question no agent can settle →
  surface to the user. Keep this list SHORT (the point of agent-answering
  is compressing 20 questions to the 2-3 that need a human).

### Step 5 — Re-grill (max 1 repeat)

After fixes, re-run Steps 2-3 on the previously non-ANSWERED qids only.
Two rounds total, then whatever is still open goes to USER-ESCALATION.
A BLOCK verdict at round 2 stops the pipeline (Stage 2: Runner is NOT
dispatched; Stage 1: idea does not pass Gate1).

## Quality metric for the grill itself

Evidence alignment > verdict: a verdict is a yes/no that can be
guessed; the real signal is whether the interrogation forced out the
SPECIFIC evidence an expert would rely on. Score the grill by
evidence-ID alignment, not verdict precision/recall. Maintain a
regression gold set in `regression/`: a design doc with known,
pre-registered gaps; a good manual must surface most of those gaps
from the pre-run doc. When editing manual.md, re-run the regression
before committing. (The original internal regression fixture is not
shipped; add your own from your first grilled project.)

## Outputs

- `grill_report.md` — tag table + verdict + routing, written to
  `{exp_dir}/methodology/grill-doc_v{N}.md` when invoked by the conductor.
- `grill_result.json` — machine-readable, consumed as `methodology_input`
  by the next agent's task.json.
