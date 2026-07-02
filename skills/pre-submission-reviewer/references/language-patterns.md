# Language Pattern Catalogue

Detection cues and rewrite templates for the language sweep
(Sweep 4). Every finding must quote the offending sentence verbatim
and name the pattern ID below. If a genuinely new pattern recurs
three or more times in one draft, add it here rather than reporting
uncatalogued style opinions.

The catalogue has two parts: **machine-flavor patterns** (prose
that reads as generated or template-filled) and **grammar
patterns** (recurrent faults, especially from non-native writers).
Severity is computed by rules L1–L6 in the severity rulebook, keyed
on occurrence counts — so count every instance; do not sample.

## Part 1: Machine-flavor patterns

### M1 — Uniform sentence openings

**Cue:** three or more consecutive sentences opening with the same
scaffold word or construction. Common scaffolds: connective adverbs
("Moreover", "Furthermore", "Additionally", "Notably"), the bare
demonstrative "This ...", and "It is worth noting that".

**Why it reads generated:** human authors vary rhythm; templated
generation defaults to one connective per sentence, round-robin.

**Rewrite template:** delete the connective outright in at least
two of the three sentences — most survive unharmed — and merge or
subordinate one pair ("X. Moreover, Y." → "X, and consequently Y.")
so the paragraph regains varied sentence length.

### M2 — Hedging stacks

**Cue:** two or more hedges guarding a single clause. Hedge
inventory: "could", "may", "might", "potentially", "possibly",
"perhaps", "seems to", "tends to", "to some extent", "arguably".
"could potentially" and "may possibly" are the canonical stacks.

**Why it reads generated:** a writer who has looked at the evidence
picks one epistemic level; stacked hedges signal that no one
decided.

**Rewrite template:** keep exactly one hedge, chosen by the
overclaiming ladder from Sweep 1. "This could potentially suggest
that X may improve Y" → "This suggests that X improves Y" (if the
evidence supports "suggest") or "X might improve Y" (if it does
not).

### M3 — Empty intensifiers

**Cue:** an adjective or adverb whose deletion changes nothing a
reader could act on. Inventory: "very", "extremely", "highly",
"truly", "significantly" (when no statistical test is cited),
"comprehensive(ly)", "seamless(ly)", "robustly" (without a
robustness experiment), "crucial", "vital".

**Test:** delete the word and reread. If the sentence's information
content is identical, the word was empty.

**Rewrite template:** delete, or replace with the measurement that
earned the adjective: "significantly faster" → "2.1× faster
(Table 4)". An intensifier is only legitimate when the paper
contains the number that backs it.

### M4 — List-itis

**Cue:** either (a) three or more consecutive paragraphs that each
consist of a bullet/numbered list, or (b) a "First, ... Second, ...
Third, ..." run whose final sentence never states what the
enumeration adds up to.

**Why it reads generated:** enumeration is cheap structure. Papers
owe arguments — enumerations that never converge on a conclusion
show structure without reasoning.

**Rewrite template:** keep at most one list per page of prose;
convert the rest to paragraphs whose final sentence states the
consequence ("Together, these three failures indicate that the
bottleneck is X, which motivates the design in Section 4.").

## Part 2: Grammar patterns

### G1 — Dangling or misattached modifier

**Cue:** a participial opener whose implied subject is not the
sentence's grammatical subject. "Using a larger batch size, the
loss diverges" (the loss is not using anything).

**Rewrite:** name the true agent, or convert to a "when/with"
clause: "With a larger batch size, the loss diverges."

**Note:** when the misattachment changes the technical meaning,
rule L3 applies (MAJOR), not L4.

### G2 — Ambiguous pronoun in a claim sentence

**Cue:** "it", "this", "they", or "which" with two or more
plausible antecedents, occurring in a sentence that states a result
or a design decision. "We compare A with B and find that it is
faster."

**Rewrite:** repeat the noun. Repetition of a technical noun is
never a fault in a paper; ambiguity always is.

### G3 — Article omission or misuse on countable technical nouns

**Cue:** bare singular countable nouns ("we train model on
dataset"), or "the" on a first mention of a non-unique object.

**Rewrite:** singular countable nouns take an article or become
plural: "we train the model on dataset D" / "we train models on
three datasets".

### G4 — Tense drift within one narrative frame

**Cue:** a single paragraph that switches between past and present
when describing one experiment or one method. Convention: the
paper's own method and findings in present tense ("the encoder
maps", "Table 2 shows"); the concrete acts of experimentation in
past tense ("we trained for 100 epochs"); pick one frame per
paragraph and hold it.

**Rewrite:** normalize the paragraph to the frame of its topic
sentence.

### G5 — Comma splice around a contrast

**Cue:** two independent clauses joined by a bare comma, usually
with "however" or "instead" floating mid-sentence: "Prior methods
use X, however this fails at scale."

**Rewrite:** semicolon plus connective, or two sentences: "Prior
methods use X; however, this fails at scale."

### G6 — Noun-pileup (stacked attributive nouns)

**Cue:** four or more nouns in a row acting as one noun phrase:
"training data distribution shift detection module".

**Rewrite:** unstack with prepositions, keeping at most two
attributive nouns: "a module that detects shift in the training
data distribution".

### G7 — Singular/plural agreement across an intervening phrase

**Cue:** subject and verb separated by a prepositional phrase whose
object has different number: "the set of experiments confirm".

**Rewrite:** agree with the head noun: "the set of experiments
confirms" — or drop the wrapper: "the experiments confirm".

## Counting and reporting

- Count occurrences per pattern ID over the sweep's scope; report
  the count in the finding's `fix` field context if it drove the
  severity (rules L1/L2).
- One sentence can trigger multiple pattern IDs; report each as a
  separate finding sharing the same `verbatim_quote` (rule L5 then
  applies at ≥ 3 patterns on one sentence).
- Abstract occurrences are escalated by rule L6.
