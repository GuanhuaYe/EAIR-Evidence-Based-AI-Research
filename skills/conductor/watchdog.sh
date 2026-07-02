#!/bin/bash
# the conductor Watchdog — displays experiment progress in tmux status bar
# Usage: bash watchdog.sh <PID> <LOG_FILE> [TIMEOUT_MIN]
# Runs in background, updates tmux status-right every 1s
# Sends email on CRASH or TIMEOUT via notify.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID=${1:?Usage: watchdog.sh <PID> <LOG_FILE>}
LOG=${2:?Usage: watchdog.sh <PID> <LOG_FILE>}
TIMEOUT_MIN=${3:-120}  # default 2h timeout
START_TIME=$(date +%s)
TIMEOUT_SEC=$((TIMEOUT_MIN * 60))
ALERTED=0  # prevent duplicate emails

update_tmux() {
    local msg="$1"
    tmux set-option -g status-right "$msg" 2>/dev/null
}

send_alert() {
    local subject="$1"
    local body="$2"
    if [ $ALERTED -eq 0 ]; then
        bash "$SCRIPT_DIR/notify.sh" "$subject" "$body" &
        ALERTED=1
    fi
}

cleanup() {
    tmux set-option -g status-right "" 2>/dev/null
    exit 0
}
trap cleanup EXIT INT TERM

while true; do
    # Check if process is alive
    if ! kill -0 "$PID" 2>/dev/null; then
        TAIL=$(tail -10 "$LOG" 2>/dev/null)
        if echo "$TAIL" | grep -qi "error\|traceback\|exception"; then
            update_tmux "#[fg=red,bold] CRASHED #[default]| check log"
            send_alert "Experiment CRASHED (PID $PID)" "$(tail -20 "$LOG" 2>/dev/null)"
            sleep 1
            cleanup
        else
            update_tmux "#[fg=green,bold] DONE #[default]| $(date +%H:%M)"
            send_alert "Experiment DONE (PID $PID)" "Completed at $(date). Check results."
            sleep 1
            cleanup
        fi
    fi

    # Extract progress from log
    ELAPSED=$(( $(date +%s) - START_TIME ))
    ELAPSED_MIN=$((ELAPSED / 60))

    # Parse latest progress line
    PROGRESS=$(tail -5 "$LOG" 2>/dev/null | tr '\r' '\n' | grep -oP '\d+%.*?\d+/\d+' | tail -1)
    STEP=$(tail -20 "$LOG" 2>/dev/null | tr '\r' '\n' | grep -oP '\[Step [A-Z]\]' | tail -1)
    SPEED=$(tail -5 "$LOG" 2>/dev/null | tr '\r' '\n' | grep -oP '\d+\.\d+s/it' | tail -1)

    if [ -n "$PROGRESS" ]; then
        update_tmux "#[fg=cyan]${STEP:-Run}#[default] ${PROGRESS} | ${SPEED:-?} | ${ELAPSED_MIN}m/${TIMEOUT_MIN}m"
    else
        update_tmux "#[fg=yellow]EXP#[default] running | ${ELAPSED_MIN}m/${TIMEOUT_MIN}m"
    fi

    # Timeout check
    if [ $ELAPSED -ge $TIMEOUT_SEC ]; then
        update_tmux "#[fg=red,bold] TIMEOUT ${ELAPSED_MIN}m>${TIMEOUT_MIN}m #[default]"
        send_alert "Experiment TIMEOUT (PID $PID)" \
            "Exceeded ${TIMEOUT_MIN}min limit. Elapsed: ${ELAPSED_MIN}min.
Last progress: ${PROGRESS:-unknown}
Last step: ${STEP:-unknown}
Speed: ${SPEED:-unknown}

Last 10 lines of log:
$(tail -10 "$LOG" 2>/dev/null)"
        echo "[$(date)] WATCHDOG TIMEOUT: PID $PID exceeded ${TIMEOUT_MIN}min" >> /tmp/conductor_watchdog.log
        sleep 60  # don't spam, check once per minute after timeout
        continue
    fi

    sleep 1
done
