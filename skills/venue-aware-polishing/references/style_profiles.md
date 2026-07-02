# Venue-family style profiles

Five families, each with a parameterized profile. Stage 1 loads one.

## ml-formal (NeurIPS / ICML / ICLR)

```yaml
name: ml-formal
sentence_length:
  mean_target: 21
  std_target: 7
  hard_cap: 38
first_person:
  preferred: "we"
  acceptable: ["this paper", "passive"]
  forbidden: ["the authors"]
quantification_placement: "initial-preferred"
hedges:
  in_claims: "none"
  in_limitations: "mild"
  forbidden_in_claims:
    - "may", "might", "could", "possibly", "perhaps", "somewhat", "fairly"
heading_register: "noun-phrase, title-case, max 6 words"
figure_ref: "Fig. N" (or "Figure N" — be consistent)
table_ref: "Table N"
equation_density: "high — interleave with prose"
contraction: "forbidden"
oxford_comma: "preferred"
```

## nlp-narrative (ACL / EMNLP / NAACL / TACL)

```yaml
name: nlp-narrative
sentence_length:
  mean_target: 24
  std_target: 8
  hard_cap: 42
first_person:
  preferred: "we"
  acceptable: ["this paper", "passive"]
quantification_placement: "mid-with-context"
hedges:
  in_claims: "mild"  # "suggests", "indicates" OK
  in_limitations: "moderate"
heading_register: "noun-phrase or short sentence; question form acceptable"
figure_ref: "Figure N"
table_ref: "Table N"
linguistic_examples: "italic + gloss"
contraction: "forbidden"
oxford_comma: "preferred"
```

## db-engineering (SIGMOD / VLDB / ICDE)

```yaml
name: db-engineering
sentence_length:
  mean_target: 19
  std_target: 6
  hard_cap: 35
first_person:
  preferred: "we"
  acceptable: ["the system", "passive"]
quantification_placement: "mid-late"
hedges:
  in_claims: "none"
  in_limitations: "minimal"
heading_register: "noun-phrase, often with mechanism: 'The ABC Operator'"
figure_ref: "Figure N" (often "Fig. N" in tighter venues)
table_ref: "Table N"
emphasis_on: ["correctness", "performance numbers", "deployment"]
mechanism_first: true  # describe the mechanism before motivation in §4+
contraction: "forbidden"
oxford_comma: "preferred"
```

## cv-visual (CVPR / ICCV / ECCV / ACM MM)

```yaml
name: cv-visual
sentence_length:
  mean_target: 21
  std_target: 7
  hard_cap: 38
first_person:
  preferred: "we"
  acceptable: ["this paper"]
quantification_placement: "with-figure-anchor"
hedges:
  in_claims: "none"
  in_limitations: "mild"
heading_register: "noun-phrase"
figure_ref: "Fig. N"
table_ref: "Tab. N" (or "Table N")
visual_first_framing: true  # introduce figure before result number
contraction: "forbidden"
oxford_comma: "preferred"
```

## mining-applied (KDD / SIGIR / WWW / WSDM / ICDM / CIKM)

```yaml
name: mining-applied
sentence_length:
  mean_target: 22
  std_target: 8
  hard_cap: 40
first_person:
  preferred: "we"
  acceptable: ["the system", "this paper"]
quantification_placement: "mid"
hedges:
  in_claims: "minimal"
  in_deployment_discussion: "moderate"
heading_register: "noun-phrase; 'Deployment' section common"
figure_ref: "Figure N"
table_ref: "Table N"
application_framing: true
contraction: "forbidden"
oxford_comma: "preferred"
```

## Profile application order in Stage 3

1. Sentence-length check: split sentences over hard_cap; merge fragments
   below mean - std.
2. First-person: enforce preferred register; rewrite forbidden.
3. Quantification placement: reorder claim sentences to match.
4. Hedges: strip forbidden_in_claims; preserve allowed in
   limitations/discussion.
5. Heading register: enforce capitalization and form.
6. Figure / table refs: normalize per profile.
7. Contractions: expand all ("don't" → "do not", "it's" → "it is").

## When AAAI / IJCAI

Route by paper topic:
- Theory / methods paper → `ml-formal`
- Applied / deployment paper → `mining-applied`
- DB-flavored → `db-engineering`
- Vision-flavored → `cv-visual`

If ambiguous, ask the user.
