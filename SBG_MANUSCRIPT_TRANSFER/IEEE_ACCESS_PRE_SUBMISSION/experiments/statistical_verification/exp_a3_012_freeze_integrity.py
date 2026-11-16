#!/usr/bin/env python3
"""EXP-A3-012: freeze-file integrity & chronology. Re-hash every file pinned by FREEZE_V9.json / FREEZE_V10.json / FREEZE_V10_SCORED.json and compare with the
CURRENT repo working tree (read-only); read-only git chronology of the frozen artifacts; v5_full / fallback fraction in the scored pairs files.
  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a3_012_freeze_integrity.py"""
import csv, hashlib, json, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L
R = L.REPO
def sh(p): return hashlib.sha256((R / p).read_bytes()).hexdigest()
def git(*a): return subprocess.run(["git", "-C", str(R), *a], capture_output=True, text=True).stdout.strip()
rows = []
f10 = json.loads((L.ART / "FREEZE_V10.json").read_text())
for p, h in f10["sha256"].items():
    rows.append({"freeze": "FREEZE_V10", "path": p, "pinned": h, "current": sh(p), "match": sh(p) == h})
rows.append({"freeze": "FREEZE_V10", "path": "benchmark/datasets/v10_independent/variants (tree sha)", "pinned": f10["variants_tree_sha256"], "current": "", "match": "n/a (tree-hash algorithm not re-derived)"})
s10 = json.loads((L.ART / "FREEZE_V10_SCORED.json").read_text())
rows.append({"freeze": "FREEZE_V10_SCORED", "path": s10["scored_file"], "pinned": s10["scored_file_sha256"], "current": sh(s10["scored_file"]), "match": sh(s10["scored_file"]) == s10["scored_file_sha256"]})
f9 = json.loads((L.ART / "FREEZE_V9.json").read_text())
m = {"experiments/final/evaluate_v9.py": f9["code_sha256"]["experiments/final/evaluate_v9.py"],
     "artifacts/final/pairs_v9c_val_output_free_v8.jsonl": f9["scored_v9c_val_sha256"], "artifacts/final/pairs_v8val_output_free_v8.jsonl": f9["scored_v8_val_sha256"],
     "benchmark/datasets/v9_composed/pairs_val.jsonl": f9["dataset"]["v9c_pairs_val"], "benchmark/datasets/v8/pairs_val.jsonl": f9["dataset"]["v8_pairs_val"]}
for p, h in m.items(): rows.append({"freeze": "FREEZE_V9", "path": p, "pinned": h, "current": sh(p), "match": sh(p) == h})
v10m = json.loads((L.ART / "V10_MODELS_FROZEN.json").read_text())
rows.append({"freeze": "V10_MODELS_FROZEN", "path": "artifacts/final/pairs_v9c_train_v6exp.jsonl (fit input)", "pinned": v10m["fitted_on"]["scored_v6exp_sha256"], "current": sh("artifacts/final/pairs_v9c_train_v6exp.jsonl"),
             "match": sh("artifacts/final/pairs_v9c_train_v6exp.jsonl") == v10m["fitted_on"]["scored_v6exp_sha256"]})
v9m = json.loads((L.ART / "V9_MODELS_FROZEN.json").read_text())
rows.append({"freeze": "V9_MODELS_FROZEN", "path": "artifacts/final/pairs_v9c_train_output_free_v8.jsonl (fit input)", "pinned": v9m["fitted_on"]["scored_pairs_sha256"], "current": sh("artifacts/final/pairs_v9c_train_output_free_v8.jsonl"),
             "match": sh("artifacts/final/pairs_v9c_train_output_free_v8.jsonl") == v9m["fitted_on"]["scored_pairs_sha256"]})
with open(L.PKG / "results/tables/EXP-A3-012_freeze_hashes.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["freeze", "path", "pinned", "current", "match"]); w.writeheader(); w.writerows(rows)
mism = [r for r in rows if r["match"] is False]
print("hash checks:", len(rows), "mismatches:", len(mism)); [print(" MISMATCH", r["freeze"], r["path"]) for r in mism]
# git chronology (read-only)
chron = {}
for p in ["artifacts/final/FREEZE_V10.json", "artifacts/final/FREEZE_V10_SCORED.json", "artifacts/final/V10_MODELS_FROZEN.json", "artifacts/final/pairs_v10_test_v6exp.jsonl", "experiments/final/evaluate_v10.py",
          "artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json", "benchmark/datasets/v10_independent/pairs_test.jsonl", "artifacts/final/FREEZE_V9.json", "artifacts/final/V9_MODELS_FROZEN.json",
          "artifacts/final/pairs_v9c_val_output_free_v8.jsonl", "artifacts/paper_evidence/V9_VAL_EVALUATION.json", "experiments/final/evaluate_v9.py", "experiments/final/fit_weights.py", "sbg/statistics.py",
          "sbg/v5/distance_v5.py", "experiments/final/extraction.py", "benchmark/scripts/generate_v10_independent.py"]:
    chron[p] = git("log", "--format=%h|%aI|%s", "--", p).splitlines()
chron["v5_weights_introduced"] = git("log", "-S", "TEMPORAL_WEIGHT = 0.25", "--format=%h|%aI|%s").splitlines()
chron["FREEZE_V10.written_at"] = f10["written_at"]; chron["FREEZE_V10.git_head"] = f10["git_head"]; chron["FREEZE_V9.written_at"] = f9["written_at"]; chron["FREEZE_V9.git_head"] = f9["git_head_at_freeze"]
chron["git_head_now"] = git("rev-parse", "HEAD")
chron["c5bc130_commit_time"] = git("show", "-s", "--format=%aI", "c5bc130"); chron["8386eb5_commit_time"] = git("show", "-s", "--format=%aI", "8386eb5")
chron["files_in_c5bc130_that_are_freeze_pinned_and_changed_since_8386eb5"] = git("diff", "--stat", "8386eb5", "c5bc130", "--", "experiments/final/extraction.py", "experiments/final/protocol.py", "experiments/final/entry_policy.py", "experiments/final/static_baselines.py",
                                                                                 "experiments/final/fit_weights.py", "sbg/statistics.py", "sbg/v3/genome.py", "sbg/v5", "sbg/extraction/dynamic/tracer.py", "experiments/final/edit_size_analysis.py").splitlines()
# v5_full & fallbacks in scored files
fb = {}
for name, pth in (("v10_test", "pairs_v10_test_v6exp.jsonl"), ("v9c_val", "pairs_v9c_val_output_free_v8.jsonl"), ("v9c_train", "pairs_v9c_train_output_free_v8.jsonl"), ("v8_test", "pairs_v8test_output_free_v8.jsonl")):
    rr = [r for r in L.jl(L.ART / pth) if r["evaluated"]]
    fb[name] = {"evaluated": len(rr), "v5_full_false": sum(1 for r in rr if not r["scores"]["v5_full"]), "sbg_v5_exactly_0": sum(1 for r in rr if r["scores"]["sbg_v5"] == 0.0),
                "sbg_v5_exactly_0.5": sum(1 for r in rr if r["scores"]["sbg_v5"] == 0.5), "state_exactly_0.5": sum(1 for r in rr if r["scores"]["sbg_state"] == 0.5)}
chron["fallback_counts"] = fb
(L.PKG / "results/raw/EXP-A3-012/freeze_chronology.json").write_text(json.dumps({"hash_rows": rows, "chronology": chron}, indent=1, default=str))
print(json.dumps(chron, indent=1)[:6000])
