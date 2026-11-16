# SHARED PROTOCOL & GOVERNANCE (authoritative for every agent) — v1.0

Package root: `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION/` (called `PKG`).
Repository under review: `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/` (called `REPO`), git HEAD `3425693b432bb774b10db1cf3185eae1a7eef095`
(branch `remediation/sbg-v4`, tree contains 4 untracked v8-dev files + untracked `paper/`, `reports/sprint2/`).
Prior in-repo audit material (READ for orientation, do NOT trust as evidence — re-verify): `../SBG_CURRENT_STATE_FORENSIC_AUDIT_2026-11-04.md`,
`REPO/artifacts/paper_evidence/*`, `REPO/paper/*`, `../reports`.

## 0. Mission
Decide, with independently verifiable evidence, whether SBG (Software Behavior Genome, V5 fixed weights 0.50 V3 / 0.25 temporal / 0.25 state) has a
novel, reproducible, competitive and statistically defensible contribution for an IEEE Access Research Article. This is an EXECUTION task, not a writing task.
Do NOT draft a manuscript. Do NOT push/publish anything. Report negative findings plainly. Never fabricate numbers or references.

## 1. Hard rules
1. **REPO is READ-ONLY.** Never write, edit, delete, `make`, `git checkout/stash/reset/clean/commit` inside `REPO`. Always run python with
   `PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1`. Anything that may write (test suites, `make`, `consistency_check.py`) must run on a **copy**
   (`git -C REPO archive HEAD | tar -x -C PKG/reproduction/clean_checkout`, plus copy untracked files if needed). A before-hash of the REPO tree is at
   `PKG/logs/sbg_tree_sha256_BEFORE.txt`; the orchestrator re-checks it at the end. Any change = protocol violation.
2. **Python:** canonical interpreter `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python` (CPython 3.13.5, stdlib + pytest only; NO numpy/scipy/sklearn).
   `venvs/py39/bin/python` is 3.9.6 for version-sensitivity tests only. Write pure-stdlib code.
