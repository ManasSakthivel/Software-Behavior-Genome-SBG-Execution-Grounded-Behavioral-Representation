# MASTER HANDOFF PROMPT — SBG IEEE Access Pre-Submission Validation

Paste this file (plus the one `NEXT_SESSION_ASSIGNMENTS.md` section for your work package) at the start of a new Bob session.
Written 2026-11-14 ~20:30 IST. Nothing in this file claims completion beyond what the evidence files named in `COMPLETED_WORK.md` show.

## 0. Mission
Decide, from independently verifiable evidence, whether SBG is ready for IEEE Access. This is an execution assignment, not paper drafting.
Final output: GO / CONDITIONAL GO / NO-GO plus a 7-gate scorecard (PASS / CONDITIONAL / BLOCKED).
Do NOT draft the manuscript. Do NOT claim superiority from published numbers on other datasets, real-bug detection, or cross-language generality.

## 1. Paths and interpreter
- Workspace: `/Users/manassakthivel/Desktop/SBG-FINALREVIEW`
- SBG repo (READ-ONLY): `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/` (branch `remediation/sbg-v4`, HEAD `3425693b432bb774b10db1cf3185eae1a7eef095`). The workspace root is NOT a git repo.
- `PKG` = `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION`
- Canonical Python (3.13.5, stdlib + pytest, no numpy): `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python`
- Other interpreters (version-sensitivity only): `venvs/py39` (3.9.6), `/opt/homebrew/bin/python3.11`, `/opt/homebrew/bin/python3.14`. Results reproduce bit-identically only on 3.13.x.
- Machine: 14 cores. Keep at most ~4 heavy processes at once.

## 2. Environment variables (always)
```
export PYTHONHASHSEED=0
export PYTHONDONTWRITEBYTECODE=1
PY=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python
PKG=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION
```
Frozen tracer protocol `output_free_v8`: 11 synthesised inputs, 5 runs, max 5000 events, 1 s/trace, <=2 timeouts.

## 3. Read-only repo rule
- Never write under `SBG/`. Never run `make`, `git checkout|stash|reset|commit|push|clean`, or anything that regenerates `SBG/artifacts`.
- Pytest only with `-p no:cacheprovider` and `PYTHONDONTWRITEBYTECODE=1`; run on a COPY if in doubt.
- Run `find SBG -type f` re-hash at the end (EXP-ORCH-006) and diff against `PKG/logs/sbg_tree_sha256_BEFORE.txt` (16,137 files).

## 4. Frozen source hashes (SHA-256)
| File (under `SBG/`) | Hash |
|---|---|
| `benchmark/datasets/v10_independent/pairs_test.jsonl` | `476c3efffcf4a20c9cf92212b932b03b29c64ca8e505742710a0da7555d53735` |
| `artifacts/final/FREEZE_V10.json` | `77e95252e9d27e3910c06c3b686c659ff7b8f70b3c03a8b6eda0f9fed0f55c3a` |
| `artifacts/final/FREEZE_V9.json` | `19d4460ace0384e8892287075a9108d201a40d1c602a7f2f38ae972638968c8a` |
| `artifacts/final/pairs_v10_test_v6exp.jsonl` | `292233fe70000b8f60326da2e2a22b9a0613caa95d5cd5c186ee9e3f01e2d146` |
| `artifacts/final/V10_MODELS_FROZEN.json` | `fe637cbddd0236086e964f7c2b609ad4c6c0af72322733dfecd8cada287f7e76` |
| `artifacts/final/V9_MODELS_FROZEN.json` | `010394dadc91c47ac53e9741a0faf5144c1bb33df34c5d21752e97cb22438cc8` |
| `experiments/final/extraction.py` | `549d5cf29acb807e9b984e40c424f730744ab01d2642bd7fc2d24008f1835f55` |
| `sbg/v5/distance_v5.py` | `e7419d2bbc905e7f6cdeedc1d55d633dab15a5816743a29fe86b211aa0308ac9` |

