#!/usr/bin/env python3
"""EAIR shepherd — CPU wave executor for multi-wave GPU sweeps. Zero LLM tokens.

Executes a declarative wave plan (waves.json) that an LLM Engineer/Runner
compiled beforehand: launch each wave, poll until its done-check passes,
run the gate checks, move on. Any off-nominal condition — gate failure,
timeout, command error — appends an alarm to ALARMS.jsonl and exits
nonzero; judgment belongs to whoever watches the alarms, not to this
script. The nominal path never involves a language model.

waves.json:
{
  "project_dir": "/abs/path",               # for HEARTBEAT.jsonl + ALARMS.jsonl
  "experiment": "E00X_...",
  "poll_seconds": 300,
  "max_wave_seconds": 3600,
  "waves": [
    {"id": "w1-gemma-belebele",
     "launch": "ssh gpu-host 'tmux new-session -d ...'",   # shell string
     "done":   "ssh gpu-host 'grep -q EXIT= .../en.log && grep -q EXIT= .../zh.log'",
     "gates": [
       {"desc": "exit codes 0",        "check": "ssh gpu-host 'grep -q EXIT=0 .../en.log && grep -q EXIT=0 .../zh.log'"},
       {"desc": "sanity floor",        "check": "ssh gpu-host 'python3 .../gate.py --floor 0.35'"}
     ]},
    ...
  ],
  "finish": ["...merge cmd...", "...rsync cmd..."]          # run after all waves pass
}

Every check is a shell command; exit 0 = pass. The LLM compiles judgment
into these commands ahead of time (smart zone writes the plan); this
script only executes and reports (dumb zone runs it).

Usage: shepherd.py --plan waves.json [--start-at WAVE_ID]
"""
import argparse, json, os, subprocess, sys, time


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def sh(cmd, timeout):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout)
        return r.returncode, (r.stdout + r.stderr)[-500:]
    except subprocess.TimeoutExpired:
        return 124, "timeout"


class Plan:
    def __init__(self, path):
        self.d = json.load(open(path))
        self.project = os.path.expanduser(self.d["project_dir"])
        self.exp = self.d.get("experiment", "?")

    def beat(self, event):
        line = json.dumps({"ts": now(), "agent": "shepherd",
                           "experiment": self.exp, "event": event},
                          ensure_ascii=False)
        with open(os.path.join(self.project, "HEARTBEAT.jsonl"), "a") as f:
            f.write(line + "\n")
        print(line, flush=True)

    def alarm(self, aid, note):
        with open(os.path.join(self.project, "ALARMS.jsonl"), "a") as f:
            f.write(json.dumps({"id": aid, "fired_at": now(),
                                "fired_because": "shepherd_offnominal",
                                "registered_by": "shepherd", "note": note[:500]},
                               ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--start-at", default="")
    a = ap.parse_args()
    p = Plan(a.plan)
    poll = int(p.d.get("poll_seconds", 300))
    max_wave = int(p.d.get("max_wave_seconds", 3600))

    waves = p.d["waves"]
    if a.start_at:
        ids = [w["id"] for w in waves]
        if a.start_at not in ids:
            sys.exit(f"unknown wave id {a.start_at}")
        waves = waves[ids.index(a.start_at):]

    for w in waves:
        wid = w["id"]
        p.beat(f"{wid}: launch")
        rc, out = sh(w["launch"], timeout=300)
        if rc != 0:
            p.alarm(f"shepherd-{wid}-launch-fail", f"launch rc={rc}: {out}")
            p.beat(f"{wid}: LAUNCH FAILED rc={rc} — alarm written, stopping")
            sys.exit(1)

        t0 = time.time()
        while True:
            time.sleep(poll)
            rc, _ = sh(w["done"], timeout=120)
            elapsed = int(time.time() - t0)
            if rc == 0:
                p.beat(f"{wid}: done after {elapsed}s")
                break
            if elapsed > max_wave:
                p.alarm(f"shepherd-{wid}-timeout",
                        f"wave exceeded {max_wave}s without done-check passing")
                p.beat(f"{wid}: TIMEOUT — alarm written, stopping")
                sys.exit(1)
            p.beat(f"{wid}: running, {elapsed}s elapsed")

        for g in w.get("gates", []):
            rc, out = sh(g["check"], timeout=300)
            if rc != 0:
                p.alarm(f"shepherd-{wid}-gate-fail",
                        f"gate '{g.get('desc','?')}' rc={rc}: {out}")
                p.beat(f"{wid}: GATE FAIL '{g.get('desc','?')}' — alarm written, stopping")
                sys.exit(1)
            p.beat(f"{wid}: gate pass — {g.get('desc','?')}")

    for cmd in p.d.get("finish", []):
        rc, out = sh(cmd, timeout=1800)
        if rc != 0:
            p.alarm("shepherd-finish-fail", f"finish cmd rc={rc}: {out}")
            p.beat(f"finish: FAILED rc={rc} — alarm written, stopping")
            sys.exit(1)
        p.beat("finish: step ok")
    p.beat("ALL WAVES COMPLETE — finish steps done")


if __name__ == "__main__":
    main()
