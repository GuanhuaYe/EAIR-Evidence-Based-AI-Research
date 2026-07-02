#!/bin/bash
# Refresh the control host's cache of the GPU host's shared resources.
# Captures: HF models, datasets, non-HF models, Python venvs, system Python ML packages.
#
# Configuration (env vars, all optional):
#   MAESTRO_GPU_HOST    SSH alias of the GPU host (default: gpu-host; configure in ~/.ssh/config)
#   PROJECT_ROOT        Local research root (default: ~/Paper); inventory written to $PROJECT_ROOT/.shared_inventory.md
#   MODELS_DIR   Shared model dir on the GPU host (default: ~/work/shared_models)
#   DATA_DIR     Shared dataset dir on the GPU host (default: ~/work/shared_data)
#   ENVS_DIR     Shared conda-env dir on the GPU host (default: ~/work/shared_envs)
#   REMOTE_ROOT         Workspace root on the GPU host (default: ~/work)
#
# Called on-demand before any acquisition action (hourly auto-refresh is
# optional heartbeat automation, not included in v1).
#
# NOT `set -e` — many sub-commands return non-zero naturally (grep -c on empty input).

GPU_HOST="${MAESTRO_GPU_HOST:-gpu-host}"
PROJECT_ROOT="${PROJECT_ROOT:-$HOME/Paper}"
INVENTORY="$PROJECT_ROOT/.shared_inventory.md"
R_MODELS="${MODELS_DIR:-~/work/shared_models}"
R_DATA="${DATA_DIR:-~/work/shared_data}"
R_ENVS="${ENVS_DIR:-~/work/shared_envs}"
R_ROOT="${REMOTE_ROOT:-~/work}"
TMP="$(mktemp)"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

RAW="$(ssh "$GPU_HOST" "MODELS_DIR=\"$R_MODELS\" DATA_DIR=\"$R_DATA\" ENVS_DIR=\"$R_ENVS\" REMOTE_ROOT=\"$R_ROOT\" bash -s" <<'REMOTE'
# Expand possible leading ~ in the passed paths
expand() { case "$1" in "~"*) echo "$HOME${1#\~}" ;; *) echo "$1" ;; esac; }
MODELS_DIR=$(expand "$MODELS_DIR")
DATA_DIR=$(expand "$DATA_DIR")
ENVS_DIR=$(expand "$ENVS_DIR")
REMOTE_ROOT=$(expand "$REMOTE_ROOT")

echo "===HF_MODELS==="
if [ -d "$MODELS_DIR/huggingface/hub" ]; then
    cd "$MODELS_DIR/huggingface/hub"
    for d in models--*; do
        [ -d "$d" ] || continue
        name=$(echo "$d" | sed "s|^models--||" | sed "s|--|/|")
        size=$(du -sh "$d" 2>/dev/null | cut -f1)
        mtime=$(stat -c "%y" "$d" 2>/dev/null | cut -d" " -f1)
        echo "$name|$size|$mtime"
    done
fi

echo "===DATASETS==="
if [ -d "$DATA_DIR" ]; then
    cd "$DATA_DIR"
    for d in */; do
        [ "$d" = "lost+found/" ] && continue
        name="${d%/}"
        size=$(du -sh "$d" 2>/dev/null | cut -f1)
        mtime=$(stat -c "%y" "$d" 2>/dev/null | cut -d" " -f1)
        echo "$name|$size|$mtime"
    done
fi

echo "===NON_HF_MODELS==="
if [ -d "$MODELS_DIR" ]; then
    cd "$MODELS_DIR"
    for d in */; do
        name="${d%/}"
        [ "$name" = "huggingface" ] && continue
        size=$(du -sh "$d" 2>/dev/null | cut -f1)
        echo "$name|$size"
    done
fi

echo "===VENVS==="
# Capture any python env: conda envs (preferred), venv, virtualenv, custom dirs.
# Sources: conda env list (if installed), $ENVS_DIR, conda base, env roots, generic */bin/python.
# Note: non-interactive ssh shell doesn't load .bashrc, so we explicitly source conda.sh.
for sh in ~/miniforge3/etc/profile.d/conda.sh ~/miniconda3/etc/profile.d/conda.sh ~/anaconda3/etc/profile.d/conda.sh /opt/conda/etc/profile.d/conda.sh; do
    [ -f "$sh" ] && . "$sh" && break
done

