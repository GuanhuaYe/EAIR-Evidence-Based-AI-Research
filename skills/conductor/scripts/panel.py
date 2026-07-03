#!/usr/bin/env python3
"""EAIR live ops panel — read-mostly HTTP service, stdlib only, zero LLM tokens.

Serves a single-page console with 3s polling:
  GET  /            the page
  GET  /api/state   JSON: clock, host vitals, GPU (background-sampled), agents
                    (context occupancy + latest activity parsed from transcript
                    tails), conversation mirror, hypotheses, experiments,
                    alarms, conductor log
  POST /api/say     append {ts, text} to <project>/PANEL_INBOX.jsonl — the
                    observer tails this file; binding to a tailnet IP is the
                    access control.

Run:  panel.py --project-dir P --bind 100.x.y.z --port 8377
      [--gpu-host alias] [--transcripts ~/.claude/projects/<slug>]
      [--tasks-dir /tmp/claude-1000/<slug>]
"""
import argparse, glob, json, os, re, shutil, subprocess, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ARGS = None
GPU = {"sampled_at": 0}          # background sampler writes, requests read
_TAIL_CACHE = {}                 # path -> (mtime, size, parsed)


def tail_jsonl(path, max_bytes=262144):
    """Parse the last complete JSONL records of a file, cached by (mtime,size)."""
    try:
        st = os.stat(path)
    except OSError:
        return []
    key = (st.st_mtime, st.st_size)
    hit = _TAIL_CACHE.get(path)
    if hit and hit[0] == key:
        return hit[1]
    out = []
    with open(path, "rb") as f:
        if st.st_size > max_bytes:
            f.seek(st.st_size - max_bytes)
            f.readline()                      # drop partial first line
        for line in f.read().decode("utf-8", "replace").splitlines():
            line = line.strip()
            if line:
                try:
                    rec = json.loads(line)
                    if isinstance(rec, dict):
                        out.append(rec)
                except Exception:
                    pass
    _TAIL_CACHE[path] = (key, out)
    if len(_TAIL_CACHE) > 64:
        _TAIL_CACHE.pop(next(iter(_TAIL_CACHE)))
    return out


def text_of(msg):
    """Flatten a transcript message's content to plain text."""
    c = msg.get("content")
    if isinstance(c, str):
        return c
    parts = []
    for b in c or []:
        if isinstance(b, dict) and b.get("type") == "text":
            parts.append(b.get("text", ""))
    return "\n".join(parts)


def last_usage(records):
    """Newest usage block -> (occupancy_tokens, window_guess)."""
    for r in reversed(records):
        m = r.get("message") or {}
        u = m.get("usage") or r.get("usage")
        if u and u.get("input_tokens") is not None:
            occ = sum(u.get(k) or 0 for k in (
                "input_tokens", "cache_creation_input_tokens",
                "cache_read_input_tokens", "output_tokens"))
            model = m.get("model") or r.get("model") or ""
            win = 1_000_000 if ("[1m]" in model or occ > 200_000) else 200_000
            return occ, win, model
    return None, None, ""


def agent_card(path):
    recs = tail_jsonl(path)
    if not recs:
        return None
    occ, win, model = last_usage(recs)
    label, activity = "", ""
    for r in recs:                                    # first user text = task label
        if r.get("type") == "user" or (r.get("message") or {}).get("role") == "user":
            label = text_of(r.get("message") or r)[:90].replace("\n", " ")
            if label:
                break
    for r in reversed(recs):                          # newest assistant text = activity
        m = r.get("message") or {}
        if m.get("role") == "assistant" or r.get("type") == "assistant":
            t = text_of(m or r).strip()
            if t:
                activity = t[:280].replace("\n", " ")
                break
    st = os.stat(path)
    return {"id": os.path.basename(path).split(".")[0], "label": label,
            "occupancy": occ, "window": win, "model": model.split("/")[-1],
            "activity": activity, "mtime": int(st.st_mtime),
            "live": (time.time() - st.st_mtime) < 300}


