# PROTOCOL ADDENDUM v1.1 (resume phase) — read AFTER configs/PROTOCOL.md; where they conflict, THIS file wins.

## Agents in the resume phase (registry file `PKG/logs/registry/<ID>.jsonl`; experiment ids `EXP-<ID>-NNN`)
| ID | Role | Owns (write ONLY here) |
|---|---|---|
| A4R | A4 recovery/audit of predecessor baselines + authoritative registry | `PKG/EXPERIMENT_RECOVERY_AND_REGISTRY.md`, `PKG/logs/registry/INDEX.md`, `PKG/experiments/competitor_baselines/recovery/`, `PKG/results/raw/EXP-A4R-*` |
| A4B | A4 new competitor implementations | `PKG/experiments/competitor_baselines/competitors_new/`, `PKG/results/raw/EXP-A4B-*` |
| A4C | A4 benchmark execution + `05_…`, `06_…` | `PKG/experiments/competitor_baselines/run/`, `PKG/05_*.md`, `PKG/06_*.md`, `PKG/results/{raw,processed,tables,figures}/EXP-A4C-*` |
| A4D | A4 independent statistical verification (must NOT import A4's metric code; may use `experiments/common/eval_lib.py` only as a cross-check, primary = own code) | `PKG/experiments/statistical_verification/a4d/`, `PKG/05b_A4_INDEPENDENT_STATISTICAL_VERIFICATION.md`, `PKG/results/*/EXP-A4D-*` |
| A5E | component ablation + state-genome dominance + leakage test | `PKG/experiments/ablations/`, `PKG/results/*/EXP-A5E-*`, `PKG/08a_ABLATION_REPORT.md` |
| A5F | SC-6 / return-value / architectural analysis (modified-SBG experiments kept separate) | `PKG/experiments/ablations/return_value/`, `PKG/results/*/EXP-A5F-*`, `PKG/08b_RETURN_VALUE_REPORT.md` |
| A5G | external validation (+ version/event-cap/timeout sensitivity) | `PKG/experiments/external_validation/`, `PKG/results/*/EXP-A5G-*`, `PKG/08c_EXTERNAL_VALIDATION_REPORT.md` |
| A6 | adversarial reviewer | `PKG/10_ADVERSARIAL_REVIEWER_2_REPORT.md`, `PKG/results/raw/review/` |
| AI | artifact integrity / reproducibility, math_gray_code root cause, Makefile safety, EXP-ORCH-006 | `PKG/reproduction/final/`, `PKG/results/raw/EXP-AI-*`, `PKG/ARTIFACT_MANIFEST_FINAL.md` |
| AJ | scientific positioning (02) and readiness (11) | `PKG/02_*.md`, `PKG/11_*.md` |
Lead orchestrator writes `00`, `12`, merges `08a/08b/08c` into `08_ROBUSTNESS_ABLATION_AND_EXTERNAL_VALIDATION.md`, and writes the final report. Nobody else writes those.

## Provenance classes (A4R assigns; only VERIFIED COMPLETE may be cited as final evidence)
VERIFIED COMPLETE · PARTIALLY COMPLETE · INTERRUPTED · INVALID · UNKNOWN PROVENANCE (⇒ reproduce from frozen code+config under a NEW id).

## Hand-off file convention (agents run in parallel; poll, don't wait idle)
* A4R publishes `PKG/results/raw/EXP-A4R-001/VERIFIED_BASELINES.json` (list of baseline modules + status + known bugs). A4B/A4C poll it for ≤10 min, then start with what is verified; never run an UNVERIFIED module on held-out data.
* A4B publishes each finished competitor as `PKG/experiments/competitor_baselines/competitors_new/<name>.py` + `<name>.READY` (a JSON stating class A/B/C/D, faithful vs adapted, unit-test result). A4C polls for `.READY`.
* A4C writes per-method predictions to `PKG/results/raw/EXP-A4C-*/predictions/<population>/<method>.json` as `{pair_id, base_id, label, group, score}` rows plus `meta.json` (config, code sha256, train-threshold). A4D reads ONLY those prediction files + population files; it publishes `…/A4D_READY` when verification is complete.
* A5E/A5F/A5G publish `…/<AGENT>_DONE` marker files.

## Resource rules (14 cores shared by ≤9 concurrent agents)
≤3 heavy processes per agent (global cap ≈ 12). Every subprocess bounded: wall timeout; monitor RSS (`ps -o rss`) and kill a process > 6 GB. Previous failure: `math_gray_code` (v9c_train trace dump) died with rc=-9 after 1057 s — AI investigates; others must not re-run it. Estimate runtime before launching anything > 10 min. Write checkpoints/partial results after each unit of work.

## Integrity reminders
* REPO read-only; run python with `PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1`; use `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python`.
* Held-out sets (v10_test, v9c_val) are scored ONCE per frozen configuration. Anything computed after seeing held-out numbers is EXPLORATORY and labelled so. Modified-SBG variants are never reported as evidence for original SBG; the V10 set is "burned" for any variant designed after seeing V10.
* Never silently exclude programs/pairs: log with reason. Never present planned work as done.
* Every report states: what was executed (EXP ids), what failed, what is BLOCKED (+ continuation command).