Population files (`PKG/configs/populations/`): `v10_test` ba307a2f…c35d, `v9c_train` 3f252a9a…c8e, `v9c_dev` 4b8ff238…6fe4, `v9c_val` 5e2e2e1a…a8a (full hashes in `SUMMARY.json`; verify with `shasum -a 256`).
Full-length hashes:
- v10_test `ba307a2f2f865dd048315a4f5bf874a15d7ad610422ad71d4b81b4737101c35d`
- v9c_train `3f252a9ad96bd620d81434f8aec94f4538124ecd76b92167a4a835ade54ce83a`
- v9c_dev `4b8ff238566567b97824074472fa94e19189cbb55c3d56109d013809ff1c6fe4`
- v9c_val `5e2e2e1ab3546a7271cf0f9bdeba1779ff090ca217f3e5764a862656b1310a8e`

## 5. Datasets, caches, governance
- Governance (orchestrator-owned): `PKG/configs/PROTOCOL.md`, `PROTOCOL_ADDENDUM_v1.1.md` (addendum wins), `PKG/configs/populations/*.json`.
- Shared common code (do not edit): `PKG/experiments/common/{dump_traces,make_populations,eval_lib}.py`.
- Trace caches (read-only): `PKG/results/raw/trace_cache/{v10_test 19/19, v9c_val 11/11, v9c_dev 13/13, v9c_train 45/46}`. `math_gray_code` (v9c_train) failed rc=-9 after 1057 s; uninvestigated (WP-E).
- Splits: tune ONLY on v9c_train / v9c_dev. v9c_val and v10_test are scored once per frozen configuration. Log every exclusion.
- Sizes: V10 638 pairs / 19 programs; V9c-val 432 / 11; V9c-dev 464 / 13; V9c-train 1650 / 46.
- Known label defect: V9c-val has 16/216 EQUIVALENT pairs changing output and 67/216 CHANGED pairs unobservable. V10 labels are clean.
- Label tautology: any output-reading baseline on the protocol's own 11 inputs reproduces labels by construction — report only as a label-oracle ceiling; fair competitors need an independent input battery.

## 6. Experiment IDs
Registry snapshot: `HANDOFF/EXPERIMENT_REGISTRY_SNAPSHOT.md`. Live registries: `PKG/logs/registry/{A1_lit,A2_repo,A3_stats}.jsonl` (A4R/A4B/A4C/A4D registries are MISSING — a continuing session must create them from the raw dirs).
- ORCH: EXP-ORCH-001..004 (trace caches, done); EXP-ORCH-006 (final tree re-hash, NOT started).
- A1: literature (done). A2: repo/repro (done). A3: `EXP-A3-*` (done).
- A4 predecessor (partial, cancelled): `results/raw/EXP-A4-002/003/004`.
- A4B: `results/raw/EXP-A4B-001`. A4C: `EXP-A4C-001..005` (frozen config `EXP-A4C-002/frozen_config.json`, dev-only predictions). A4D: `EXP-A4D-002..005` (005 running when last checked).
- A5E / A5F / A5G / A6 / AJ: not started.

## 7. Liveness check (RUN FIRST)
```
cd $PKG
date
find . -type f -newermt "-10 min" -not -path "./HANDOFF/*" -not -name "*.pyc" | sort | head -50
ps aux | grep -i "[p]ython" | grep -v "grep" | awk '{print $2, $3"%CPU", $4"%MEM", $11, $12, $13, $14}'
ls -la --time-style=full-iso results/raw/EXP-A4C-* results/raw/EXP-A4D-* 2>/dev/null | tail -40
```
Interpretation:
- Any file under `experiments/competitor_baselines/{recovery,run,competitors_new}`, `results/raw/EXP-A4{B,C,D}-*`, or `experiments/statistical_verification/a4d/` modified in the last 10 min, OR a python process referencing those paths → originating A4R/A4B/A4C/A4D agents are STILL ACTIVE. Do NOT start WP-A/WP-B; do WP-C/D/E/F only; re-poll in 10 min.
- No writes for >10 min AND no such process → they are quiet; WP-A/WP-B may take over (read their last files first; never restart completed runs).
- Note: `spawn_subagent` often reports "cancelled" even though the agent ran. Trust mtimes and `ps`, not the tool message.
- Last observed state at 20:29 IST: writes in `run/`, `competitors_new/`, `recovery/` within the previous 10 min → ACTIVE.

