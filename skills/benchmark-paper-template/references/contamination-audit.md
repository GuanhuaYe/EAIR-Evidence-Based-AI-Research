# Contamination Audit Playbook (P4)

Goal: bound how much of the benchmark score could come from training-data
leakage rather than the measured capability, and commit to a policy that keeps
the bound from decaying. Every probe below ends in a number the paper reports.

## 1. n-gram overlap probe

- Tokenize every item (question text, gold answer, and distractors separately)
  and search for 13-gram (fallback: 8-gram for short items) exact matches
  against open pretraining corpora you can index: Dolma, RedPajama, The Pile,
  C4, plus any corpus the evaluated model families disclose.
- Report per split: `hit rate = items with ≥1 matched n-gram / total items`,
  broken out by whether the match covers the *answer span* (worst case) or
  only the question stem.
- Decision rule to print in the paper: items whose answer span matches are
  removed or moved to a "contaminated" reporting bucket; never silently kept.

## 2. Provenance / URL probe

- For every item derived from a source document, record the source URL or
  document ID at construction time (retrofit via search if not recorded).
- Check whether the source is (a) publicly indexed, (b) present in Common
  Crawl snapshots predating the evaluated models' cutoffs, (c) behind access
  controls.
- Report the fraction of items in each bucket. Items in bucket (b) are
  presumed reachable by pretraining regardless of n-gram misses (paraphrased
  or reformatted copies evade exact match).

## 3. Paraphrase / completion probes (behavioral)

n-gram and URL checks miss items that entered training data reworded. Probe
the models directly:

- **Partial-item completion.** Prompt the model with the first half of the
  item text and measure verbatim (or near-verbatim, edit distance < 0.1)
  continuation of the second half. Report the completion rate against a
  matched control set of items published after the model's cutoff.
- **Choice-order sensitivity.** For multiple-choice items, shuffle option
  order and letters. A memorized item shows accuracy tied to the original
  ordering; report the accuracy delta.
- **Distractor recall.** Ask the model to list the answer options for a named
  item without providing them. Any success is direct evidence of leakage.
- **Paraphrase gap.** Rewrite items with meaning preserved (human-checked
  sample), and report `score(original) − score(paraphrased)` per model. Gaps
  well above the P2 confidence interval indicate memorized surface forms.
  (This probe doubles as a P2 rewording stability check — run once, report
  under both properties.)

## 4. Interpreting probe results

- No single probe is conclusive; report all that apply and the union of
  flagged items.
- A clean n-gram result with a large paraphrase gap means the leakage is
  reworded — trust the behavioral probe.
- Contamination is model-relative: report per model family where behavior
  probes are used, since cutoffs differ.

## 5. Refresh policy patterns (pick one, state it)

- **Held-back private split.** Keep x% of items unreleased; scores on it are
  obtained via an eval service or maintainer-run harness. State who runs it
  and how discrepancies with the public split are reported.
- **Scheduled rotation.** Regenerate or re-source a fixed fraction of items on
  a stated cadence, with an anchoring subset kept fixed (or equated via
  overlapping administration) so scores stay comparable across versions.
- **Post-cutoff sourcing.** Items are drawn only from material dated after a
  rolling cutoff (news, new repositories, newly published problems); state the
  lag between sourcing and release, which bounds the exposure window.
- **Generative templates with held-out seeds.** Release the generator, hold
  back the seed pool; state the seed-pool size and collision probability.

A refresh policy must name: trigger (time or observed saturation/leakage),
what changes, what stays comparable, and where version scores are archived.

## Minimal reporting block for the paper

> Contamination audit: 13-gram overlap vs {corpora} = a% of items (answer-span
> hits: b%, removed); source provenance: c% of items publicly indexed
> pre-cutoff; partial-item completion rate = d% vs e% on post-cutoff controls;
> paraphrase gap = f points (CI ±g). Refresh policy: {pattern, cadence,
> anchoring method}.
