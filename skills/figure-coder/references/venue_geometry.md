# Venue figure geometry

Confirm against current style files. The column-width values below are
standard but may shift by ±0.1in per cycle.

## NeurIPS (acmart-like LaTeX class)
- Single column: 3.25 in (~83 mm)
- Double column (full page width): 6.75 in (~171 mm)
- Body font: Times, 10pt
- Caption font: 9pt
- Min in-figure font: 7pt
- Aspect ratio: prefer 1.5:1 to 2:1
- Output: PDF (vector)

## ICML (similar to NeurIPS)
- Single column: 3.25 in
- Double column: 6.75 in
- Body font: Times, 10pt
- Output: PDF

## ICLR (OpenReview, NeurIPS-like)
- Single column: 3.25 in
- Double column: 6.75 in
- Body font: Times, 10pt
- Output: PDF

## ACL ARR / EMNLP / NAACL
- Single column: 3.1 in (~78 mm)
- Double column: 6.3 in (~160 mm)
- Body font: Times, 11pt
- Output: PDF

## AAAI
- Single column: 3.42 in
- Double column: 7.0 in
- Body font: Times, 10pt
- Output: PDF

## IJCAI
- Single column: 3.33 in
- Double column: 6.85 in
- Body font: Times, 9pt
- Output: PDF

## CVPR / ICCV / ECCV
- Single column: 3.25 in
- Double column: 6.875 in
- Body font: Times, 10pt
- Output: PDF

## ACM MM (acmart)
- Single column: 3.33 in
- Double column: 7.0 in
- Body font: Linux Libertine in acmart, 9pt body
- Output: PDF

## SIGMOD (acmart)
- Single column: 3.33 in
- Double column: 7.0 in
- Body font: Linux Libertine in acmart, 9pt body
- Output: PDF

## VLDB (PVLDB style)
- Single column: 3.33 in
- Double column: 7.0 in
- Body font: Times, 9pt
- Output: PDF

## ICDE (IEEE conference)
- Single column: 3.4 in
- Double column: 7.0 in
- Body font: Times, 10pt
- Output: PDF

## KDD (acmart)
- Single column: 3.33 in
- Double column: 7.0 in
- Body font: Linux Libertine in acmart, 9pt body
- Output: PDF

## SIGIR (acmart)
- Single column: 3.33 in
- Double column: 7.0 in
- Body font: 9pt
- Output: PDF

## WWW (acmart)
- Single column: 3.33 in
- Double column: 7.0 in
- Body font: 9pt
- Output: PDF

## Universal minimums

- In-figure text minimum: 7pt (smaller is unreadable in print)
- Line width minimum: 0.5pt
- Marker size minimum: 3pt at 100% scale

## Column-width helper

Helper function to use in templates:

```python
def venue_width(venue: str, span: str) -> float:
    spec = {
        "neurips": (3.25, 6.75), "icml": (3.25, 6.75), "iclr": (3.25, 6.75),
        "acl": (3.1, 6.3), "emnlp": (3.1, 6.3), "naacl": (3.1, 6.3),
        "aaai": (3.42, 7.0), "ijcai": (3.33, 6.85),
        "cvpr": (3.25, 6.875), "iccv": (3.25, 6.875), "eccv": (3.25, 6.875),
        "mm": (3.33, 7.0), "sigmod": (3.33, 7.0), "vldb": (3.33, 7.0),
        "icde": (3.4, 7.0), "kdd": (3.33, 7.0), "sigir": (3.33, 7.0),
        "www": (3.33, 7.0),
    }
    single, double = spec[venue.lower()]
    return single if span == "single" else double
```
