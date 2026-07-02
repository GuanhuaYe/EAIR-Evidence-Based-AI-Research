# Section heading register per venue family

## ml-formal (NeurIPS / ICML / ICLR)

- Title case: capitalize content words, lowercase articles /
  prepositions / conjunctions ≤4 chars.
- Form: noun phrase, max 6 words.
- Example: "1. Introduction", "3. Problem Formulation",
  "4. Method", "5. Experiments".
- Sub-headings: same rules.
- AVOID: question-form headings, sentence-form headings.

## nlp-narrative (ACL / EMNLP / NAACL)

- Title case or sentence case both seen; pick one and lock per paper.
- Form: noun phrase OR short sentence OR question.
- Examples: "What Do Probing Tasks Measure?", "Detecting
  Hallucinations in Long-Form Generation", "Method".
- Sub-headings: descriptive OK.

## db-engineering (SIGMOD / VLDB / ICDE)

- Title case.
- Form: noun phrase, often with concrete mechanism name.
- Examples: "4. The ABC Operator", "5. Index Maintenance",
  "6. Buffer Pool Management".
- AVOID: question form, sentence form. AVOID adjectives
  ("Efficient X", "Robust Y") in headings.

## cv-visual (CVPR / ICCV / ECCV / ACM MM)

- Title case.
- Form: noun phrase.
- Examples: "3. Network Architecture", "4. Training Procedure".
- Sub-headings often module names.

## mining-applied (KDD / SIGIR / WWW)

- Title case.
- Form: noun phrase; "Deployment", "Online Evaluation", "Online
  A/B Test" sections common.

## Normalization rule

If headings within one paper mix capitalization styles, normalize to
the majority style. If unclear majority, ask user.
