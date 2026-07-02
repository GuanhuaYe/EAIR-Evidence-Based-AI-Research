# L1-interference patterns (Chinese→English) — L2-English failure modes

These patterns appear in papers by Chinese-L1 authors. Stage 4
detects and rewrites.

## Article errors

| Pattern | Fix |
|---|---|
| "We propose method that ..." | "We propose a method that ..." |
| "The Figure 3 shows ..." | "Figure 3 shows ..." |
| "The Table 2 reports ..." | "Table 2 reports ..." |
| "In above equation ..." | "In the equation above ..." |
| "First, we present method." | "First, we present the method." |
| "From perspective of ..." | "From the perspective of ..." |
| "Recently, transformer-based methods ..." | "Recently, transformer-based methods ..." (preserve unless "the" needed) |

Rule: bare uncountable mass-nouns are fine; bare named entities
("Figure 3", "Table 2") never take an article; bare singular
countables ("method", "model") need an article unless generic plural.

## Tense drift

A discussion paragraph must keep one primary tense:
- Past simple: describing what was done in this work
- Present simple: stating what holds in general / what tables show
- Present perfect: rare, only for ongoing relevance

Detect mixed tense in adjacent sentences and rewrite to match the
paragraph's primary tense.

## Subject-verb agreement on collective nouns

| Pattern | Fix |
|---|---|
| "The data shows that ..." (sometimes preferred plural in formal) | leave singular; venues vary, prefer paper-internal consistency |
| "A group of methods are ..." | "A group of methods is ..." (collective sg) |
| "Each of the models have ..." | "Each of the models has ..." (each = sg) |
| "Both X and Y is ..." | "Both X and Y are ..." |

## Which vs that

- Restrictive (no comma): use "that"
- Non-restrictive (with comma): use "which"

Common error: "The model which we train on dataset X" (no comma) →
"The model that we train on dataset X"

## Comma splices

| Pattern | Fix |
|---|---|
| "X is fast, it has high throughput." | "X is fast; it has high throughput." or split into two sentences |
| "We trained on dataset A, the results show ..." | "We trained on dataset A. The results show ..." or insert "and" / ", so" |

## Topic-comment to subject-predicate

Chinese is topic-comment; English is subject-predicate.

| Topic-comment (L1 interference) | Subject-predicate (English) |
|---|---|
| "As for the model, it ..." | "The model ..." |
| "Regarding the dataset, we ..." | "We use the dataset ..." |
| "About the experiments, we ..." | "Our experiments ..." |
| "When it comes to scalability, ..." | "For scalability, ..." or restructure |

## "However" overuse

"However, " at the start of every other sentence is a common
L1-interference marker. Detect frequency: if ≥3 in 8 consecutive sentences,
rewrite ≥1 with a different connector ("In contrast", "By contrast",
"Yet", or restructure as one sentence with "while").

## "On the one hand / on the other hand"

Acceptable but overused. Limit to once per paper. Replace with "First
... Second" or sentence-internal contrast.

## "And so on" / "etc."

In technical writing, list specifically or drop. Reviewers read these
as imprecision.

## "Make" overuse

Chinese 让 / 使 maps to "make" too often:
| L1 interference | English |
|---|---|
| "X makes Y improve by Z%" | "X improves Y by Z%" |
| "This makes the model more robust" | "This improves model robustness" or restructure with concrete metric |

## "More than" comparative confusion

| L1 interference | English |
|---|---|
| "X is more better than Y" | "X is better than Y" |
| "Y is much more faster" | "Y is much faster" |

## Number-noun agreement

| L1 interference | English |
|---|---|
| "3 dataset" | "3 datasets" |
| "10 model" | "10 models" |

## Capitalization in titles

Section headings should follow venue's title-case rules. Detect
inconsistent capitalization across headings and normalize.