## 8. Files that must NOT be modified concurrently
- `PKG/04_HEAD_TO_HEAD_BENCHMARK_PLAN.md` (frozen pre-registration; only dated amendments appended, by the A4 owner).
- `PKG/configs/**`, `PKG/experiments/common/**`.
- `PKG/results/raw/EXP-A4*/frozen_config.json` and everything in existing `results/raw/EXP-*` dirs (append new IDs, never overwrite).
- `PKG/experiments/competitor_baselines/**` and `experiments/statistical_verification/a4d/**` while the liveness check says active.
- Finished reports `01`, `03`, `07`, `09` (amend via a dated "Errata" section only).
- `PKG/logs/sbg_tree_sha256_BEFORE.txt`, `PKG/logs/git_status_before.txt`.
- Each work package writes only into its own directory (`experiments/ablations/`, `experiments/external_validation/`, etc.) and its own `results/raw/EXP-<agent>-NNN/`.

## 9. Exact resume commands
Environment:
```
export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1
PY=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python
PKG=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION
cd $PKG
```
Sanity: verify eval_lib still reproduces the headline numbers (V10 V5 AUROC 0.8968 [0.8629, 0.9216]; V9c-val 0.7514 [0.7063, 0.7936]); entry points are in `experiments/common/eval_lib.py` and the A3 scripts in `experiments/statistical_verification/`.
Reproduction of A2 results: `bash reproduction/run_repro.sh` (see `reproduction/REPRODUCE.md`).
Trace-cache regeneration (only if a cache is missing; one program): see `experiments/common/dump_traces.py --help`. For `math_gray_code`, run it ALONE with a hard external timeout (e.g. `timeout 600`), background via `execute_command background:true`, log to `PKG/logs/EXP-E-<n>_math_gray_code.log`.
A4 resume (only after §7 says quiet): read `HANDOFF/NEXT_SESSION_ASSIGNMENTS.md` WP-A/WP-B; frozen config is `results/raw/EXP-A4C-002/frozen_config.json`; runners are `experiments/competitor_baselines/run/{run_all,run_competitors,eval_all}.py`. Do not score v9c_val or v10_test before the frozen config is confirmed and the plan amendment is appended.
Background jobs: use `execute_command` with `background: true` (plain `nohup … &` dies with the shell).
Tests: `$PY -m pytest -p no:cacheprovider -q` run from a COPY of `SBG/` (baseline: 807 passed, 3 warnings on 3.13.5).

## 10. Still-open deliverables
`00_EXECUTIVE_SUMMARY`, `02_SCIENTIFIC_CONTRIBUTION_AND_POSITIONING`, `05_COMPARATIVE_EVALUATION_RESULTS`, `06_COMPARATIVE_BENCHMARK_REPRODUCTION`, `08_ROBUSTNESS_ABLATION_AND_EXTERNAL_VALIDATION`, `10_ADVERSARIAL_REVIEWER_2_REPORT`, `11_IEEE_ACCESS_SUBMISSION_READINESS`, `12_FINAL_GO_NO_GO_DECISION`, `EXPERIMENT_RECOVERY_AND_REGISTRY.md`, `ARTIFACT_MANIFEST_FINAL.md`, final 15-point report.
Provisional gate reading (NOT final): integrity near-PASS; reproducibility CONDITIONAL; novelty CONDITIONAL/weak; comparative benchmarking BLOCKED; robustness/external BLOCKED; contribution and IEEE readiness pending. Evidence favours a methodology + null-result positioning (H4 inconclusive; BugsInPy/QuixBugs AUROC at or below chance).

## 11. Integrity rules (carry forward verbatim)
No fabricated data or references; no label edits; no threshold selection on held-out data; no hiding negative findings; no silent architecture changes (a revised representation = a new experiment, never reported with old results); approximations labelled as approximations; never present planned work as done; every number must trace to a file.
