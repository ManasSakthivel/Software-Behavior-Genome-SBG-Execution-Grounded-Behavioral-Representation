#!/usr/bin/env python3
"""EXP-A3-010: sensitivity of V9c-val headline results to the label defects found by EXP-A3-008/009 (post-hoc, exploratory; frozen analysis unchanged).
Scenarios (matched SETS are removed as a unit):
  S0 reported primary population (432 pairs)
  S1 drop the 16 EQUIVALENT pairs whose outputs differ from base (SP-8/SP-11 generator defects) + their CHANGED partners
  S2 drop CHANGED pairs with no observable output difference on protocol inputs (67) + their EQ partners
  S3 drop both (clean-label subset: only pairs with oracle-confirmed labels)
  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a3_010_label_clean_sensitivity.py
"""
import csv, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L
RAW = L.PKG / "results/raw/EXP-A3-010"; RAW.mkdir(parents=True, exist_ok=True)
_, pop = L.build_v9c("val")
mf = json.loads((L.ART / "V9_MODELS_FROZEN.json").read_text())["models"]
for r in pop:
    for n, m in mf.items():
        r["scores"]["M_" + n] = L.lin_score({"features": m["features"], **m}, r["scores"])
mut = json.loads((L.PKG / "results/raw/EXP-A3-009/mutation_aware.json").read_text())
ch_same = {x["pair_id"] for x in mut if x["label"] == 1 and x["n_any_diff"] == 0}
eq_diff = {x["pair_id"] for x in mut if x["label"] == 0 and x["n_any_diff"] > 0}
bad_sets = lambda ids: {r["group"] for r in pop if r["pair_id"] in ids}   # noqa: E731
sc = {"S0 reported (432)": set(), "S1 drop sets with EQ output-differing (SP-8/SP-11)": bad_sets(eq_diff),
      "S2 drop sets with CH no-observable-diff": bad_sets(ch_same), "S3 drop both (clean labels)": bad_sets(eq_diff) | bad_sets(ch_same)}
preds = ["sbg_v5", "sbg_state", "edit", "M_EX", "M_ESX", "M_E", "M_ES", "coverage_size", "static_ast"]
rows, out = [], {}
plan_cache = {}
for name, drop in sc.items():
    sub = [r for r in pop if r["group"] not in drop]
    y = [r["label"] for r in sub]; c = [r["base_id"] for r in sub]
    d = {"n": len(sub), "n_sets": len(sub) // 2, "n_programs": len(set(c)), "n_changed": sum(y), "auroc": {}, "delta": {}}
    for p in preds:
        s = [r["scores"][p] for r in sub]
        a = L.auroc(s, y); ci = L.boot_ci(s, y, c)
        d["auroc"][p] = [round(a, 4), ci[0], ci[1]]
        rows.append({"scenario": name, "n": len(sub), "n_programs": len(set(c)), "predictor": p, "auroc": round(a, 4), "ci_lo": ci[0], "ci_hi": ci[1]})
    for h, a_, b_ in (("H2 M_ES-M_E", "M_ES", "M_E"), ("H3 V5-edit", "sbg_v5", "edit"), ("H4 M_ESX-M_EX", "M_ESX", "M_EX"), ("V5-state", "sbg_v5", "sbg_state")):
        dl = L.paired_delta([r["scores"][a_] for r in sub], [r["scores"][b_] for r in sub], y, c)
        d["delta"][h] = dl
        rows.append({"scenario": name, "n": len(sub), "n_programs": len(set(c)), "predictor": "DELTA " + h, "auroc": dl.get("delta") if isinstance(dl, dict) else dl[0], "ci_lo": "", "ci_hi": ""})
    out[name] = d
    print(name, d["n"], d["n_programs"], {p: d["auroc"][p][0] for p in ("sbg_v5", "sbg_state", "edit", "M_EX", "M_ESX")}, flush=True)
    print("   deltas", {k: (v if not isinstance(v, dict) else {kk: v[kk] for kk in list(v)[:5]}) for k, v in d["delta"].items()}, flush=True)
(RAW / "label_clean_sensitivity.json").write_text(json.dumps(out, indent=1, default=str))
with open(L.PKG / "results/tables/EXP-A3-010_v9c_val_label_clean_sensitivity.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
