# Engineer Knowledge Base (Cross-Project)

This file is the Engineer agent's persistent memory. It survives across
research projects and conversations. Engineer MUST read this before every
performance review.

---

## 1. Machine Hardware

(Generic reference specs — NOT a specific machine. Replace with your own host's
actual GPU count and layout.)

| GPU | VRAM | Bandwidth | FP16 compute | Notes |
|-----|------|-----------|-------------|-------|
| consumer-24gb | 24GB | baseline | lower | Best for <14GB models; PCIe-only, no fast multi-GPU interconnect |
| datacenter-80gb | 80GB | ~2x consumer | higher | ~2x consumer bandwidth; NVLink-class interconnect for fast multi-GPU; best for large models |

**Key perf differences:**
- The datacenter GPU has ~2x memory bandwidth → memory-bound ops (attention, large batch inference) ~2x faster
- The consumer GPU has better FP16 compute density per watt but less VRAM
- The datacenter GPU has an NVLink-class interconnect — multi-GPU comms fast. The consumer GPU is PCIe-only.
- For the target model (~14GB bf16): fits on the consumer GPU, faster on the datacenter GPU due to bandwidth

**CPU/RAM:** (update when known)
**Disk:** (update when known)

## 2. Known Users & GPU Allocation

(Fill in your lab's allocation. Example format:)

| User | Typical GPUs | Workload | Notes |
|------|-------------|----------|-------|
| user-a | cuda:0 | NLP research | Primary user |
| user-b | cuda:1 | Medical imaging | Long training runs |
| user-c | cuda:2,3 | Multimodal embedding | Multi-GPU training |

**Contention rule:** NEVER kill other users' processes. If your assigned GPUs are busy, wait or use the fallback GPU agreed with the team.

## 3. Optimization Playbook (Accumulated Experience)

(Illustrative entries from a reference project — replace with your own. Run
IDs like `pilot-NNN` / `formal-NNN` below are example labels, not real runs.)

### The target model on the consumer GPU
- **KV-cache reuse for oracle gaps:** Collect KV cache for prefix once, eval each expert with single-position attention. ~2.3s/it → 60x speedup over naive (91s/it). (example run)
- **Per-expert forward pass:** 64 experts × 16 MoE layers, but only eval 4 target layers. Main bottleneck is the expert loop at each target layer.
- **VRAM:** Model ~14GB + KV cache ~56MB + peak activations ~1.5GB = ~16.5GB / 24GB.
- **Batch perplexity:** batch_size=8-16 safe on the consumer GPU for this model.

### General Optimization Patterns
| Problem | Method | Speedup | Risk | First Used |
|---------|--------|---------|------|------------|
| Redundant prefix computation | Cache prefix hidden states per (text, layer) | 2-3x | Zero | formal-001-crr |
| Repeated dataset loading | Pre-load texts once globally | ~10min saved | Zero | formal-001-crr |
| Slow per-token expert eval | KV-cache single-position attention | ~60x | Zero | pilot-005 |
| Bulk LLM inference | vLLM batch inference | 20x+ | Low | (known, not yet applied to MoE) |
| Sequential gamma search | Multi-GPU parallelism | 3-5x | Low | formal-001-crr (identified) |
| Sequential seed eval | Multi-GPU parallelism | 3x | Low | formal-001-crr (identified) |
| Naive HF benchmark eval | vLLM + batching | 5-10x | Low | formal-001-crr Step E (identified) |
| Unconditional on ALL tokens | Skip/approximate small corrections | 1.3x | Low | formal-001-crr (identified) |
| torch.compile | Graph optimization | 1.5-3x | Medium (compatibility) | (not yet tested on target-model) |

### What Didn't Work / Mistakes
- **Example mistake:** an engineer profiled only Step A (1.7s/it, LET_RUN) but ignored a later Step E benchmark eval running naive HuggingFace inference. Step E should have been flagged for vLLM optimization pre-run. **Lesson: MUST profile ALL steps, not just the first/current one.**

## 4. Model Performance Baselines

| Model | GPU | Task | Speed | Notes |
|-------|-----|------|-------|-------|
| target-model | consumer-24gb | Oracle gap collection (KV-cache) | ~1.7s/text | formal-001-crr Step A |
| target-model | consumer-24gb | Perplexity eval | ~2s/batch (bs=8) | Estimate |
| target-model | consumer-24gb | CRR real forward pass eval | ~8-11 tok/s | formal-001-crr Step D |
| target-model | consumer-24gb | Benchmark eval (HF naive) | ~24 min for 7 benchmarks | formal-001-crr Step E |
| target-model | consumer-24gb | Gamma search (5 values, sequential) | 54.5 min | formal-001-crr Step D |
| target-model | consumer-24gb | Condition eval (3 seeds, sequential) | 50.5 min | formal-001-crr Step C/D |
| target-model | datacenter-80gb | Oracle gap collection | ~0.8-1.0s/text | Estimate (2x bandwidth) |

## 5. Update Log

(Append dated entries here as you accumulate experience. Illustrative example:)

- **Example entry:** Full-pipeline profile of a 129-min run. Key findings: (1) 42% time in gamma search (sequential, parallelizable across GPUs), (2) 39% in condition eval (sequential seeds, parallelizable), (3) 19% in benchmarks (naive HF, vLLM could 5-10x). Estimated optimized runtime: ~33 min (3.9x speedup). Anti-patterns: sequential gamma/seed loops, batch_size=1 benchmarks, unconditional correction on ALL tokens.
