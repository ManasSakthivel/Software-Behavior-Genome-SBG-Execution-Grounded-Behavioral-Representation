#!/usr/bin/env python3
"""EXP-A3-006: threshold-selection integrity.
 (1) recompute Youden thresholds on V9c-TRAIN matched-complete population with own code; compare with V10_MODELS_FROZEN.json (and V9_MODELS_FROZEN.json)
 (2) [--refit] refit the frozen logistic combiners with own fit_logistic on V9c-train and compare weights
 (3) V10 and V9c-val precision/recall/F1 at the FROZEN thresholds, + oracle best-F1 thresholds on the test sets (NON-HONEST, informational)
  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a3_006_thresholds.py [--refit]
"""
import csv, json, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L

RAW = L.PKG / "results/raw/EXP-A3-006"; TAB = L.PKG / "results/tables"
refit = "--refit" in sys.argv
t0 = time.time()

def add_static(rows):
    cache = {}
    for r in rows:
        if "static_ast" in r["scores"]:
            continue
        for p in (r["base_path"], r["variant_path"]):
            if p not in cache:
                src = (L.REPO / p).read_text(); cache[p] = (L.token_multiset(src), L.ast_multiset(src))
        r["scores"]["static_token"] = L.ms_distance(cache[r["base_path"]][0], cache[r["variant_path"]][0])
        r["scores"]["static_ast"] = L.ms_distance(cache[r["base_path"]][1], cache[r["variant_path"]][1])

def add_models(rows, models):
    for r in rows:
        for n, m in models.items():
            r["scores"]["M_" + n] = L.lin_score({"features": m["features"], **m}, r["scores"])
        r["scores"]["edit_reversed"] = -r["edit"]

mf10 = json.loads((L.ART / "V10_MODELS_FROZEN.json").read_text())
mf9 = json.loads((L.ART / "V9_MODELS_FROZEN.json").read_text())
_, tr = L.build_v9c("train", v6exp=True)
add_static(tr)
print("train matched-complete", len(tr), len({r["base_id"] for r in tr}), flush=True)
add_models(tr, mf10["models"])
y = [r["label"] for r in tr]
out = {"train_n": len(tr), "train_programs": len({r["base_id"] for r in tr}), "train_changed": sum(y), "thresholds": {}}
rows = []
for name, frozen in mf10["thresholds_youden_train"].items():
    if name not in tr[0]["scores"]:
        rows.append({"predictor": name, "frozen": frozen, "recomputed": None, "abs_diff": None, "note": "score not available"}); continue
    s = [r["scores"][name] for r in tr]
    t = L.youden(s, y)
    rows.append({"predictor": name, "frozen": frozen, "recomputed": t, "abs_diff": abs(t - frozen) if t is not None else None, "note": ""})
out["thresholds"] = rows
# V9 frozen thresholds (separate file)
v9thr = mf9.get("thresholds_youden_train") or mf9.get("thresholds") or {}
out["v9_frozen_threshold_keys"] = list(v9thr)
w = max((r["abs_diff"] for r in rows if r["abs_diff"] is not None), default=None)
out["max_abs_threshold_diff"] = w
print("max abs thr diff", w, flush=True)
with open(TAB / "EXP-A3-006_thresholds_recomputed.csv", "w", newline="") as f:
    cw = csv.DictWriter(f, fieldnames=list(rows[0])); cw.writeheader(); cw.writerows(rows)

# (3) P/R/F1 on test sets at frozen thresholds + oracle thresholds
def prf_table(pop, tag, thr_map):
    yy = [r["label"] for r in pop]; res = []
    for name in ["sbg_v5", "sbg_state", "edit", "coverage_size", "exception_fraction", "call_count", "static_ast", "static_token",
                 "M_E", "M_X", "M_EX", "M_E+V5", "M_EX+V5"]:
        if name not in pop[0]["scores"]:
            continue
        s = [r["scores"][name] for r in pop]
        a = L.prf_at(s, yy, thr_map[name])
        ot, of = L.best_f1_threshold(s, yy)
        o = L.prf_at(s, yy, ot)
        base_f1 = 2 * sum(yy) / (len(yy) + sum(yy))   # F1 of 'predict everything CHANGED'
        res.append({"design": tag, "predictor": name, "frozen_thr": thr_map[name], "auroc": round(L.auroc(s, yy), 4), "auprc": round(L.auprc(s, yy), 4),
                    "precision": round(a["precision"], 4), "recall": round(a["recall"], 4), "f1": round(a["f1"], 4), "specificity": round(a["specificity"], 4),
                    "tp": a["tp"], "fp": a["fp"], "fn": a["fn"], "tn": a["tn"], "all_positive_f1": round(base_f1, 4),
                    "ORACLE_thr_NONHONEST": ot, "ORACLE_f1": round(o["f1"], 4), "ORACLE_prec": round(o["precision"], 4), "ORACLE_rec": round(o["recall"], 4)})
    return res
_, v10 = L.build_v10(); add_models(v10, mf10["models"])
_, v9v = L.build_v9c("val"); add_static(v9v)
for r in v9v: r["scores"]["edit_reversed"] = -r["edit"]
thr = mf10["thresholds_youden_train"]
tabs = prf_table(v10, "v10_test", thr)
# V9c val: use V9 frozen thresholds (the models frozen for the V9 evaluation) when available, else V10-frozen
thr9 = {**thr}
v9tabs = []
for r in v9v:
    pass
v9tabs = prf_table(v9v, "v9c_val(train-Youden thr; V9 models n/a)", thr)
allrows = tabs + v9tabs
with open(TAB / "EXP-A3-006_prf_at_frozen_and_oracle_thresholds.csv", "w", newline="") as f:
    cw = csv.DictWriter(f, fieldnames=list(allrows[0])); cw.writeheader(); cw.writerows(allrows)
out["prf"] = allrows

# (2) optional refit
if refit:
    refit_res = []
    for n, m in mf10["models"].items():
        if n in ("EX+V5+V6",) and False: continue
        feats = m["features"]
        X = [[r["scores"][f] for f in feats] for r in tr]
        t1 = time.time(); fit = L.fit_logistic(X, y)
        dw = max(abs(a - b) for a, b in zip(fit["weights_standardised"], m["weights_standardised"]))
        db = abs(fit["bias"] - m["bias"])
        refit_res.append({"model": n, "features": "+".join(feats), "max_abs_dw": dw, "abs_db": db,
                          "max_abs_dmean": max(abs(a - b) for a, b in zip(fit["feature_means"], m["feature_means"])),
                          "max_abs_dstd": max(abs(a - b) for a, b in zip(fit["feature_stds"], m["feature_stds"])),
                          "own": fit, "frozen_w": m["weights_standardised"], "seconds": round(time.time() - t1, 1)})
        print("refit", n, dw, db, flush=True)
    out["refit"] = refit_res
    with open(TAB / "EXP-A3-006_refit_weights.csv", "w", newline="") as f:
        cw = csv.writer(f); cw.writerow(["model", "features", "max_abs_dw", "abs_db", "max_abs_dmean", "max_abs_dstd", "seconds"])
        for r in refit_res: cw.writerow([r["model"], r["features"], r["max_abs_dw"], r["abs_db"], r["max_abs_dmean"], r["max_abs_dstd"], r["seconds"]])
out["runtime_s"] = round(time.time() - t0, 1)
(RAW / ("thresholds_refit.json" if refit else "thresholds.json")).write_text(json.dumps(out, indent=1, default=str))
print("done", out["runtime_s"])
