#!/usr/bin/env python3
"""EAIR pulse — the CPU-driven clock. Observes, timestamps, alarms. Never decides.

The LLM layers (conductor, workers, observer) have no internal clock; any time
claim they produce without an anchor is fabrication. pulse is the anchor: a dumb
process that ticks from cron, records objective liveness, and fires alarms that
agents registered. Time facts come from the machine; judgment stays with the LLMs.

Cron (every 2 min):
  */2 * * * * python3 <this file> --project-dir <project> [--gpu-host <ssh-alias>]

Outputs (append-only, inside --project-dir):
  PULSE.jsonl   one line per tick: wall time + observed activity (file mtimes,
                GPU util/mem, tmux sessions). Observed liveness — not agent
                self-reports. Rotates at 5 MB.
  ALARMS.jsonl  one line per fired alarm. Readers (observer/conductor) treat a
                new line as a wake signal; pulse itself takes no action.

Alarm registration — any agent drops a JSON file into alarms/pending/:
  {"id": "runner-e003-output",
   "deadline": "2026-07-03T04:00:00+08:00",
   "condition": {"type": "file_exists", "path": "experiments/E003/agents/runner/output.json"},
   "note": "Runner output expected within ~2h of GPU launch"}

condition.type:
  file_exists    met when <path> (relative to project dir) exists
  mtime_advance  met while <path>'s newest mtime is younger than <within_min>;
                 fires if it goes stale before deadline OR deadline passes
  none / absent  pure reminder; fires at deadline
Met alarms move to alarms/met/, fired ones to alarms/fired/ (fire once).
"""
import argparse, json, os, shutil, subprocess, sys
from datetime import datetime, timezone


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def newest_mtime(path):
    latest = 0.0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            try:
                m = os.path.getmtime(os.path.join(root, f))
                if m > latest:
                    latest = m
            except OSError:
                pass
    return latest


def observe_gpu(host):
    try:
        out = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host,
             "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits;"
             "echo ---; tmux ls 2>/dev/null || true"],
            capture_output=True, text=True, timeout=25)
        if out.returncode != 0:
            return {"reachable": False}
        gpu_part, _, tmux_part = out.stdout.partition("---")
        gpus = []
        for line in gpu_part.strip().splitlines():
            u, m = [x.strip() for x in line.split(",")[:2]]
            gpus.append({"util_pct": int(u), "mem_mib": int(m)})
        tmux = [l.split(":")[0] for l in tmux_part.strip().splitlines() if ":" in l]
        return {"reachable": True, "gpus": gpus, "tmux": tmux}
    except Exception:
        return {"reachable": False}


def append_line(path, obj, rotate_bytes=5_000_000):
    if os.path.exists(path) and os.path.getsize(path) > rotate_bytes:
        shutil.move(path, path + ".1")
    with open(path, "a") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def check_alarms(project, tick_ts):
    pending = os.path.join(project, "alarms", "pending")
    met_dir = os.path.join(project, "alarms", "met")
    fired_dir = os.path.join(project, "alarms", "fired")
    if not os.path.isdir(pending):
        return
    os.makedirs(met_dir, exist_ok=True)
    os.makedirs(fired_dir, exist_ok=True)
    now = datetime.now().astimezone()
    for name in sorted(os.listdir(pending)):
        fp = os.path.join(pending, name)
        try:
            alarm = json.load(open(fp))
        except Exception:
            continue  # half-written registration; next tick
        cond = alarm.get("condition") or {}
        ctype = cond.get("type", "none")
        target = os.path.join(project, cond.get("path", "")) if cond.get("path") else None

        met, stale = False, False
        if ctype == "file_exists" and target:
            met = os.path.exists(target)
        elif ctype == "mtime_advance" and target:
            within = float(cond.get("within_min", 20)) * 60
            m = newest_mtime(target) if os.path.isdir(target) else (
                os.path.getmtime(target) if os.path.exists(target) else 0)
            stale = (now.timestamp() - m) > within

        deadline = None
        try:
            deadline = datetime.fromisoformat(alarm["deadline"])
        except (KeyError, ValueError):
            pass
        overdue = deadline is not None and now >= deadline

        if met:
            alarm["met_at"] = tick_ts
            json.dump(alarm, open(os.path.join(met_dir, name), "w"), ensure_ascii=False, indent=1)
            os.remove(fp)
        elif overdue or (ctype == "mtime_advance" and stale):
            alarm["fired_at"] = tick_ts
            alarm["fired_because"] = "deadline" if overdue else "went_stale"
            append_line(os.path.join(project, "ALARMS.jsonl"), alarm)
            json.dump(alarm, open(os.path.join(fired_dir, name), "w"), ensure_ascii=False, indent=1)
            os.remove(fp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", required=True)
    ap.add_argument("--gpu-host", default=os.environ.get("EAIR_GPU_HOST", ""))
    args = ap.parse_args()
    project = os.path.expanduser(args.project_dir)
    if not os.path.isdir(project):
        sys.exit(f"pulse: no such project dir: {project}")

    ts = now_iso()
    writes = {}
    exp_root = os.path.join(project, "experiments")
    if os.path.isdir(exp_root):
        for d in sorted(os.listdir(exp_root)):
            p = os.path.join(exp_root, d)
            if os.path.isdir(p):
                m = newest_mtime(p)
                if m:
                    writes[d] = datetime.fromtimestamp(m).astimezone().isoformat(timespec="seconds")

    tick = {"ts": ts, "newest_writes": writes}
    if args.gpu_host:
        tick["gpu_host"] = args.gpu_host
        tick.update(observe_gpu(args.gpu_host))
    append_line(os.path.join(project, "PULSE.jsonl"), tick)
    check_alarms(project, ts)


if __name__ == "__main__":
    main()
