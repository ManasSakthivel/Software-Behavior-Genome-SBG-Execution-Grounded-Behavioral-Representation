# 01 — Repository Architecture Map (checkpoint `4a50145`)

Counts are `git ls-files` at the checkpoint; sizes from `du`.

## Top-level layout

| Path | Files | Role |
|---|---|---|
| `sbg/` | 59 | Library. Generations coexist: root `distance.py`/`extraction/` (V1: static + dynamic genomes), `v2/` (execution runner, normaliser, noise floor), `v3/` (dynamic genome V3 + metrics), `v5/` (the V5 representation), `v6/` (experimental state-transition genome, **frozen** by `verify_v6_unchanged.py`), `repair/` |
| `tests/`, `sbg/**/test_*.py` | 18 + in-package | 807 pytest tests (all pass at checkpoint) |
| `benchmark/` | 13,606 (75 MB) | Corpus + datasets: `corpus/base_programs`, `corpus/fresh_programs`, `datasets/{v6,v7,v8,v9_composed,v10_independent,variants}`, `ground_truth`, `splits`, `transformations`, generators in `scripts/` |
| `external/` | 589 | Pinned external corpora: `quixbugs` (50 Python programs + `json_testcases`), `bugsinpy` (55 function units), `quixbugs_java` |
| `experiments/final/` | ~75 scripts | The V5 evaluation pipeline: `protocol.py`, `entry_policy.py`, `class_driver.py`, `extraction.py` (one trace pass → every predictor), `run_main_evaluation.py`, `evaluate_v10.py`, `static_baselines.py`, audits |
| `artifacts/final/` | | Frozen pair-level predictions: `pairs_<split>_output_free_v8.jsonl` (per-pair `scores{}`), freeze manifests (`FREEZE_V8*.json`, `FREEZE_V10*.json`), `THRESHOLD_*`, `STANFORD_GATE.json` |
| `artifacts/paper_evidence/` | | Evidence package: `RESEARCH_STATUS.md`, `DIAGNOSTIC_REPORT.md`, `LABEL_GENERATION_AUDIT.json`, `EQUIVALENT_LABEL_AUDIT.json`, baseline tables, claim matrices |
| `reports/external_validation/` | 55 | Nov-2026 multi-benchmark "external validation" (QuixBugs repaired harness, Bugs.jar, Codeflaws, SeqCoBench) — **audited in `02_PRIOR_CLAIM_AUDIT.md`** |
| `reports/v6_investigation/` | 15 | Prior V6 proposal documents (AI-generated; inputs, not authority) |
| `reports/{recovery_programme,remediation,sprint2}` | | Earlier recovery/remediation reports |
| `paper/`, `phase5-7/`, `docs/` | | Manuscript drafts, sprint workspaces, design docs |

## V5 pipeline (what "SBG V5" actually is)

```
program source ─▶ entry_policy.select_entry_structural (rename-invariant entry) ─▶ inputs synthesised from annotations
   (class tier: class_driver)                                    │
                                                                 ▼
                      sbg.v2.execution.runner.SandboxRunner (n_runs=5, seed 42, max_events 5000, per-trace timeout)
                                                                 │ ExecutionTrace[] (call/line/return/exception events,
                                                                 │  repr-capped locals, return_value, exception, truncated, coverage)
              ┌──────────────────────────┬───────────────────────┴───────────────┐
              ▼                          ▼                                       ▼
   DynamicGenomeV3 (sbg.v3)     TemporalGenomeV5 (events→sequences)    StateTransitionGraph (abstract value domain)
              └───────── d = 0.50·d_v3 + 0.25·d_temporal + 0.25·d_state  (fallback to d_v3 when a layer fails) ─────────┘
```

* `experiments/final/extraction.py::score_pair` is the single definition of the pair scores stored in `artifacts/final/pairs_*.jsonl` (`sbg_v5`, `sbg_v3`, `sbg_temporal`, `sbg_state`, execution-volume shortcuts, `static_token`, `static_ast`, `v5_full` flag).
* Silent degradations in V5: `distance_v5` returns **0.5** when V3 extraction fails and **0.0 for a missing layer**; `score_pair` substitutes `d_v3` when temporal/state fail (recorded only as `v5_full=0`). These are direct motivation for explicit execution-evidence in V6.
* Output-free protocol: pair scores must not read program outputs (`OUTPUT_ORACLE_LEAK_AUDIT.json` found the original entry policy traced self-test asserts in 47/64 programs; fixed by `output_free_v6+`).

## Benchmarks and label provenance

| Benchmark | Location | Pairs | Label origin |
|---|---|---|---|
| Synthetic v8 (train/val/test) | `benchmark/datasets/v8`, `artifacts/final/pairs_v8*_output_free_v8.jsonl` | 1931 / 461 / 967 | **generator-bound**: SP-* transform → EQUIVALENT(0), SC-* mutation → CHANGED(1); no execution-based equivalence check (`LABEL_GENERATION_AUDIT.json`); 73/842 train "EQUIVALENT" pairs differ in output (SP-8, SP-11) per `EQUIVALENT_LABEL_AUDIT.json` |
| v9c composed | `benchmark/datasets/v9_composed` | 233 dev (all label 1) | composed transformations |
| v10 independent | `benchmark/datasets/v10_independent` | 638, 19 programs | independent authoring |
| QuixBugs (Python) | `external/quixbugs` | 40 progs × (buggy, fixed, SP variants) | buggy/fixed = real bug; SP variants synthetic |
| BugsInPy units | `external/bugsinpy/units` | 55 function units | real bug fixes; inputs synthesised (most raise) |
| Bugs.jar / Codeflaws / SeqCoBench | `reports/external_validation` | 24 / 36 / 1364 (claimed) | see audit — no usable real-benchmark data in repo |

## Gaps relevant to V6

1. Labels are partially unverified and edit-size-confounded (reversed edit size AUROC 0.85 on train, 0.876 on test).
2. No plain **differential-testing** baseline exists in the pair files (outputs are deliberately unread).
3. `v8 test`, `v10` and the external sets are already observed; no pristine holdout remains. Any V6 result there is post-freeze, non-pristine.
4. Only Python has a working execution adapter. Java (`external/quixbugs_java`) has a separate runner; C has none that measures behaviour.
