# Contributing

PRs and issues welcome. Two house rules govern every contribution, because
they are the reason this repo exists:

1. **Verdicts must be computable.** If your skill emits a judgment
   (PASS/BLOCK, severity, verdict), the criteria must be stated explicitly
   enough that a second person — or a script — reaches the same judgment
   from the same inputs. "the LLM weighs the
   overall picture" counts as a design defect here.
2. **Rules must cite their failure.** Every hard rule, gate, or veto you add
   must name the concrete failure that motivated it (an incident, a
   measured collapse, a reproduced trap). A rule that can't point to a real
   failure will be rejected.

## Adding a skill

- One directory under `skills/<name>/` with a `SKILL.md` (frontmatter:
  `name`, `description`, `license: CC-BY-4.0`); optional `references/` and
  `scripts/`.
- State the pipeline position: what invokes it, what it consumes, what
  structured output it emits, and who consumes that output.
- Findings/outputs that assert something about a document must carry
  evidence (verbatim quote + location) or an explicit `NOT-IN-DOC`.
- Scripts: python3 stdlib preferred; declare extra dependencies at the top
  of the file; no hardcoded paths (use env vars with defaults); no secrets.
- Maturity label in the skill index (README): Draft / Beta / Stable.

## Reporting problems with a shipped rule

Open an issue with: the rule, the case where it misfired, and what evidence
would justify changing it. Gates may be tightened freely; loosening a gate
requires the receipt that motivated it to be re-examined first.

## Code style

Match what's around you. Scripts are small, deterministic where possible
(seeded randomness), and print what they decided and why.
