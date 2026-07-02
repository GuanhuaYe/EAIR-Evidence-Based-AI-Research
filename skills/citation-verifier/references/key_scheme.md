# Canonical bibtex key scheme

## Default scheme

`<lastname-of-first-author><year><firstword-of-title-lowercased>`

Examples:
- "Vaswani et al., Attention Is All You Need, NeurIPS 2017" →
  `vaswani2017attention`
- "Ho et al., Denoising Diffusion Probabilistic Models, NeurIPS 2020"
  → `ho2020denoising`
- "Beeri, Vardi, Formal Systems for Tuple and Key Dependencies,
  SIAM 1984" → `beeri1984formal`

## Rules

1. Lastname is the first author's surname, lowercased, no spaces.
   Hyphenated lastnames collapse: "Van der Berg" → `vanderberg`.
2. Year is 4 digits, the publication year (not arXiv year).
3. First word of title, lowercased, skipping articles ("A", "An",
   "The"). Stop at 12 chars.
4. If collision: append a single letter suffix (`vaswani2017attentiona`,
   `vaswani2017attentionb`).

## Project overrides

If a project's existing bibtex uses a different scheme (`@inproceedings`
labels like `attention-is-all-you-need-2017`), do NOT rename — the
scheme is project-local. Detect via majority pattern: if ≥80% of
existing keys match a single scheme, lock to that scheme and only
flag keys that violate IT.

Override registry per paper:
```
<paper>/latex/.bibkey_scheme.txt    # one line, scheme name
```

Supported scheme names: `lastname-year-firstword` (default),
`title-year`, `lastname-year-suffix`, `dblp-key`.