3. **Write only inside your own directories** (see §6). Never overwrite another agent's files. Shared read-only inputs: `PKG/configs/`, `PKG/experiments/common/`, `PKG/results/raw/trace_cache/`.
4. **No leakage / no tuning on held-out data.** Any tunable baseline is fitted/threshold-tuned on V9c-**train** only (V9c-dev may be used for model *selection*); V10-test and V9c-val are scored once per frozen configuration. Report ALL configurations you ran (no cherry-picking). If you try more than one configuration on a held-out set, report the full set and mark it exploratory.
5. **Never hide failures.** Slow/failed/excluded items are logged with reason. Bounded runtimes (use `timeout`, ≤ ~25 min per command; background + poll for longer). CPU budget: ≤ 4 concurrent heavy processes per agent (14 cores shared by 5 agents).
6. **Evidence discipline:** every number in your report cites `EXP-ID`, script path, and output artifact path. Distinguish REPRODUCED (we ran it) / ADAPTED (our implementation of someone else's idea) / PUBLISHED (quoted from literature, different dataset — never a head-to-head claim).
7. **Preserve raw outputs** under `PKG/results/raw/<EXP-ID>/`; derived tables under `PKG/results/processed|tables/<EXP-ID>_*`; logs under `PKG/logs/`.

## 2. Authoritative populations (frozen by EXP-ORCH-005; `PKG/configs/populations/*.json`, sha256 in `SUMMARY.json`)
| name | design | primary pairs | programs | role |
|---|---|---|---|---|
| `v10_test` | V10 withheld | 638 (319 CHANGED / 319 EQUIV matched sets) | 19 | **headline held-out** |
| `v9c_val` | V9c validation | 432 | 11 | **confirmatory held-out #2** |
| `v9c_dev` | V9c dev | 464 | 13 | model selection / exploratory |
| `v9c_train` | V9c train | 1650 | 46 | fit weights, models, thresholds (ONLY place to fit) |

Each row: `pair_id, base_id, label (1=CHANGED), group (matched-set id), edit (edit-size = repo `_edit_size`), transformation_type, sc_type, sp_type, base_path, variant_path` (paths relative to REPO), `scores` (frozen SBG V5 / V3 / temporal / state, exec-statistics, static_token, static_ast, [sbg_v6, sbg_state_v6 for v10]). `primary` = `in_primary_population` (matched-complete: both members of the set valid & evaluated). Load with `eval_lib.load_population(name)`.
Label = CHANGED means "output/exception/stdout/argument-mutation differs on the protocol's 11 synthesised inputs" (oracle-validated for V10; static-observability-audited for V9c). It is NOT general semantic (non-)equivalence.
Excluded from the primary population but kept in `rows`: unevaluated pairs (3 non-terminating in V10), unmatched sets.

## 3. Shared raw traces (EXP-ORCH-001..004)
`PKG/results/raw/trace_cache/<design>_<split>/<base_id>/<sha1(path)[:12]>__<variant_stem>.json.gz` (`design_split` ∈ `v10_test`, `v9c_val`, `v9c_train`, `v9c_dev`), plus `pairs_scores.json` (SBG scores recomputed by the frozen extraction → replication check vs frozen scored files) and a `DONE` marker per program. Produced by `experiments/common/dump_traces.py` (frozen SBG extraction, protocol `output_free_v8`: structural entry policy, 11 synthesised inputs, 5 runs, max 5000 events, 1 s/trace, ≤2 timeouts). Record schema (gzip JSON): `{path, ok, failure_kind, entry_function, stats, sandbox:{n_runs, run_digests, traces:[{input, ret (repr ≤1500), ret_type, exc, stdout, ms, cov:[lines], trunc, events:[[type1char(c/r/e/l), function, lineno, locals_snapshot_or_null]]}]}}`. Only run 0 is stored in full; `run_digests` shows determinism across the 5 runs. Return values ARE stored — SBG itself is forbidden to read them (SAFEGUARD-2), but competitor baselines that are *defined* on outputs (e.g. Kessel & Atkinson-style output comparison, differential testing) may use them; such baselines MUST be labelled "output-reading (privileged)" vs "output-free". Base-program file ↔ variant mapping: `path` field equals `base_path`/`variant_path` in the population rows. Check `DONE` exists before reading a program directory. The dump jobs run in the background (log: `PKG/logs/EXP-ORCH-00{1..4}_*.log`); poll for `DONE` files.

## 4. Metrics & statistics (identical for every method)
`experiments/common/eval_lib.py` (pure stdlib; already verified to reproduce V10 SBG V5 AUROC 0.8968 [0.8629, 0.9216] and V9c-val 0.7514 [0.7063, 0.7936]):
tie-aware AUROC; AUPRC (tie-aware average precision, prevalence 0.5); precision/recall/F1/FPR at a Youden threshold chosen on **V9c-train scores of the same predictor** and applied unchanged; 95 % CI = program-cluster bootstrap (B=2000, seed 42, percentile); paired ΔAUROC with same resamples (two-sided bootstrap p); one-sided cluster permutation p (labels permuted within program); Holm correction over the declared family; matched-set concordance; exact-edit-size stratified AUROC; edit-size quantile strata. Cluster = base program (≈19 independent units for V10 — cluster-level inference is the only valid inference; pair-level CIs are anti-conservative).
Effect sizes: ΔAUROC with CI; also report concordance-based `A12`-style effect (AUROC itself) and Cliff's δ = 2·AUROC−1 where helpful.
Runtime/peak memory: measure per-pair scoring cost for each method (wall seconds via `time.perf_counter`; peak RSS via `resource.getrusage(RUSAGE_SELF).ru_maxrss` — macOS reports bytes) in a clean subprocess; report extraction cost separately from scoring cost.

## 5. Experiment registry (central, append-only, one file per agent to avoid write races)
Each agent appends JSON lines to `PKG/logs/registry/<AGENT>.jsonl` (`AGENT` ∈ `A1_lit, A2_repo, A3_stats, A4_bench, A5_ablate, A6_review`). Experiment IDs: `EXP-<AGENT-letter+number>-<NNN>` e.g. `EXP-A4-007`. Fields:
`{"id","agent","title","status":"COMPLETED|FAILED|BLOCKED|PARTIAL|RUNNING","repo_commit","dataset(s)+sha256 (populations SUMMARY.json shas)","config","command","runtime_s","outputs":[paths],"errors_exclusions":"...","notes"}`.
One protocol per experiment name: if you change the protocol, mint a new ID. Orchestrator IDs: `EXP-ORCH-001..004` (trace dumps v10_test, v9c_val, v9c_train, v9c_dev), `EXP-ORCH-005` (populations), `EXP-ORCH-006` (final REPO-unchanged check).

## 6. Directory ownership (write ONLY here)
| Agent | Owns |
|---|---|
| A1 literature | `PKG/03_COMPETITOR_LANDSCAPE_AND_NOVELTY.md`, `PKG/results/raw/literature/` |
| A2 repo/repro | `PKG/01_…FORENSIC_AUDIT.md`, `PKG/09_…ARTIFACT_FREEZE_AUDIT.md`, `PKG/reproduction/`, `PKG/results/raw/repro/` |
| A3 stats | `PKG/07_EXPERIMENTAL_INTEGRITY_AUDIT.md`, `PKG/experiments/statistical_verification/`, `PKG/results/*/EXP-A3-*` |
| A4 bench | `PKG/04_…PLAN.md`, `PKG/05_…RESULTS.md`, `PKG/06_…REPRODUCTION.md`, `PKG/experiments/competitor_baselines/`, `PKG/results/*/EXP-A4-*` |
| A5 ablation/external | `PKG/08_….md`, `PKG/experiments/ablations/`, `PKG/experiments/external_validation/`, `PKG/results/*/EXP-A5-*` |
| A6 reviewer | `PKG/10_ADVERSARIAL_REVIEWER_2_REPORT.md`, `PKG/results/raw/review/` |
| Orchestrator | `PKG/00,02,11,12 *.md`, `PKG/configs/`, `PKG/experiments/common/`, `PKG/logs/` (except registry files), `PKG/results/figures` |

## 7. Report requirements
Each report: (1) summary of verdict first; (2) evidence table with EXP-IDs; (3) an explicit "what failed / what could not be done / exact continuation command" section; (4) "claims supported / unsupported / contradicted" where relevant. Keep reports factual and compact (tables > prose). Never mark a planned experiment as done.