{
    # Conda CLI -- authoritative when present (includes base env)
    if command -v conda >/dev/null 2>&1; then
        conda env list 2>/dev/null | awk '!/^#/ && NF>=2 {print $NF}' | while read envpath; do
            [ -x "$envpath/bin/python" ] && echo "$envpath/bin/python"
        done
    fi
    # Conda base + env roots (covers cases where conda.sh sourcing fails)
    for envroot in "$ENVS_DIR" ~/.conda/envs ~/miniforge3/envs ~/miniconda3/envs ~/anaconda3/envs /opt/conda/envs; do
        [ -d "$envroot" ] || continue
        for e in "$envroot"/*; do
            [ -x "$e/bin/python" ] && echo "$e/bin/python"
        done
    done
    # Conda base env itself (lives at the miniforge root, not under envs/)
    for base in ~/miniforge3 ~/miniconda3 ~/anaconda3 /opt/conda; do
        [ -x "$base/bin/python" ] && echo "$base/bin/python"
    done
    # Generic venv search under workspaces
    for root in "$REMOTE_ROOT" "$HOME"; do
        [ -d "$root" ] || continue
        find "$root" -maxdepth 6 \( -path "*/.cache/*" -o -path "*/__pycache__*" -o -path "*/node_modules/*" -o -path "*/.git/*" -o -path "*/miniforge3/*" -o -path "*/miniconda3/*" \) -prune -o -type f -name python -print 2>/dev/null
    done | grep "/bin/python$"
} | sort -u | while read pybin; do
    venv=$(dirname "$(dirname "$pybin")")
    case "$venv" in /usr*) continue ;; esac
    pyver=$("$pybin" --version 2>&1 | tr -d "\n")
    # Tag env type
    case "$venv" in
        "$ENVS_DIR"/*) tag="[conda-shared]" ;;
        */miniforge3|*/miniconda3|*/anaconda3|/opt/conda) tag="[conda-base]" ;;
        */miniforge3/envs/*|*/miniconda3/envs/*|*/anaconda3/envs/*|*/.conda/envs/*|/opt/conda/envs/*) tag="[conda]" ;;
        *) tag="[venv]" ;;
    esac
    pip="$venv/bin/pip"
    if [ -x "$pip" ]; then
        pkgs=$("$pip" list 2>/dev/null | awk 'BEGIN{IGNORECASE=1} /^(vllm|transformers|torch|accelerate|datasets|peft|chromadb|sentence-transformers|flash-attn|deepspeed|trl|lightning|openai|anthropic)[ \t]/ {printf "%s==%s, ", $1, $2}' | sed "s/, $//")
        [ -z "$pkgs" ] && pkgs="(no key ML pkgs)"
    else
        pkgs="(no pip)"
    fi
    rel=$(echo "$venv" | sed "s|^$HOME|~|")
    echo "$tag $rel|$pyver|$pkgs"
done

echo "===SYSTEM_PY==="
for pyver in python3 python3.10 python3.11 python3.12; do
    pybin=$(command -v "$pyver" 2>/dev/null)
    [ -z "$pybin" ] && continue
    ver=$("$pybin" --version 2>&1)
    pkgs=$("$pybin" -c "
import importlib.metadata as md
for pkg in ['vllm','transformers','torch','accelerate','datasets','peft','chromadb','sentence-transformers','flash-attn','deepspeed','openai','anthropic']:
    try:
        print(f'{pkg}=={md.version(pkg)}', end=', ')
    except md.PackageNotFoundError:
        pass
" 2>/dev/null | sed "s/, $//")
    [ -z "$pkgs" ] && pkgs="(no key ML pkgs installed)"
    echo "$pybin|$ver|$pkgs"
done | sort -u
REMOTE
)"

# Parse sections
hf=$(echo "$RAW" | awk '/===HF_MODELS===/,/===DATASETS===/' | grep -v '^===' | grep -v '^$')
ds=$(echo "$RAW" | awk '/===DATASETS===/,/===NON_HF_MODELS===/' | grep -v '^===' | grep -v '^$')
nh=$(echo "$RAW" | awk '/===NON_HF_MODELS===/,/===VENVS===/' | grep -v '^===' | grep -v '^$')
venvs=$(echo "$RAW" | awk '/===VENVS===/,/===SYSTEM_PY===/' | grep -v '^===' | grep -v '^$')
syspy=$(echo "$RAW" | awk '/===SYSTEM_PY===/{flag=1; next} flag' | grep -v '^$')

count() { local n; n=$(echo "$1" | grep -c . 2>/dev/null); echo "${n:-0}"; }
c_hf=$(count "$hf")
c_ds=$(count "$ds")
c_nh=$(count "$nh")
c_venvs=$(count "$venvs")
c_syspy=$(count "$syspy")

{
  echo "# Shared Resources Inventory ($GPU_HOST)"
  echo ""
  echo "<!-- Auto-generated $TIMESTAMP by refresh_inventory.sh -->"
  echo "<!-- Refresh: bash ~/.claude/skills/maestro/scripts/refresh_inventory.sh -->"
  echo ""
  echo "## MANDATORY CHECK BEFORE ANY ACQUISITION"
  echo ""
  echo "**Before** \`huggingface-cli download\` / \`wget\` model / \`pip install\` heavy ML pkg / \`python -m venv\`:"
  echo ""
  echo "1. \`grep -i <keyword>\` against this file."
  echo "2. Miss? \`ssh $GPU_HOST 'ls $R_MODELS/huggingface/hub | grep -i <name>'\` (fuzzy)."
  echo "3. Still miss? OK to acquire — then refresh: \`bash ~/.claude/skills/maestro/scripts/refresh_inventory.sh\`."
  echo ""
  echo "Paths on $GPU_HOST (configure via MODELS_DIR / DATA_DIR / ENVS_DIR / REMOTE_ROOT):"
  echo "- Models (HF cache): \`$R_MODELS/huggingface/hub/\`"
  echo "- Datasets:          \`$R_DATA/\`"
  echo "- Paper workspace:   \`$R_ROOT/Paper/\`"
  echo ""
  echo "## HuggingFace models ($c_hf)"
  echo ""
  if [ -n "$hf" ]; then
    echo "| Model | Size | Modified |"
    echo "|---|---|---|"
    echo "$hf" | awk -F'|' '{printf "| `%s` | %s | %s |\n", $1, $2, $3}'
  else
    echo "(none / shared model dir not accessible)"
  fi
  echo ""
  echo "## Datasets ($c_ds)"
  echo ""
  if [ -n "$ds" ]; then
    echo "| Dataset | Size | Modified |"
    echo "|---|---|---|"
    echo "$ds" | awk -F'|' '{printf "| `%s` | %s | %s |\n", $1, $2, $3}'
  else
    echo "(none)"
  fi
  echo ""
  if [ -n "$nh" ]; then
    echo "## Non-HF models ($c_nh)"
    echo ""
    echo "$nh" | awk -F'|' '{printf "- `%s` (%s)\n", $1, $2}'
    echo ""
  fi
  echo "## Python venvs ($c_venvs)"
  echo ""
  if [ -n "$venvs" ]; then
    echo "Activate via: \`ssh $GPU_HOST \"source ~/miniforge3/etc/profile.d/conda.sh && conda activate <env-path> && python -m ...\"\`"
    echo "(NOT \`source <env>/bin/activate\` -- mamba -p envs don't ship that script)"
    echo ""
    echo "| Path | Python | Key ML packages |"
    echo "|---|---|---|"
    echo "$venvs" | awk -F'|' '{printf "| `%s` | %s | %s |\n", $1, $2, $3}'
  else
    echo "**None discovered.** Conda convention (mandatory on a multi-user server):"
    echo ""
    echo "- **Team-shared envs:** \`$R_ENVS/<purpose>/\` (e.g. \`vllm-<ver>-<model>\`, \`torch-<ver>-<cuda>\`)"
    echo "  - Use for stable, reusable stacks; anyone can activate them"
    echo "- **Per-user / per-paper envs:** \`~/miniforge3/envs/<paper>-<purpose>/\`"
    echo "  - Use for experimental / ephemeral envs"
    echo "- **NEVER** use \`python -m venv\` on this server. Use conda for full isolation (CUDA runtime, MKL, etc.) — venv on a shared GPU server breaks cross-user reproducibility."
    echo "- After creating, immediately run \`bash refresh_inventory.sh\` so future sessions see it."
    echo ""
    echo "**If conda is not yet installed:** install miniforge3 to \`~/miniforge3/\`, then \`source ~/miniforge3/etc/profile.d/conda.sh\`."
  fi
  echo ""
  echo "## System Python ML packages ($c_syspy interpreters)"
  echo ""
  if [ -n "$syspy" ]; then
    echo "Use via \`ssh $GPU_HOST '<pybin> ...'\` — only when no venv has the package."
    echo ""
    echo "| Binary | Version | Key ML packages |"
    echo "|---|---|---|"
    echo "$syspy" | awk -F'|' '{printf "| `%s` | %s | %s |\n", $1, $2, $3}'
  else
    echo "(no probe results)"
  fi
} > "$TMP"

mv "$TMP" "$INVENTORY"
echo "[$TIMESTAMP] inventory: $INVENTORY"
echo "  HF=$c_hf  datasets=$c_ds  non-HF=$c_nh  venvs=$c_venvs  syspy=$c_syspy"
