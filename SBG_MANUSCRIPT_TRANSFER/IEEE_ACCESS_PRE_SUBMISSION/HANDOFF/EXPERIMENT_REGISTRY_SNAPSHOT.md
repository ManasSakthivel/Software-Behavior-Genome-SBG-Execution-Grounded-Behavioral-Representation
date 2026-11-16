# EXPERIMENT REGISTRY SNAPSHOT (2026-11-14 20:25 IST)

Authoritative registry files: `PKG/logs/registry/{A1_lit,A2_repo,A3_stats}.jsonl` (exist). A4R/A4B/A4C/A4D have **not yet written registry files**; their experiments below are reconstructed from output directories (status = what the files show, NOT agent-attested). `logs/registry/INDEX.md` does not exist yet (A4R's job).

## Registered (agent-attested)
| IDs | Owner | Status | Notes |
|---|---|---|---|
| EXP-A1-001..007 | A1 | COMPLETED (007 incl. early brief) | 001 has a stale RUNNING line + later COMPLETED line |
| EXP-A2-001..018 | A2 | 16 completed, 011 completed-with-abort (py39 pytest SIGABRT at one recursion test after 758 passed), 015 partial (orchestrator cache cross-check — superseded by full caches) | |
| EXP-A3-001..014 (+004b) | A3 | done | 522 quantities reproduced, max\|Δ\|=0.0 |

## Orchestrator (not in a registry file — reconstructed)
| ID | What | Status | Output |
|---|---|---|---|
| EXP-ORCH-001 | trace dump v10_test | COMPLETED 19/19 (first attempt died with the shell; resumed) | `results/raw/trace_cache/v10_test`, `logs/EXP-ORCH-001_v10.log` |
| EXP-ORCH-002 | trace dump v9c_val | COMPLETED 11/11 | `…/v9c_val` |
| EXP-ORCH-003 | trace dump v9c_train | PARTIAL 45/46; `math_gray_code` **FAILED rc=-9 after 1057 s** (cause unknown, not retried) | `…/v9c_train` |
| EXP-ORCH-004 | trace dump v9c_dev | COMPLETED 13/13 | `…/v9c_dev` |
| EXP-ORCH-005 | frozen populations | COMPLETED (v10 638/19; val 432/11; dev 464/13; train 1650/46) | `configs/populations/` |
| EXP-ORCH-006 | final SBG tree re-hash | **NOT RUN** | compare with `logs/sbg_tree_sha256_BEFORE.txt` |

## Reconstructed from files (UNREGISTERED, provenance classes provisional — A4R to confirm)
| ID | Owner (inferred) | Evidence / contents | Provisional class |
|---|---|---|---|
| EXP-A4-002 | predecessor A4 | features_*.json, extract_seconds_*, idf.pkl (19:59–20:00) | UNKNOWN PROVENANCE |
| EXP-A4-003 | predecessor A4 | independent-input batteries/runs/indep_*.json for ALL 4 splits (19:56–20:01 incl. v10_test, v9c_val outputs — label-free per file names; unverified) | UNKNOWN PROVENANCE |
| EXP-A4-004 | predecessor A4 | frozen_config.json, selection.json, models.pkl, config_train_dev_auroc.json (20:02:54) | UNKNOWN PROVENANCE (freeze before held-out unverified) |
| EXP-A4B-001 | A4B | smoke_*/sanity_*(v9c_dev) JSON for static_tce/ted/srclev/tfidf, trace_align, birthmark_kgram, obs_points (outfree/outreading), diffexec_same_input; logs `A4B_smoke_*.log` | PARTIALLY COMPLETE (RUNNING) |
| EXP-A4C-001 | A4C | features/, idf.pkl, indep/ (train+dev) | PARTIALLY COMPLETE |
| EXP-A4C-002 | A4C | `frozen_config.json` (20:19), models.pkl, selection, train/dev AUROC | COMPLETE-looking; **freeze precedes held-out** (no held-out predictions exist) |
| EXP-A4C-003 | A4C | predictions for v9c_train & v9c_dev (213 methods each); NO v10_test/v9c_val | PARTIALLY COMPLETE |
| EXP-A4C-004 | A4C | `eval_v9c_dev.json`, results matrix CSV (dev only, exploratory) | PARTIALLY COMPLETE |
| EXP-A4C-005 | A4C | incremental.json, sensitivity.json (dev) | PARTIALLY COMPLETE |
| EXP-A4D-002 | A4D | phase-1 re-verification of SBG columns: 296 quantities, max\|Δ\|=5.0e-7, 0 over tolerance | COMPLETE-looking |
| EXP-A4D-003 | A4D | independent population re-derivation | COMPLETE-looking (content not reviewed here) |
| EXP-A4D-004 | A4D | phase-1 pipelines on v10_test, v9c_val (SBG columns only) | COMPLETE-looking |
| EXP-A4D-005 | A4D | verification of A4C predictions — process live | RUNNING |

## Not started
EXP-A5E-*, EXP-A5F-*, EXP-A5G-*, EXP-A6-*, EXP-AI-*, EXP-AJ-*.

## Counts (honest)
Registered+reconstructed experiments: A1 7, A2 18, A3 15(+1), ORCH 5 executed (1 partial), A4-predecessor 3, A4 wave-2 ≈ 10 (running). Failed/interrupted: ORCH-003 (1 program), ORCH-001 first attempt, A2-011 (py39 abort), A4 predecessor (cancelled).
