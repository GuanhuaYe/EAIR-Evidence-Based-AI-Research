#!/usr/bin/env python3
"""Generate a self-contained HTML ops dashboard from a project's clock/ledger files.

Reads (all optional, degrades gracefully):
  PULSE.jsonl, ALARMS.jsonl, alarms/{pending,met,fired}/, CONDUCTOR_LOG.json,
  tree.json, experiments/*/decision.md

Usage: gen_dashboard.py --project-dir <p> --out <file.html> [--ticks 240]
"""
import argparse, glob, html, json, os, re


def jload(p, default):
    try:
        return json.load(open(p))
    except Exception:
        return default


def jsonl(p, limit=None):
    out = []
    try:
        for line in open(p):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return out[-limit:] if limit else out


def esc(s):
    return html.escape(str(s), quote=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ticks", type=int, default=240)
    a = ap.parse_args()
    P = os.path.expanduser(a.project_dir)

    ticks = jsonl(os.path.join(P, "PULSE.jsonl"), a.ticks)
    last = ticks[-1] if ticks else {}
    log = jload(os.path.join(P, "CONDUCTOR_LOG.json"), {})
    entries = log if isinstance(log, list) else (log.get("entries") or log.get("log") or [])
    treedoc = jload(os.path.join(P, "tree.json"), {})
    tree = treedoc.get("nodes", {})
    expreg = treedoc.get("experiments", {})

    # experiment ledger: verdict line from each decision.md
    exps = []
    for d in sorted(glob.glob(os.path.join(P, "experiments", "*"))):
        name = os.path.basename(d)
        verdict = "in progress"
        dm = os.path.join(d, "decision.md")
        if os.path.exists(dm):
            head = open(dm).read(600)
            m = re.search(r"\*\*Verdict:\s*([A-Z_]+)\*\*", head)
            verdict = m.group(1) if m else "decided"
        exps.append((name, verdict))

    # alarms
    def alarm_files(sub):
        out = []
        for f in sorted(glob.glob(os.path.join(P, "alarms", sub, "*.json"))):
            j = jload(f, None)
            if j:
                out.append(j)
        return out
    pend, met, fired = alarm_files("pending"), alarm_files("met"), alarm_files("fired")

    # gpu series for canvas: [[u0,u1], ...] + ts labels
    series = []
    for t in ticks:
        g = t.get("gpus") or []
        series.append({"ts": t.get("ts", "")[11:16],
                       "u": [x.get("util_pct", 0) for x in g[:2]]})

    verdict_cls = {"REPLICATED": "good", "PROVEN": "good", "CONFIRMED": "good",
                   "INSUFFICIENT": "warn", "CONFOUNDED": "warn", "OPEN": "warn",
                   "FAIL": "crit", "REFUTED": "crit"}

    def chip(txt, cls):
        return f'<span class="chip {cls}">{esc(txt)}</span>'

    # interactive tree: node data inlined as JSON; click opens detail panel
    node_data = {}
    for k, v in tree.items():
        node_data[k] = {
            "status": v.get("status", "?"), "short": v.get("short", ""),
            "falsifiable_form": v.get("falsifiable_form", ""),
            "mechanism_claim": v.get("mechanism_claim", ""),
            "generalization_scope": v.get("generalization_scope", ""),
            "kill_criteria": v.get("kill_criteria", ""),
            "notes": (v.get("notes") or "")[:600] if isinstance(v.get("notes"), str) else "",
            "experiments": [
                {"id": e, "hyp": expreg.get(e, {}).get("hypothesis", ""),
                 "verdict": next((verd for nm, verd in exps if nm.startswith(e)), "")}
                for e in (v.get("experiments") or [])
            ],
        }

    def tree_nodes_html(parent):
        kids = [k for k, v in tree.items() if v.get("parent") == parent]
        if parent is None:
            kids = [k for k, v in tree.items()
                    if not v.get("parent") or v.get("parent") not in tree]
        if not kids:
            return ""
        items = ""
        for k in sorted(kids):
            st = tree[k].get("status", "?")
            items += (f'<li><button class="node" data-id="{esc(k)}">'
                      f'<span class="hyp-id">{esc(k)}</span>'
                      f'{chip(st, verdict_cls.get(st, "warn"))}'
                      f'<span class="node-short">{esc((tree[k].get("short") or "")[:80])}</span>'
                      f'</button>{tree_nodes_html(k)}</li>')
        return f"<ul>{items}</ul>"

    hyp_html = (f'<div class="treewrap"><div class="tree">{tree_nodes_html(None)}</div>'
                f'<div class="detail" id="detail"><span class="dim">click a node</span></div></div>')

    exp_rows = "".join(
        f'<tr><td class="mono">{esc(n)}</td>'
        f'<td>{chip(v, verdict_cls.get(v, "warn") if v != "in progress" else "warn")}</td></tr>'
        for n, v in exps)

    def alarm_rows(items, state, cls):
        r = ""
        for al in items[-6:]:
            when = al.get("fired_at") or al.get("met_at") or al.get("registered_at", "")
            r += (f'<tr><td class="mono">{esc(al.get("id","?"))}</td>'
                  f'<td>{chip(state, cls)}</td>'
                  f'<td class="mono dim">{esc(when[11:19])}</td>'
                  f'<td class="dim note">{esc((al.get("note") or "")[:130])}</td></tr>')
        return r
    alarms_html = (alarm_rows(pend, "armed", "acc") + alarm_rows(fired, "fired", "crit")
                   + alarm_rows(met, "met", "good"))

    log_html = "".join(
        f'<tr><td class="mono dim">{esc((e.get("timestamp") or "")[5:16])}</td>'
        f'<td class="mono">{esc(e.get("action","?"))}</td>'
        f'<td class="dim note">{esc((e.get("detail") or e.get("id") or "")[:150])}</td></tr>'
        for e in entries[-15:][::-1])

    g = last.get("gpus") or [{}, {}]
    def gv(i, k, suf=""):
        v = g[i].get(k) if i < len(g) else None
        return f"{v}{suf}" if v is not None else "–"

    vitals = f"""
    <div class="vital"><span class="lbl">tick</span><span class="mono">{esc(last.get('ts','–')[11:19])}</span></div>
    <div class="vital"><span class="lbl">GPU0</span><span class="mono">{gv(0,'util_pct','%')} · {gv(0,'power_w','W')} · {gv(0,'temp_c','°C')}</span></div>
    <div class="vital"><span class="lbl">GPU1</span><span class="mono">{gv(1,'util_pct','%')} · {gv(1,'power_w','W')} · {gv(1,'temp_c','°C')}</span></div>
    <div class="vital"><span class="lbl">tmux</span><span class="mono">{esc(', '.join(last.get('tmux') or []) or 'none')}</span></div>
    <div class="vital"><span class="lbl">server0 load/mem/disk</span><span class="mono">{esc(last.get('load1','–'))} · {esc(last.get('mem_avail_gb','–'))}G · {esc(last.get('disk_pct','–'))}%</span></div>
    <div class="vital"><span class="lbl">server-3 disk</span><span class="mono">{esc(last.get('remote_disk_pct','–'))}%</span></div>"""

    doc = f"""<title>EAIR ops — pmj-idea</title>
<style>
  :root {{
    --bg:#131a21; --panel:#1b232d; --panel2:#202a35; --line:#2b3642;
    --ink:#e6e2d8; --dim:#8b96a4; --acc:#7fb4c9;
    --good:#6aa87b; --warn:#d1a04a; --crit:#c65f57;
  }}
  html {{ background:var(--bg); }}
  body {{ color:var(--ink); font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;
         max-width:1100px; margin:0 auto; padding:28px 20px 60px; }}
  .mono {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
           font-variant-numeric:tabular-nums; font-size:13.5px; }}
  header {{ display:flex; justify-content:space-between; align-items:baseline;
            border-bottom:1px solid var(--line); padding-bottom:14px; margin-bottom:22px; }}
  h1 {{ font-size:17px; margin:0; letter-spacing:.4px; }}
  h1 .proj {{ color:var(--acc); }}
  header .mono {{ color:var(--dim); }}
  h2 {{ font-size:11.5px; text-transform:uppercase; letter-spacing:.14em; color:var(--dim);
        margin:26px 0 10px; font-weight:600; }}
  .strip {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
            gap:10px; }}
  .vital {{ background:var(--panel); border:1px solid var(--line); border-radius:4px;
            padding:9px 12px; display:flex; flex-direction:column; gap:2px; }}
  .lbl {{ font-size:10.5px; text-transform:uppercase; letter-spacing:.12em; color:var(--dim); }}
  .chip {{ display:inline-block; padding:1px 9px; border-radius:3px; font-size:11.5px;
           font-family:ui-monospace,Menlo,monospace; letter-spacing:.04em; }}
  .chip.good {{ background:#22352a; color:var(--good); }}
  .chip.warn {{ background:#3a3120; color:var(--warn); }}
  .chip.crit {{ background:#3b2624; color:var(--crit); }}
  .chip.acc  {{ background:#213038; color:var(--acc); }}
  .treewrap {{ display:grid; grid-template-columns:minmax(300px,5fr) minmax(280px,4fr);
               gap:18px; }}
  @media (max-width:760px) {{ .treewrap {{ grid-template-columns:1fr; }} }}
  .tree ul {{ list-style:none; margin:0; padding-left:20px; border-left:1px solid var(--line); }}
  .tree > ul {{ padding-left:0; border-left:none; }}
  .tree li {{ padding:3px 0; }}
  .node {{ display:flex; gap:9px; align-items:baseline; background:none; border:1px solid
           transparent; border-radius:4px; padding:5px 8px; width:100%; text-align:left;
           color:var(--ink); font:inherit; cursor:pointer; }}
  .node:hover {{ background:var(--panel2); }}
  .node:focus-visible {{ outline:1.5px solid var(--acc); }}
  .node.sel {{ background:var(--panel2); border-color:var(--acc); }}
  .hyp-id {{ font-family:ui-monospace,Menlo,monospace; color:var(--acc); min-width:42px; }}
  .node-short {{ color:var(--dim); font-size:13px; }}
  .detail {{ background:var(--panel2); border:1px solid var(--line); border-radius:4px;
             padding:14px 16px; font-size:13.5px; align-self:start;
             position:sticky; top:14px; }}
  .detail h3 {{ margin:0 0 8px; font-size:14px; font-family:ui-monospace,Menlo,monospace;
               color:var(--acc); }}
  .detail dt {{ font-size:10.5px; text-transform:uppercase; letter-spacing:.12em;
               color:var(--dim); margin-top:10px; }}
  .detail dd {{ margin:3px 0 0; }}
  .detail .exps span {{ margin-right:8px; }}
  table {{ border-collapse:collapse; width:100%; }}
  td {{ padding:6px 10px 6px 0; border-bottom:1px solid var(--line); vertical-align:top; }}
  .dim {{ color:var(--dim); }} .note {{ font-size:12.5px; }}
  .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:4px;
            padding:14px 16px; }}
  .scroll {{ overflow-x:auto; }}
  canvas {{ width:100%; height:120px; display:block; }}
  .legend {{ display:flex; gap:18px; margin-top:6px; font-size:12px; color:var(--dim); }}
  .sw {{ display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:5px;
         vertical-align:-1px; }}
</style>
<header>
  <h1>EAIR ops · <span class="proj">pmj-idea</span> · geometry_budget_repair</h1>
  <span class="mono">generated {esc(last.get('ts','?'))}</span>
</header>

<h2>Now</h2>
<div class="strip">{vitals}</div>

<h2>GPU utilization — last {len(series)} ticks (~{len(series)*2} min)</h2>
<div class="panel">
  <canvas id="gpu" width="1060" height="120"></canvas>
  <div class="legend"><span><span class="sw" style="background:var(--acc)"></span>GPU0</span>
  <span><span class="sw" style="background:var(--warn)"></span>GPU1</span></div>
</div>

<h2>Hypotheses</h2>
<div class="panel">{hyp_html or '<span class="dim">no tree.json</span>'}</div>

<h2>Experiment ledger</h2>
<div class="panel scroll"><table>{exp_rows}</table></div>

<h2>Clock — alarms (armed / fired / met)</h2>
<div class="panel scroll"><table>{alarms_html or '<tr><td class="dim">none</td></tr>'}</table></div>

<h2>Progress log — conductor, last 15</h2>
<div class="panel scroll"><table>{log_html}</table></div>

<script>
  const NODES = {json.dumps(node_data, ensure_ascii=False)};
  const detail = document.getElementById('detail');
  const CHIP = {json.dumps(verdict_cls)};
  function show(id) {{
    document.querySelectorAll('.node').forEach(b => b.classList.toggle('sel', b.dataset.id === id));
    const n = NODES[id]; if (!n) return;
    const cls = CHIP[n.status] || 'warn';
    const field = (lbl, val) => val ? `<dt>${{lbl}}</dt><dd>${{val}}</dd>` : '';
    const exps = n.experiments.map(e =>
      `<span class="chip ${{CHIP[e.verdict] || 'warn'}}">${{e.id}} ${{e.verdict || ''}}</span>`).join(' ');
    detail.innerHTML = `<h3>${{id}} <span class="chip ${{cls}}">${{n.status}}</span></h3>
      <div>${{n.short}}</div><dl>
      ${{field('Falsifiable form', n.falsifiable_form)}}
      ${{field('Mechanism claim', n.mechanism_claim)}}
      ${{field('Generalization scope', n.generalization_scope)}}
      ${{field('Kill criteria', n.kill_criteria)}}
      ${{n.experiments.length ? '<dt>Experiments</dt><dd class="exps">' + exps + '</dd>' : ''}}
      ${{field('Notes', n.notes)}}</dl>`;
  }}
  document.querySelectorAll('.node').forEach(b =>
    b.addEventListener('click', () => show(b.dataset.id)));
  const first = Object.keys(NODES).find(k => NODES[k].status === 'PROVEN') || Object.keys(NODES)[0];
  if (first) show(first);

  const S = {json.dumps(series)};
  const cv = document.getElementById('gpu'), cx = cv.getContext('2d');
  const W = cv.width, H = cv.height, n = S.length;
  cx.strokeStyle = '#2b3642'; cx.lineWidth = 1;
  [0, 50, 100].forEach(v => {{ const y = H - 8 - (H - 20) * v / 100;
    cx.beginPath(); cx.moveTo(0, y); cx.lineTo(W, y); cx.stroke(); }});
  const colors = ['#7fb4c9', '#d1a04a'];
  for (let gi = 0; gi < 2; gi++) {{
    cx.strokeStyle = colors[gi]; cx.lineWidth = 1.6; cx.beginPath();
    let started = false;
    S.forEach((t, i) => {{
      if (t.u.length <= gi) return;
      const x = n > 1 ? i * W / (n - 1) : 0;
      const y = H - 8 - (H - 20) * t.u[gi] / 100;
      started ? cx.lineTo(x, y) : cx.moveTo(x, y); started = true;
    }});
    cx.stroke();
    const lastPt = S.filter(t => t.u.length > gi).slice(-1)[0];
    if (lastPt) {{
      const i = S.lastIndexOf(lastPt);
      const x = n > 1 ? i * W / (n - 1) : 0;
      const y = H - 8 - (H - 20) * lastPt.u[gi] / 100;
      cx.fillStyle = colors[gi]; cx.beginPath(); cx.arc(x, y, 3, 0, 7); cx.fill();
    }}
  }}
</script>
"""
    open(a.out, "w").write(doc)
    print(f"dashboard: {a.out} ({len(doc)} bytes, {len(series)} ticks)")


if __name__ == "__main__":
    main()
