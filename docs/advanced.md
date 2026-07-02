# Tier 3 — Multi-machine GPU orchestration (reference deployment)

This is how our lab runs EAIR across machines. Nothing in Tiers 1–2 requires
any of this; treat it as a pattern to adapt, not a requirement.

## Topology

```
control host (CPU-only, runs Claude Code + the conductor)
    │  ssh / rsync
    ▼
gpu-host (training & inference only; no agent runtime)
```

Two principles drive the split:

1. **The conductor never leaves the control host.** All Read/Write/Edit and
   agent dispatch happen locally. The only channel to the GPU side is
   `ssh gpu-host "..."` plus `rsync` for code.
2. **Heavy data never comes back.** Datasets and checkpoints live on the GPU
   host. Only small result JSONs are rsynced back for the Verifier to read.

This also covers the case where your GPU host has restricted or unreliable
egress (common in institutional clusters): LLM/API calls all happen on the
control host, so the GPU side needs no external connectivity.

## Setup

1. Configure `~/.ssh/config` on the control host:

   ```
   Host gpu-host
     HostName <ip-or-name>
     User <you>
   ```

   Passwordless key auth is required (agents run non-interactively).

2. Set the path variables in `.env` (see `.env.example`):
   `REMOTE_ROOT` (workspace on the GPU host), `MODELS_DIR`,
   `DATA_DIR`, `ENVS_DIR` (shared resource mounts, if your
   cluster has them).

3. Shared-resource discipline (multi-user clusters): before any model or
   dataset download, agents check the shared inventory
   (`skills/maestro/scripts/refresh_inventory.sh`) — re-downloading a 60GB
   model that already sits on a shared mount is exactly the waste this
   prevents. Use conda environments, not venv, on shared machines.

## The standard GPU-task pattern

```bash
# 1. prepare code locally, then sync
rsync -avz ./myproj/ gpu-host:$REMOTE_ROOT/myproj/

# 2. launch inside tmux so the run survives disconnects
ssh gpu-host "tmux new -d -s exp001 'bash -lc \"cd $REMOTE_ROOT/myproj && \
  source ~/miniforge3/etc/profile.d/conda.sh && conda activate <env> && \
  python train.py > run.log 2>&1; echo EXIT=\$? >> run.log\"'"

# 3. monitor without logging in
ssh gpu-host "tail -5 $REMOTE_ROOT/myproj/run.log"
ssh gpu-host nvidia-smi

# 4. bring back ONLY the small results
rsync -avz gpu-host:$REMOTE_ROOT/myproj/results.json ./myproj/
```

Notes from production:

- Always end launch commands with `echo EXIT=$? >> run.log` — the Runner
  agent checks exit codes, not log tails.
- Multi-turn inference: budget `max_model_len ≥ 4×` the single-step maximum
  token count. (Incident: a 5-step pipeline passed at steps 1–2 and failed
  100% of samples at steps 3–5 because the length budget assumed one step.)
- Archive with `tar.gz`, not zip — zip's missing EOCD on truncated transfers
  has silently corrupted archives for us twice.
- If you power-limit GPUs (thermal/noise), expect roughly proportional
  throughput loss and re-estimate runtimes before preregistering deadlines.

## Optional: heartbeat automation

Our internal deployment adds a user-managed heartbeat (a tmux script that
pings the conductor every N minutes to check gates and dispatch queued
work). It is deliberately not shipped in v1; the conductor works fine
interactively. If you build one, keep it user-managed — the conductor must
never start or restart its own heartbeat (that is a hard rule).
