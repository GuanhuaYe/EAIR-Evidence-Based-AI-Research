#!/usr/bin/env bash
# EAIR live-panel controller.
#
# Installs/switches/stops the tailnet-bound ops panel as a systemd service so
# that changing the active EAIR project is ONE command instead of hand-editing
# the unit file. The panel itself (panel.py) is stdlib-only and burns zero LLM
# tokens; this wrapper just owns its lifecycle.
#
#   panel_ctl.sh switch <project-dir> [--gpu-host A] [--port N] [--bind IP]
#                                     [--transcripts DIR] [--tasks-dir DIR]
#   panel_ctl.sh stop
#   panel_ctl.sh status
#   panel_ctl.sh url
#
# Two-tier note (EAIR conductor): the Claude session's cwd (the control
# plane, e.g. ~/research/control-plane) is NOT the same as <project-dir> (e.g.
# .../<project>/big_finding). panel.py derives its transcript/tasks slug from
# <project-dir>, which is wrong in that layout — so this wrapper auto-detects
# the live session dirs (newest under ~/.claude/projects) and passes them
# explicitly. Override with --transcripts / --tasks-dir when you have >1 live
# session and the newest isn't the one you mean.
set -euo pipefail

SERVICE=eair-panel
UNIT="/etc/systemd/system/${SERVICE}.service"
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
PANEL="$SCRIPT_DIR/panel.py"

cmd="${1:-}"; shift || true
case "$cmd" in
  stop)
    sudo systemctl disable --now "$SERVICE" 2>/dev/null || true
    echo "panel stopped + disabled."; exit 0 ;;
  status)
    systemctl status "$SERVICE" --no-pager 2>&1 | head -14; exit 0 ;;
  url)
    grep -oE -- '--bind [^ ]+ --port [0-9]+' "$UNIT" 2>/dev/null \
      | awk '{print "http://"$2":"$4}'; exit 0 ;;
  switch) : ;;
  *)
    echo "usage: panel_ctl.sh {switch <project-dir>|stop|status|url} [flags]" >&2
    exit 2 ;;
esac

PROJECT_DIR="${1:-}"; shift || true
[ -n "$PROJECT_DIR" ] || { echo "switch needs <project-dir>" >&2; exit 2; }
PROJECT_DIR="$(readlink -f "$PROJECT_DIR")"
[ -d "$PROJECT_DIR" ] || { echo "no such dir: $PROJECT_DIR" >&2; exit 2; }
[ -f "$PANEL" ] || { echo "panel.py not found next to this script: $PANEL" >&2; exit 2; }

BIND="$(tailscale ip -4 2>/dev/null | head -1 || true)"; BIND="${BIND:-127.0.0.1}"
PORT=8377
GPU_HOST="${EAIR_GPU_HOST:-gpu-host}"
TRANSCRIPTS=""; TASKS_DIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --gpu-host)    GPU_HOST="$2";    shift 2 ;;
    --port)        PORT="$2";        shift 2 ;;
    --bind)        BIND="$2";        shift 2 ;;
    --transcripts) TRANSCRIPTS="$2"; shift 2 ;;
    --tasks-dir)   TASKS_DIR="$2";   shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
done

# Auto-detect the live Claude session dirs (control-plane cwd), newest first.
if [ -z "$TRANSCRIPTS" ]; then
  TRANSCRIPTS="$(ls -1dt "$HOME"/.claude/projects/*/ 2>/dev/null | head -1 || true)"
  TRANSCRIPTS="${TRANSCRIPTS%/}"
fi
if [ -z "$TASKS_DIR" ] && [ -n "$TRANSCRIPTS" ]; then
  slug="$(basename "$TRANSCRIPTS")"
  TASKS_DIR="$(ls -1dt /tmp/claude-*/"$slug"/ 2>/dev/null | head -1 || true)"
  TASKS_DIR="${TASKS_DIR%/}"
fi

EXEC="/usr/bin/python3 $PANEL --project-dir $PROJECT_DIR --bind $BIND --port $PORT --gpu-host $GPU_HOST"
[ -n "$TRANSCRIPTS" ] && EXEC="$EXEC --transcripts $TRANSCRIPTS"
[ -n "$TASKS_DIR" ]   && EXEC="$EXEC --tasks-dir $TASKS_DIR"

sudo tee "$UNIT" >/dev/null <<EOF
[Unit]
Description=EAIR live ops panel (tailnet-bound)
After=network-online.target tailscaled.service

[Service]
User=$USER
ExecStart=$EXEC
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE" >/dev/null 2>&1 || sudo systemctl restart "$SERVICE"
sleep 1
echo "panel  → $PROJECT_DIR"
echo "session→ ${TRANSCRIPTS:-<panel-default>}"
echo "url    → http://$BIND:$PORT   (gpu-host=$GPU_HOST)"
if systemctl is-active "$SERVICE" >/dev/null 2>&1; then
  echo "status → active"
else
  echo "status → FAILED; last log:"; journalctl -u "$SERVICE" --no-pager 2>/dev/null | tail -15
  exit 1
fi
