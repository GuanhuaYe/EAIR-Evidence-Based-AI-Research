# SIGMOD Artifact Evaluation submission template

Separate AE submission after main paper acceptance. Aims for one or
more badges: Available / Functional / Reusable / Reproduced / Replicated.

## Submission package

### README (required)

- One-paragraph summary of the artifact
- Paper title, authors, paper DOI/URL
- Reproducibility scope: which experiments are reproducible
- Hardware / OS requirements (CPU model, RAM, disk, GPU model if any)
- Software dependencies (versions pinned)
- Estimated total runtime to reproduce all paper results
- Sanity-check run (≤10 min) with expected output

### Build / install

- Docker image OR VM image OR step-by-step bash
- All dependencies declared, version-pinned
- No network access required AFTER initial install (if possible)
- If network required, document why and provide cached fallback

### Data

- Datasets included (if license permits) OR fetch script
- Total dataset size declared
- Data preprocessing scripts included
- Expected preprocessed data hash / checksum

### Run

- One script per paper table / figure: `repro_table_N.sh`,
  `repro_figure_N.sh`
- Expected runtime per script (be honest)
- Expected output format
- Mapping table: paper claim → script → expected number ± tolerance

### Verify

- Tolerance: numbers within ±X% match the paper
- Bit-exact reproduction NOT required for stochastic experiments,
  but the tolerance must be declared up front
- For non-stochastic experiments, bit-exact reproduction expected

## Badges and what they require

| Badge | Requirement |
|---|---|
| Artifacts Available | Public DOI / URL with permanent identifier |
| Artifacts Evaluated — Functional | Reviewer can build + run + reproduce a smoke test |
| Artifacts Evaluated — Reusable | Reviewer can run on a new (related) input |
| Results Reproduced | Reviewer reproduces full paper claims with the artifact |
| Results Replicated | Independent re-implementation matches |

## Author response

After reviewers run the artifact, AE asks for an author response on
any reproducibility gap. Tone: same discipline as
`rebuttal-drafter` — concede, refute, evidence.

## Common AE failure modes (avoid)

- Network access required mid-run (download from S3 / GitHub during
  experiment)
- "Works on my machine" CUDA / Python version mismatch
- Total runtime > AE reviewer budget (typically 2-3 days)
- A smoke test that does not actually test anything (passes without
  exercising the core method)
- Random seeds not set, so results drift between runs
- Hidden assumptions: undocumented env vars, undocumented input files
