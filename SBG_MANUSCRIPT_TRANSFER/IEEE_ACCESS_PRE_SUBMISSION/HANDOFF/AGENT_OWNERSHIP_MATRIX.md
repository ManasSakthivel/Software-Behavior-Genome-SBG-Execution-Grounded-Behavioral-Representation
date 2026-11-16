# AGENT OWNERSHIP MATRIX (file/experiment ownership boundaries; no two owners per path)

Package root `PKG` = `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION`.

| Work package (new Bob session) | Owns (write only here) | Reads (read-only) | Must wait for |
|---|---|---|---|
| **WP-A** A4 recovery + competitor implementation (A4R + A4B) | `EXPERIMENT_RECOVERY_AND_REGISTRY.md`, `logs/registry/INDEX.md`, `logs/registry/A4R.jsonl`, `A4B.jsonl`, `experiments/competitor_baselines/recovery/`, `…/competitors_new/`, `results/raw/EXP-A4R-*`, `EXP-A4B-*` | predecessor modules, trace caches, populations, `03`, `EARLY_COMPETITOR_BRIEF.md` | nothing (start immediately — but see CONFLICT RULE) |
| **WP-B** A4 benchmark execution + independent stats (A4C + A4D) | `experiments/competitor_baselines/run/`, `05_*`, `06_*`, `results/*/EXP-A4C-*`, `experiments/statistical_verification/a4d/`, `05b_*`, `results/*/EXP-A4D-*`, registries `A4C.jsonl`, `A4D.jsonl` | WP-A outputs, populations | WP-A `.READY` + `VERIFIED_BASELINES.json` before running new competitors on held-out data |
| **WP-C** A5 ablations + return-value (A5E + A5F) | `experiments/ablations/` (+`return_value/`), `08a_*`, `08b_*`, `results/*/EXP-A5E-*`, `EXP-A5F-*`, registries `A5E.jsonl`,`A5F.jsonl` | trace caches, SBG source (import read-only) | nothing |
| **WP-D** A5 external validation (A5G) | `experiments/external_validation/`, `08c_*`, `results/*/EXP-A5G-*`, registry `A5G.jsonl` | `SBG/external/*`, frozen external scored files, A2 raw version-sensitivity outputs in `results/raw/repro/` | nothing |
| **WP-E** Artifact integrity + reproducibility (AI) | `reproduction/final/`, `ARTIFACT_MANIFEST_FINAL.md`, `results/raw/EXP-AI-*`, registry `AI.jsonl` | everything | final re-hash must run LAST (after all other WPs); `math_gray_code` investigation can start now |
| **WP-F** A6 review + positioning (A6 + AJ) | `10_*`, `02_*`, `11_*`, `results/raw/review/`, registries `A6.jsonl`,`AJ.jsonl` | all reports | final A6/AJ update must wait for WP-A/B/C/D evidence; first-pass review of existing evidence can start now |
| Orchestrator (last session) | `00_*`, `12_*`, merged `08_*`, `HANDOFF/*`, `configs/`, `experiments/common/` | everything | WP-A…F |

## Files that must NOT be modified concurrently
* `SBG/` (entire repo; read-only; never `make`, never write)
* `configs/PROTOCOL.md`, `configs/PROTOCOL_ADDENDUM_v1.1.md`, `configs/populations/*.json` (frozen, shas in `SUMMARY.json`)
* `experiments/common/{eval_lib,dump_traces,make_populations}.py`
* `results/raw/trace_cache/**` (shared, read-only)
* `04_HEAD_TO_HEAD_BENCHMARK_PLAN.md` (pre-registration: only dated AMENDMENT appends)
* `results/raw/EXP-A4-002..004` (predecessor partial outputs; preserve)
* `results/raw/EXP-A4C-002/frozen_config.json` (A4C freeze)

## CONFLICT RULE (critical)
**A4R, A4B, A4C, A4D appear to be still running in the originating session** (see CURRENT_EXECUTION_STATUS.md). Before a new session starts WP-A or WP-B it must run the liveness check (MASTER_HANDOFF_PROMPT §7). If files in that agent's owned paths changed within the last 10 minutes, DO NOT start that work package — wait or poll. Never start two sessions on one package.
