# PHASE 7 ACCEPTANCE — V4 session

| check | command | result |
|---|---|---|
| full suite | `PYTHONHASHSEED=0 python -m pytest sbg/ tests/ -q -p no:cacheprovider` | 807 passed (3 warnings, pre-existing) |
| new tests | `tests/test_zero_score_v4.py` (35), `tests/test_v10_independent.py` (7) | 42 passed |
| consistency | `experiments/final/consistency_check.py` | 10/10 |
| gate | `experiments/final/stanford_gate.py` | 8/20 PASS, 12 BLOCKED (unchanged; novelty and real-bug items remain BLOCKED) |
| data integrity | `experiments/final/data_integrity.py --dataset benchmark/datasets/v8 --strict` | rc 0 |
| trace V3 | `experiments/final/verify_trace_v3.py` | 31/31 |
| trace V4 | `experiments/final/verify_trace_v4.py` | 35/35 |
| frozen artifacts | FREEZE_V8/V9 hashes (consistency C9), FREEZE_V10 hashes (`test_freeze_v10_hashes_match`) | unchanged |

No frozen file (`extraction.py`, `sbg/v3/genome.py`, `sbg/v5/*`, v8/v9 datasets and scored files) was modified. Four pre-existing untracked stale `*_dev_output_free_v8` files were left alone.
