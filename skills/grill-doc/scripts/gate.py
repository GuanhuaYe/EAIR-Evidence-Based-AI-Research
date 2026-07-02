#!/usr/bin/env python3
"""grill-doc evidence gate.

Programmatic validation of defender answers (iron rule from an earlier
internal project: verdict by code, LLM only reports facts). Tags each
Q&A item, computes verdict. Stdlib only (argparse/json/os/re/sys).

Usage:
  python3 gate.py --qa qa.json --docs doc1.md [doc2.md ...] \
      --manual manual.md [--out grill_report.md] [--json grill_result.json]

qa.json schema (defender output, plus griller-added criticality):
  {"qa": [{"qid": "CONF-1", "critical": true,
           "question": "...",
           "status": "ANSWERED" | "NOT-IN-DOC",
           "answer": "...",
           "evidence": [{"file": "design_doc.md", "quote": "..."}]}]}

Tags:
  ANSWERED-WITH-EVIDENCE  status ANSWERED, >=1 quote, all quotes resolve
  HAND-WAVED              status ANSWERED but no quotes / any quote fails
                          to resolve / answer uses an escape phrase
  GAP                     status NOT-IN-DOC

Verdict (fixed, do not add exception routes):
  BLOCK            any critical question tagged GAP or HAND-WAVED
  PASS-WITH-NOTES  any non-critical GAP or HAND-WAVED
  PASS             everything ANSWERED-WITH-EVIDENCE
"""
import argparse
import json
import os
import re
import sys

MIN_QUOTE_LEN = 8

# Escape phrases: promising instead of evidencing. Tightening allowed,
# loosening forbidden (lesson: escape routes may only be removed, never
# added). Chinese entries kept intentionally so bilingual docs cannot
# hand-wave in either language.
ESCAPE_PHRASES = [
    "future work", "will be addressed", "to be determined", "tbd",
    "we plan to", "should be fine", "presumably", "probably",
    "后续", "待定", "以后再", "应该没问题", "应该会", "大概率会", "未来工作",
]


def norm(s: str) -> str:
    """Collapse whitespace and markdown emphasis markers (** * ` __) so
    line-wrapping and bold/italic/code formatting differences don't matter.
    Applied symmetrically to quote and doc, so it cannot admit fabricated
    text — only formatting-invariant verbatim matches."""
    s = re.sub(r"[*`_]", "", s)
    s = s.translate(str.maketrans({"“": '"', "”": '"',
                                   "‘": "'", "’": "'"}))
    return re.sub(r"\s+", "", s)


def load_docs(paths):
    docs = {}
    for p in paths:
        with open(p, encoding="utf-8") as f:
            docs[os.path.basename(p)] = norm(f.read())
    return docs


def resolve_quote(ev, docs):
    """A quote resolves iff it is a verbatim (whitespace-normalized)
    substring of the named doc file and long enough to be meaningful."""
    fname = os.path.basename(ev.get("file", ""))
    quote = ev.get("quote", "")
    if fname not in docs:
        return False, f"file '{fname}' not among interrogated docs"
    q = norm(quote)
    if len(q) < MIN_QUOTE_LEN:
        return False, f"quote too short (<{MIN_QUOTE_LEN} chars normalized)"
    if q not in docs[fname]:
        return False, "quote does not resolve (not a verbatim substring)"
    return True, "ok"


def tag_item(item, docs):
    status = item.get("status", "").upper()
    answer = item.get("answer", "") or ""
    evidence = item.get("evidence", []) or []

    if status == "NOT-IN-DOC":
        return "GAP", "defender declared NOT-IN-DOC"
    if status != "ANSWERED":
        return "HAND-WAVED", f"invalid status '{status}'"

    low = answer.lower()
    for phrase in ESCAPE_PHRASES:
        if phrase in low:
            return "HAND-WAVED", f"escape phrase in answer: '{phrase}'"

    if not evidence:
        return "HAND-WAVED", "ANSWERED with zero quotes"

    for ev in evidence:
        ok, why = resolve_quote(ev, docs)
        if not ok:
            return "HAND-WAVED", f"quote invalid ({why}): {ev.get('quote','')[:60]!r}"
    return "ANSWERED-WITH-EVIDENCE", f"{len(evidence)} quote(s) resolved"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa", required=True)
    ap.add_argument("--docs", nargs="+", required=True)
    ap.add_argument("--manual", default=None, help="unused placeholder for provenance")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", dest="json_out", default=None)
    args = ap.parse_args()

    with open(args.qa, encoding="utf-8") as f:
        qa = json.load(f)["qa"]
    docs = load_docs(args.docs)

    results = []
    for item in qa:
        tag, reason = tag_item(item, docs)
        results.append({
            "qid": item.get("qid", "?"),
            "critical": bool(item.get("critical", False)),
            "question": item.get("question", ""),
            "status": item.get("status", ""),
            "answer": item.get("answer", ""),
            "evidence": item.get("evidence", []),
            "tag": tag,
            "gate_reason": reason,
        })

    bad = [r for r in results if r["tag"] != "ANSWERED-WITH-EVIDENCE"]
    if any(r["critical"] for r in bad):
        verdict = "BLOCK"
    elif bad:
        verdict = "PASS-WITH-NOTES"
    else:
        verdict = "PASS"

    lines = ["# grill-doc gate report", "",
             f"**Verdict: {verdict}**  (computed by gate.py — not overridable by any agent)", "",
             "| qid | crit | tag | gate reason |",
             "|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['qid']} | {'●' if r['critical'] else ''} | {r['tag']} | {r['gate_reason']} |")
    lines += ["", "## Items needing routing (GAP / HAND-WAVED)", ""]
    for r in bad:
        lines.append(f"- **{r['qid']}** [{r['tag']}] {r['question']}")
        if r["answer"]:
            lines.append(f"  - defender: {r['answer']}")
    report = "\n".join(lines) + "\n"

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump({"verdict": verdict, "results": results}, f,
                      ensure_ascii=False, indent=2)
    print(report)
    return 0 if verdict != "BLOCK" else 2


if __name__ == "__main__":
    sys.exit(main())
