"""Builds artifacts/paper_evidence/ABLATIONS.json (dev/train only; never reads a test split).

    python3 experiments/final/build_ablations.py
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from experiments.final.build_paper_evidence import RUNS, DATASETS, valid_rows, W, jl, js, src  # noqa: E402
from experiments.final.edit_size_analysis import _edit_size, EDIT_BINS, _bin_idx              # noqa: E402
from experiments.final.fit_weights import MODELS, score as lin_score                          # noqa: E402
from sbg.statistics import auroc, cluster_bootstrap_ci                                        # noqa: E402

OUT = REPO / "artifacts" / "paper_evidence" / "ABLATIONS.json"


def strata(run):
    r = RUNS[run]
    assert r["split"] != "test"
    meta = {}
    for sp in ("train", "dev", "val"):
        for m in jl(f"{DATASETS[r['dataset']]}/pairs_{sp}.jsonl"):
            meta[m["pair_id"]] = m
    rows = valid_rows(run)
    sizes = [_edit_size(meta[x["pair_id"]]["base_path"], meta[x["pair_id"]]["variant_path"]) for x in rows]
    res = {}
    for i, (lo, hi) in enumerate(EDIT_BINS):
        idx = [k for k, s in enumerate(sizes) if _bin_idx(s) == i]
        y = [rows[k]["label"] for k in idx]
        entry = {"edit_size_range": [lo, hi if hi < 10 ** 9 else None], "n": len(idx),
                 "n_changed": sum(y), "n_equivalent": len(y) - sum(y)}
        if sum(y) >= 5 and len(y) - sum(y) >= 5:
            cl = [rows[k]["base_id"] for k in idx]
            for name, fn in (("sbg_v5", lambda x: x["scores"]["sbg_v5"]),
                             ("exception_fraction", lambda x: x["scores"]["exception_fraction"]),
                             ("learned_m2", lambda x: lin_score(W["models"]["M2"], MODELS["M2"], x["scores"]))):
                sc = [fn(rows[k]) for k in idx]
                lo_, hi_, _ = cluster_bootstrap_ci(sc, y, cl, n_bootstrap=1000, seed=42)
                entry[name] = {"auroc": round(auroc(sc, y), 6), "ci95": [lo_, hi_],
                               "n_programs": len(set(cl))}
        else:
            entry["note"] = "stratum omitted: fewer than 5 pairs in a class (AUROC undefined/unstable)"
        res[str(i)] = entry
    mean_by = {}
    for lab in (1, 0):
        v = [s for s, x in zip(sizes, rows) if x["label"] == lab]
        mean_by["changed" if lab else "equivalent"] = round(sum(v) / len(v), 3)
    return {"edit_size_unit": "changed canonical-AST lines (experiments/final/edit_size_analysis._edit_size)",
            "mean_edit_size": mean_by, "strata": res}


def main():
    comp = {}
    for run in ("v6train_v7", "v6dev_v7", "v8dev_v8_rescore", "v6test_v6"):
        m = js(RUNS[run]["main"])
        p = m["results"]["VALID"]["predictors"]
        comp[run] = {k: {"auroc": p[k]["auroc"], "ci95": p[k]["ci95_cluster_bootstrap"]}
                     for k in ("sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction",
                               "call_count", "coverage_size", "n_functions", "combined_shortcut",
                               "static_token", "static_ast") if k in p}
        comp[run]["_label_shuffle_noise_floor"] = m["results"]["VALID"]["label_shuffle_noise_floor_primary"]
        comp[run]["_source"] = src(RUNS[run]["main"])
    out = {
        "scope": "Component ablation of SBG V5 (v3/temporal/state), weight-model ablation (M0/M1/M2), "
                 "edit-size confound controls, label-shuffle noise floors. Dev/train/observed-test only.",
        "component_ablation_v5": {
            "definition": "sbg_v5 = 0.50*sbg_v3 + 0.25*sbg_temporal + 0.25*sbg_state; each component scored separately "
                          "by analyse_results.py on the VALID set",
            "by_run": comp},
        "weight_model_ablation": {
            "fitted_on": "v6 TRAIN (VALID pairs)", "selected_on": "v6 DEV AUROC",
            "models": {m: {"features": v["features"], "train_auroc": v["train_auroc"], "dev_auroc": v["dev_auroc"]}
                       for m, v in W["models"].items()},
            "chosen_on_dev": W["chosen_on_dev"],
            "source": src("artifacts/final/WEIGHT_FITTING.json"),
            "caveat": "dev AUROC of M2 (0.7128) vs M0 (0.6671) is a selection statistic on 9 programs; "
                      "the M2-minus-M0 difference was not tested out-of-sample on a held-out TEST split."},
        "edit_size_confound_control": {
            "finding": "Reversed edit size (smaller edit => CHANGED) alone separates CHANGED from EQUIVALENT with "
                       "AUROC ~0.95 on v6 train/dev (construction artefact of the v6 generator). On v8 "
                       "(max_names=1 edit-size redesign) the confound is reduced but not removed (~0.85).",
            "by_run": {run: strata(run) for run in ("v6train_v7", "v6dev_v7", "v8dev_v8_rescore")},
            "raw_confound_files": ["artifacts/paper_evidence/raw/confound_v6train.json",
                                   "artifacts/paper_evidence/raw/confound_v6dev.json",
                                   "artifacts/paper_evidence/raw/confound_v8dev.json"],
            "historical_test_confound": {
                "reversed_edit_size_auroc_v6_test": 0.9667,
                "source": "reports/remediation/results/edit_size_analysis_test.json (pre-existing, not recomputed here)"},
        },
        "external_corpora_shortcut_controls": {
            "bugsinpy_valid_set": {k: js("artifacts/final/BUGSINPY_output_free_v7.json")["sets"]["VALID"]["predictors"][k]["auroc"]
                                   for k in ("sbg_v5", "exception_fraction", "call_count", "combined_shortcut", "static_ast")},
            "source": src("artifacts/final/BUGSINPY_output_free_v7.json")},
        "historical_ablations_not_comparable": {
            "files": ["results/ablations/component_ablation.json", "results/ablations/representation_ablation.json"],
            "reason": "produced 2026-08-30 on the pre-remediation 'published' protocol over the original 744-pair test "
                      "split; not comparable to output_free_v7/v8 runs and not re-run"},
        "output_oracle_leak_audit": src("artifacts/final/OUTPUT_ORACLE_LEAK_AUDIT.json"),
        "not_available": ["No ablation on any held-out TEST split (none exists); "
                          "no v8 TEST ablation; no per-transformation-type v8 ablation computed."],
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    for run, v in out["edit_size_confound_control"]["by_run"].items():
        print(run, v["mean_edit_size"])
        for i, s in v["strata"].items():
            print("  ", i, s["edit_size_range"], s["n"], s["n_changed"], s["n_equivalent"],
                  s.get("sbg_v5", {}).get("auroc"), s.get("learned_m2", {}).get("auroc"))


if __name__ == "__main__":
    main()
