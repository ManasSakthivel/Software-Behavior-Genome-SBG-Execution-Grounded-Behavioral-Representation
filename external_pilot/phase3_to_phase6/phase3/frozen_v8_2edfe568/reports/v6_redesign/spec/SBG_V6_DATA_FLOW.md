# SBG V6 — Data Flow
pairs JSONL (base_path, variant_path, label, split) -> `experiments/v6/extract_pairs.py` (multiprocessing; one worker = one base+variant)
-> V5 `entry_policy` + `extraction._runner` (traces captured by a recording wrapper; the V5 ProgramRecord is also built, so V5 scores are *recomputed* and compared with the stored ones)
-> `sbgv6.features` (A,B,C,R,E) + `sbgv6.evidence` -> pair record (JSONL, one line per pair, all vectors + stored V5 scores)
-> `experiments/v6/evaluate.py` (grouped CV, baselines, bootstrap) -> `artifacts/v6/results_*.json` and predictions CSV (pair_id, fold, model, score).
Stored: `artifacts/v6/features_<set>.jsonl`, `predictions_<set>.csv`, `FREEZE_V6.json`, run logs with seeds and versions.
