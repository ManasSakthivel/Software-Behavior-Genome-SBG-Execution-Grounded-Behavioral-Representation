#!/usr/bin/env python3
"""Post-test SUPPLEMENT (EXPLORATORY, nothing here is tuned or selected): SBG component comparison on v8 dev and v8 test using the
already-scored pair files and the evaluation sets of evaluate_v8.py; appends v8 rows to BASELINE_COMPARISON.csv from the two
frozen-script result JSONs.  Writes artifacts/paper_evidence/V8_COMPONENT_COMPARISON.json.  Idempotent."""
import csv, hashlib, json, pathlib, sys

R = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "experiments" / "final"))
import evaluate_v8 as E  # noqa: E402
from sbg.statistics import auroc, cluster_bootstrap_ci, paired_cluster_bootstrap_delta  # noqa: E402

sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()  # noqa: E731
COMP = ("sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "exception_component_v3", "exception_type_jaccard", "n_functions", "combined_shortcut")
out = {"artifact": "V8_COMPONENT_COMPARISON", "status": "EXPLORATORY / DESCRIPTIVE (computed after the single frozen test run; no selection, no tuning; sbg_v5 remains the pre-declared primary)",
       "set": "VALID", "ci": "cluster bootstrap by base program, 2000 resamples, seed 42", "splits": {}}
for split in ("dev", "test"):
    rows = [r for r in E.load_scored(split) if r["_valid"]]
    y = [r["label"] for r in rows]; cl = [r["base_id"] for r in rows]
    t = {"n_pairs": len(rows), "n_programs": len(set(cl)), "n_changed": sum(y), "scored_pairs": {"path": str(E.PAIRS[split].relative_to(R)), "sha256": sha(E.PAIRS[split])}, "predictors": {}}
    for p in COMP:
        s = [r["scores"][p] for r in rows]
        lo, hi, n = cluster_bootstrap_ci(s, y, cl, n_bootstrap=2000, seed=42)
        t["predictors"][p] = {"auroc": round(auroc(s, y), 6), "ci95": [lo, hi]}
    for p in COMP[1:]:
        d = paired_cluster_bootstrap_delta([r["scores"]["sbg_v5"] for r in rows], [r["scores"][p] for r in rows], y, cl, n_bootstrap=2000, seed=42)
        t["predictors"][p]["delta_sbg_v5_minus_this"] = d if not isinstance(d, tuple) else list(d)
    out["splits"][split] = t
(R / "artifacts/paper_evidence/V8_COMPONENT_COMPARISON.json").write_text(json.dumps(out, indent=2) + "\n")

# ---- append v8 rows to BASELINE_COMPARISON.csv (idempotent) ----
csvp = R / "artifacts/paper_evidence/BASELINE_COMPARISON.csv"
rows = list(csv.reader(csvp.open()))
rows = [r for r in rows if not (r and r[0] in ("v8dev_frozen_script", "v8test_frozen_script"))]
for run, split, f, status in (("v8dev_frozen_script", "dev", "V8_DEV_DRYRUN_EVALUATION.json", "DEV dry run of the frozen script (excl. 1 stale program); exploratory; tau_v8 derived here"),
                              ("v8test_frozen_script", "test", "V8_TEST_EVALUATION.json", "CONFIRMATORY-BY-FREEZE single run (excl. 4 stale programs); see FREEZE_V8*.json caveats")):
    d = json.loads((R / "artifacts/paper_evidence" / f).read_text())["VALID"]
    for p, st in d["predictors"].items():
        rows.append([run, "v8", split, "output_free_v8", "VALID", p, st["auroc"], st["ci95_cluster_bootstrap"][0], st["ci95_cluster_bootstrap"][1],
                     d["n_pairs"], d["n_programs"], status, f"artifacts/paper_evidence/{f}", "frozen evaluate_v8.py"])
with csvp.open("w", newline="") as fh:
    csv.writer(fh).writerows(rows)
print("ok", len(rows) - 1, "csv rows")
for s in out["splits"]:
    print(s, {p: v["auroc"] for p, v in out["splits"][s]["predictors"].items()})
