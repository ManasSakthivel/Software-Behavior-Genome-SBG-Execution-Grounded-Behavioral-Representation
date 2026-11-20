# SBG EXECUTION PROVENANCE & REPRODUCIBILITY SCHEMA

**Version:** 1.0  
**Compliance:** IEEE Empirical Software Engineering Standards  
**Target:** Cryptographically Verifiable Execution Trace & Score Provenance

---

## 1. Provenance Manifest Specification

Every experiment output directory contains a registered `provenance.json` recording the exact environment, parameters, and artifact hashes.

### JSON Schema Structure:
```json
{
  "experiment_id": "EXP-A4C-002",
  "timestamp_utc": "2026-11-14T14:49:17Z",
  "execution_environment": {
    "cpython_version": "3.13.5",
    "platform": "darwin-arm64",
    "os_release": "25.6.0",
    "python_hash_seed": 0,
    "dont_write_bytecode": 1
  },
  "dataset_manifest": {
    "split_name": "v10_test",
    "pair_count": 638,
    "program_count": 19,
    "dataset_sha256": "f52bfaee96f501fc19198de2a585dcfc500e0ae21e13f2dec0d3d670251e7bdb"
  },
  "protocol_configuration": {
    "protocol_version": "output_free_v8",
    "n_runs": 5,
    "max_events": 5000,
    "trace_timeout_s": 1.0,
    "program_budget_s": 60.0,
    "input_battery_size": 11,
    "entry_policy": "select_entry_structural"
  },
  "weights": {
    "d_V3": 0.50,
    "d_temporal": 0.25,
    "d_state": 0.25
  },
  "output_artifacts": {
    "predictions_jsonl": "pairs_v10_test_v6exp.jsonl",
    "predictions_sha256": "9b12a...38ef",
    "evaluation_summary": "EVALUATION_V10.json"
  }
}
```

---

## 2. Integrity Verification Invariants

1. **Pre-Registration Hash Check:** Predictions are only valid if computed after the `dataset_sha256` and protocol configuration have been committed and registered.
2. **Single-Pass Evaluation:** No iterative hyperparameter tuning is permitted on held-out test splits.
3. **Reproducibility Guarantee:** Any independent researcher running the registered environment with `PYTHONHASHSEED=0` must generate byte-exact matching predictions.
