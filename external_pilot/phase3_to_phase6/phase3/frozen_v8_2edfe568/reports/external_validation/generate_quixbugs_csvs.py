#!/usr/bin/env python3
"""
Generate QuixBugs CSV deliverables from recomputed summary JSON.
"""
import json
import pathlib
import pandas as pd

WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parent
summary_json = WORKSPACE_ROOT / "quixbugs_full_recomputation_summary.json"

with open(summary_json) as f:
    data = json.load(f)

rows = []
for k, v in data.items():
    rows.append({
        "configuration": k,
        "input_regime": v["regime"],
        "include_sp2": v["include_sp2"],
        "n_pairs": v["n_pairs"],
        "n_positives": v["n_pos"],
        "n_negatives": v["n_neg"],
        "auroc_sbg_v5_raw": round(v["auroc_sbg_raw"], 4),
        "ci_sbg_v5_low": round(v["ci_sbg"][0], 4),
        "ci_sbg_v5_high": round(v["ci_sbg"][1], 4),
        "auroc_state_alone": round(v["auroc_state_raw"], 4),
        "auroc_edit_baseline": round(v["auroc_edit_raw"], 4),
        "auroc_lr_conventional": round(v["auroc_lr_conv"], 4),
        "ci_lr_conv_low": round(v["ci_conv"][0], 4),
        "ci_lr_conv_high": round(v["ci_conv"][1], 4),
        "auroc_lr_sbg_alone": round(v["auroc_lr_sbg"], 4),
        "auroc_lr_full": round(v["auroc_lr_full"], 4),
        "ci_lr_full_low": round(v["ci_full"][0], 4),
        "ci_lr_full_high": round(v["ci_full"][1], 4),
        "auroc_rf_conventional": round(v["auroc_rf_conv"], 4),
        "auroc_rf_full": round(v["auroc_rf_full"], 4),
        "delta_lr_incremental": round(v["delta_lr"], 4),
        "ci_delta_low": round(v["ci_delta"][0], 4),
        "ci_delta_high": round(v["ci_delta"][1], 4),
    })

df = pd.DataFrame(rows)
df.to_csv(WORKSPACE_ROOT / "QUIXBUGS_RECOMPUTED_RESULTS.csv", index=False)
print("Saved QUIXBUGS_RECOMPUTED_RESULTS.csv")

# Trace diagnostics per program
pairs_csv = WORKSPACE_ROOT / "quixbugs_repaired_native_all_pairs.csv"
if pairs_csv.exists():
    df_p = pd.read_csv(pairs_csv)
    diag = df_p.groupby("prog").agg({
        "sbg_v5": "mean",
        "state_dist": "mean",
        "topology_dist": "mean",
        "temporal_dist": "mean",
        "exec_steps_diff": "mean",
        "exc_diff": "mean",
        "edit_size": "mean",
    }).reset_index()
    diag.to_csv(WORKSPACE_ROOT / "QUIXBUGS_TRACE_DIAGNOSTICS.csv", index=False)
    print("Saved QUIXBUGS_TRACE_DIAGNOSTICS.csv")