def conversation(transcripts_dir, limit=14):
    files = sorted(glob.glob(os.path.join(transcripts_dir, "*.jsonl")),
                   key=os.path.getmtime)
    if not files:
        return [], None
    recs = tail_jsonl(files[-1], max_bytes=524288)
    msgs = []
    for r in recs:
        m = r.get("message") or {}
        role = m.get("role") or r.get("type")
        if role not in ("user", "assistant"):
            continue
        t = text_of(m or r).strip()
        if not t or t.startswith("<") and "system-reminder" in t[:40]:
            continue
        msgs.append({"role": role, "text": t[:600], "ts": r.get("timestamp", "")})
    occ, win, _ = last_usage(recs)
    return msgs[-limit:], ({"occupancy": occ, "window": win} if occ else None)


def gpu_sampler():
    while True:
        if ARGS.gpu_host:
            try:
                out = subprocess.run(
                    ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6",
                     ARGS.gpu_host,
                     "nvidia-smi --query-gpu=utilization.gpu,memory.used,"
                     "memory.total,power.draw,power.limit,temperature.gpu"
                     " --format=csv,noheader,nounits;"
                     "echo ---; tmux ls 2>/dev/null|cut -d: -f1"],
                    capture_output=True, text=True, timeout=10)
                gp, _, tm = out.stdout.partition("---")
                gpus = []
                for ln in gp.strip().splitlines():
                    f = [x.strip() for x in ln.split(",")]
                    gpus.append({"util": int(f[0]), "mem": int(f[1]),
                                 "mem_total": int(f[2]), "w": float(f[3]),
                                 "w_cap": float(f[4]), "t": int(f[5])})
                hist = GPU.get("hist") or []
                hist.append({"t": int(time.time()),
                             "u": [g["util"] for g in gpus]})
                GPU.update({"gpus": gpus, "tmux": tm.strip().splitlines(),
                            "sampled_at": int(time.time()), "ok": True,
                            "hist": hist[-240:]})
            except Exception:
                GPU.update({"ok": False, "sampled_at": int(time.time())})
        time.sleep(12)


def build_state():
    P = ARGS.project_dir
    tree = {}
    try:
        tree = json.load(open(os.path.join(P, "tree.json")))
    except Exception:
        pass
    log = []
    try:
        doc = json.load(open(os.path.join(P, "CONDUCTOR_LOG.json")))
        log = doc if isinstance(doc, list) else (doc.get("entries") or [])
    except Exception:
        pass
    exps = []
    for d in sorted(glob.glob(os.path.join(P, "experiments", "*"))):
        v = "in progress"
        dm = os.path.join(d, "decision.md")
        if os.path.exists(dm):
            m = re.search(r"\*\*Verdict:\s*([A-Z_]+)\*\*", open(dm).read(600))
            v = m.group(1) if m else "decided"
        exps.append({"name": os.path.basename(d), "verdict": v})
    alarms = []
    for sub, state in (("pending", "armed"), ("fired", "fired"), ("met", "met")):
        for f in sorted(glob.glob(os.path.join(P, "alarms", sub, "*.json")))[-5:]:
            try:
                a = json.load(open(f))
                alarms.append({"id": a.get("id"), "state": state,
                               "deadline": a.get("deadline", ""),
                               "note": (a.get("note") or "")[:140]})
            except Exception:
                pass
    agents = []
    for f in glob.glob(os.path.join(ARGS.tasks_dir, "*", "tasks", "*.output")):
        if time.time() - os.path.getmtime(f) < 86400:
            c = agent_card(f)
            if c:
                agents.append(c)
    agents.sort(key=lambda c: -c["mtime"])
    convo, obs_ctx = conversation(ARGS.transcripts)
    du = shutil.disk_usage(P)
    mem = {}
    try:
        mem = dict(l.split(":")[:2] for l in open("/proc/meminfo").read().splitlines()[:3])
    except Exception:
        pass
    return {
        "epoch": time.time(),
        "host": {"load1": float(open("/proc/loadavg").read().split()[0]),
                 "mem_avail_gb": round(int(mem.get("MemAvailable", "0 kB").split()[0]) / 1048576, 1),
                 "disk_pct": round(du.used / du.total * 100)},
        "gpu": GPU, "agents": agents[:10],
        "observer": {"messages": convo, "context": obs_ctx},
        "hypotheses": [{"id": k, "status": v.get("status"),
                        "short": (v.get("short") or "")[:110]}
                       for k, v in (tree.get("nodes") or {}).items()],
        "experiments": exps,
        "alarms": alarms,
        "log": [{"ts": e.get("timestamp", ""), "action": e.get("action", ""),
                 "detail": (e.get("detail") or e.get("id") or "")[:150]}
                for e in log[-12:]][::-1],
    }


PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EAIR live panel</title>
<style>
:root{--bg:#131a21;--panel:#1b232d;--panel2:#202a35;--line:#2b3642;--ink:#e6e2d8;
--dim:#8b96a4;--acc:#7fb4c9;--good:#6aa87b;--warn:#d1a04a;--crit:#c65f57}
*{box-sizing:border-box}html{background:var(--bg)}
body{color:var(--ink);font:14px/1.5 system-ui,sans-serif;max-width:1150px;margin:0 auto;padding:18px 16px 50px}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-variant-numeric:tabular-nums;font-size:12.5px}
header{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:14px}
h1{font-size:15px;margin:0;letter-spacing:.4px}h1 span{color:var(--acc)}
#clock{font-size:16px;color:var(--acc)}
.mod{background:var(--panel);border:1px solid var(--line);border-radius:5px;margin-bottom:12px}
.mod-h{display:flex;justify-content:space-between;padding:7px 12px;border-bottom:1px solid var(--line);
cursor:grab;user-select:none;font-size:10.5px;text-transform:uppercase;letter-spacing:.13em;color:var(--dim)}
.mod-b{padding:10px 12px;overflow-y:auto;overflow-x:hidden;resize:vertical;min-height:60px;height:240px}
#talk{height:430px}#now{height:300px}#log{height:260px}
.mod-b::-webkit-scrollbar{width:9px}.mod-b::-webkit-scrollbar-track{background:var(--panel)}
.mod-b::-webkit-scrollbar-thumb{background:var(--line);border-radius:4px}
.mod-b::-webkit-scrollbar-thumb:hover{background:var(--dim)}
.mod-b{scrollbar-width:thin;scrollbar-color:var(--line) var(--panel)}
.mod.drag{opacity:.4}
.chip{display:inline-block;padding:0 8px;border-radius:3px;font-size:11px;font-family:ui-monospace,Menlo,monospace}
.chip.good{background:#22352a;color:var(--good)}.chip.warn{background:#3a3120;color:var(--warn)}
.chip.crit{background:#3b2624;color:var(--crit)}.chip.acc{background:#213038;color:var(--acc)}
table{border-collapse:collapse;width:100%}td{padding:4px 10px 4px 0;border-bottom:1px solid var(--line);vertical-align:top}
.dim{color:var(--dim)}.small{font-size:12px}
.bar{height:6px;background:var(--panel2);border-radius:3px;min-width:90px}
.bar i{display:block;height:6px;border-radius:3px;background:var(--acc)}
.bar i.hot{background:var(--crit)}.bar i.mid{background:var(--warn)}
.msg{margin:6px 0;padding:7px 10px;border-radius:5px;max-width:88%;white-space:pre-wrap;font-size:13px}
.msg.user{background:#213038;margin-left:auto}.msg.assistant{background:var(--panel2)}
#say{display:flex;gap:8px;margin-top:8px}
#say input{flex:1;background:var(--panel2);border:1px solid var(--line);border-radius:4px;color:var(--ink);padding:7px 10px;font:inherit}
#say button{background:#213038;color:var(--acc);border:1px solid var(--acc);border-radius:4px;padding:7px 14px;cursor:pointer;font:inherit}
#say button:hover{background:#2a3d47}
.vitals{display:flex;gap:18px;flex-wrap:wrap}
.lbl{font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:var(--dim)}
.gpugrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.gpucard{background:var(--panel2);border:1px solid var(--line);border-radius:6px;padding:10px 12px}
.gpuhead{display:flex;justify-content:space-between;align-items:baseline}
.gpumain{display:flex;gap:12px;align-items:center;margin-top:6px}
.gpumeters{flex:1;display:flex;flex-direction:column;gap:8px}
.meter{display:grid;grid-template-columns:52px 1fr auto;gap:8px;align-items:center}
.bar.wide{min-width:60px}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head><body>
<header><h1>EAIR live · <span>pmj-idea</span></h1><div id="clock" class="mono">--:--:--</div></header>
<div id="mods"></div>
<script>
const MODS=[
 {id:'talk',title:'observer — conversation'},
 {id:'now',title:'now — host & gpu'},
 {id:'agents',title:'agents — context & activity'},
 {id:'hyp',title:'knowledge tree'},
 {id:'exp',title:'experiments'},
 {id:'alarms',title:'clock — alarms'},
 {id:'log',title:'progress log'}];
const saved=JSON.parse(localStorage.getItem('order')||'null');
const order=(saved&&saved.length===MODS.length)?saved:MODS.map(m=>m.id);
const hts=JSON.parse(localStorage.getItem('hts')||'{}');
const root=document.getElementById('mods');
order.forEach(id=>{const m=MODS.find(x=>x.id===id);if(!m)return;
 const d=document.createElement('div');d.className='mod';d.id='mod-'+id;
 const inner = id==='talk'
  ? `<div id="talkmsgs"></div><div id="say"><input id="sayin" placeholder="message the observer…"><button onclick="say()">Send</button></div>`
  : '';
 d.innerHTML=`<div class="mod-h" draggable="true"><span>${m.title}</span><span class="dim">⋮⋮</span></div><div class="mod-b" id="${id}">${inner}</div>`;
 if(hts[id])d.querySelector('.mod-b').style.height=hts[id]+'px';
 root.appendChild(d);});
let dragEl=null;
root.addEventListener('dragstart',e=>{dragEl=e.target.closest('.mod');dragEl.classList.add('drag');});
root.addEventListener('dragend',()=>{if(dragEl)dragEl.classList.remove('drag');dragEl=null;
 localStorage.setItem('order',JSON.stringify([...root.children].map(c=>c.id.slice(4))));});
root.addEventListener('dragover',e=>{e.preventDefault();const t=e.target.closest('.mod');
 if(!t||t===dragEl)return;const r=t.getBoundingClientRect();
 root.insertBefore(dragEl,(e.clientY-r.top)>r.height/2?t.nextSibling:t);});
document.addEventListener('mouseup',()=>{const h={};document.querySelectorAll('.mod-b').forEach(b=>{if(b.style.height)h[b.id]=parseInt(b.style.height)});localStorage.setItem('hts',JSON.stringify(h));});
let off=0;
function tick(){const d=new Date(Date.now()+off);
 document.getElementById('clock').textContent=d.toTimeString().slice(0,8);}
setInterval(tick,250);
const esc=s=>(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const _last={};
function put(id,html){ if(_last[id]===html)return;               // diff: untouched DOM if unchanged
 const el=document.getElementById(id); if(!el)return;
 const atBottom=el.scrollHeight-el.scrollTop-el.clientHeight<60;
 const st=el.scrollTop; el.innerHTML=html; _last[id]=html;
 el.scrollTop=(id==='talkmsgs'&&atBottom)?el.scrollHeight:st; }  // chat sticks to bottom, others keep place
const chip=(t,c)=>`<span class="chip ${c}">${esc(t)}</span>`;
const VC={REPLICATED:'good',PROVEN:'good',CONFIRMED:'good',INSUFFICIENT:'warn',CONFOUNDED:'warn',OPEN:'warn',FAIL:'crit',REFUTED:'crit',armed:'acc',fired:'crit',met:'good'};
function bar(occ,win){if(occ==null)return'<span class="dim">–</span>';
 const p=win?Math.min(100,occ/win*100):0;const cls=p>75?'hot':p>50?'mid':'';
 return`<div class="bar"><i class="${cls}" style="width:${p.toFixed(0)}%"></i></div><span class="mono dim">${(occ/1000).toFixed(0)}k/${(win/1000).toFixed(0)}k</span>`;}
async function poll(){try{
 const s=await(await fetch('/api/state')).json();
 off=s.epoch*1000-Date.now();
 const g=s.gpu.gpus||[];
 const hist0=(s.gpu.hist||[]).length;
 const ring=(pct,color)=>{const C=2*Math.PI*26,d=C*Math.min(100,pct)/100;
  return`<svg width="72" height="72" viewBox="0 0 64 64"><circle cx="32" cy="32" r="26" fill="none" stroke="var(--panel2)" stroke-width="7"/>
   <circle cx="32" cy="32" r="26" fill="none" stroke="${color}" stroke-width="7" stroke-linecap="round"
    stroke-dasharray="${d} ${C-d}" transform="rotate(-90 32 32)"/>
   <text x="32" y="37" text-anchor="middle" fill="var(--ink)" font-size="15" font-family="ui-monospace,Menlo,monospace">${pct}</text></svg>`;};
 const meter=(lbl,val,max,unit,warn,crit)=>{const p=Math.min(100,val/max*100);
  const c=p>crit?'var(--crit)':p>warn?'var(--warn)':'var(--acc)';
  return`<div class="meter"><span class="lbl">${lbl}</span>
   <div class="bar wide"><i style="width:${p.toFixed(0)}%;background:${c}"></i></div>
   <span class="mono dim">${val}${unit}</span></div>`;};
 const tempChip=t=>`<span class="chip ${t>=80?'crit':t>=65?'warn':'good'}">${t}°C</span>`;
 const utilColor=u=>u>85?'var(--good)':u>5?'var(--warn)':'var(--dim)';
 put('now',
  `<div class="gpugrid">${g.map((x,i)=>`<div class="gpucard">
     <div class="gpuhead"><span class="lbl">GPU${i} · util%</span>${tempChip(x.t)}</div>
     <div class="gpumain">${ring(x.util,utilColor(x.util))}
      <div class="gpumeters">
       ${meter('vram',(x.mem/1024).toFixed(1),(x.mem_total||49140)/1024,'G',75,92)}
       ${meter('power',Math.round(x.w),x.w_cap||200,'W',80,95)}
      </div></div></div>`).join('')}
   <div class="gpucard">
     <div class="gpuhead"><span class="lbl">server0</span><span class="mono dim">load ${s.host.load1}</span></div>
     <div class="gpumeters" style="margin-top:8px">
      ${meter('disk',s.host.disk_pct,100,'%',80,90)}
      ${meter('ram free',s.host.mem_avail_gb,8,'G',999,999)}
     </div>
     <div class="small dim" style="margin-top:6px">tmux: ${esc((s.gpu.tmux||[]).join(', ')||'none')} · gpu ${s.gpu.sampled_at?Math.round(s.epoch-s.gpu.sampled_at)+'s ago':'–'}</div>
   </div></div>
   <canvas id="ghist" data-n="${hist0}" height="46" style="width:100%;margin-top:10px"></canvas>`);
 const hist=s.gpu.hist||[];const hc=document.getElementById('ghist');
 if(hc&&hist.length>1){hc.width=hc.clientWidth;const c2=hc.getContext('2d');
  const W2=hc.width,H2=hc.height;
  ['#7fb4c9','#d1a04a'].forEach((col,gi)=>{c2.strokeStyle=col;c2.lineWidth=1.4;c2.beginPath();
   hist.forEach((h,i)=>{const x=i*W2/(hist.length-1),y=H2-4-(H2-8)*(h.u[gi]||0)/100;
    i?c2.lineTo(x,y):c2.moveTo(x,y);});c2.stroke();});}
 const oc=s.observer.context;
 put('talkmsgs',
  (oc?`<div class="small dim">observer context ${bar(oc.occupancy,oc.window)}</div>`:'')+
  s.observer.messages.map(m=>`<div class="msg ${m.role}">${esc(m.text)}</div>`).join(''));
 put('agents','<table>'+s.agents.map(a=>
  `<tr><td>${a.live?chip('live','good'):chip('idle','warn')}</td>
   <td class="mono">${esc(a.model||'?')}</td><td>${bar(a.occupancy,a.window)}</td>
   <td class="small"><div class="dim">${esc(a.label)}</div><div>${esc(a.activity)}</div></td></tr>`).join('')+'</table>');
 put('hyp','<table>'+s.hypotheses.map(h=>
  `<tr><td class="mono">${esc(h.id)}</td><td>${chip(h.status,VC[h.status]||'warn')}</td><td class="small dim">${esc(h.short)}</td></tr>`).join('')+'</table>');
 put('exp','<table>'+s.experiments.map(e=>
  `<tr><td class="mono">${esc(e.name)}</td><td>${chip(e.verdict,VC[e.verdict]||'warn')}</td></tr>`).join('')+'</table>');
 put('alarms','<table>'+s.alarms.map(a=>
  `<tr><td class="mono">${esc(a.id)}</td><td>${chip(a.state,VC[a.state])}</td><td class="mono dim">${esc((a.deadline||'').slice(11,16))}</td><td class="small dim">${esc(a.note)}</td></tr>`).join('')+'</table>');
 put('log','<table>'+s.log.map(e=>
  `<tr><td class="mono dim">${esc(e.ts.slice(5,16))}</td><td class="mono">${esc(e.action)}</td><td class="small dim">${esc(e.detail)}</td></tr>`).join('')+'</table>');
}catch(e){}}
async function say(){const i=document.getElementById('sayin');const t=i.value.trim();if(!t)return;
 await fetch('/api/say',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});
 i.value='';setTimeout(poll,800);}
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target.id==='sayin')say();});
poll();setInterval(poll,3000);
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif self.path == "/api/state":
            self._send(200, json.dumps(build_state(), ensure_ascii=False),
                       "application/json")
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/say":
            return self._send(404, "not found", "text/plain")
        n = min(int(self.headers.get("Content-Length", 0)), 16384)
        try:
            text = json.loads(self.rfile.read(n)).get("text", "").strip()[:4000]
        except Exception:
            text = ""
        if not text:
            return self._send(400, '{"ok":false}', "application/json")
        with open(os.path.join(ARGS.project_dir, "PANEL_INBOX.jsonl"), "a") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                "text": text}, ensure_ascii=False) + "\n")
        self._send(200, '{"ok":true}', "application/json")


def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", required=True)
    ap.add_argument("--bind", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8377)
    ap.add_argument("--gpu-host", default=os.environ.get("EAIR_GPU_HOST", ""))
    ap.add_argument("--transcripts", default="")
    ap.add_argument("--tasks-dir", default="")
    ARGS = ap.parse_args()
    ARGS.project_dir = os.path.expanduser(ARGS.project_dir)
    slug = ARGS.project_dir.replace("/", "-")
    if not ARGS.transcripts:
        ARGS.transcripts = os.path.expanduser(f"~/.claude/projects/{slug}")
    if not ARGS.tasks_dir:
        ARGS.tasks_dir = f"/tmp/claude-{os.getuid()}/{slug}"
    threading.Thread(target=gpu_sampler, daemon=True).start()
    srv = ThreadingHTTPServer((ARGS.bind, ARGS.port), H)
    print(f"panel: http://{ARGS.bind}:{ARGS.port}  project={ARGS.project_dir}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
