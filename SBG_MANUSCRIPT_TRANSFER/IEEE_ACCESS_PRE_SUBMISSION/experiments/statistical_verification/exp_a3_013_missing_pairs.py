#!/usr/bin/env python3
"""EXP-A3-013: missing-pair / exclusion analysis and worst/best-case bounds.
For V10 (644->641->638) and V9c-val (436->434->432): list unevaluated pairs and dropped partners, label, edit size, failure kind; verify no unevaluated row
carries a score (no silent 0/0.5); compute AUROC bounds when the unevaluated CHANGED pairs are re-inserted with the WORST (score below everything) or
BEST (above everything) possible rank for the execution-derived predictors (edit is computable and is kept as is).
  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a3_013_missing_pairs.py"""
import csv, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L
out, tab = {}, []
for design in ("v10_test", "v9c_val"):
    allrows, prim = (L.build_v10(with_static=False) if design == "v10_test" else L.build_v9c("val"))
    meta = {m["pair_id"]: m for m in (L.jl(L.V10D / "pairs_test.jsonl") if design == "v10_test" else L.jl(L.V9D / "pairs_val.jsonl") + L.jl(L.V8D / "pairs_val.jsonl"))}
    raw = {r["pair_id"]: r for r in (L.jl(L.ART / "pairs_v10_test_v6exp.jsonl") if design == "v10_test" else L.jl(L.ART / "pairs_v9c_val_output_free_v8.jsonl") + L.jl(L.ART / "pairs_v8val_output_free_v8.jsonl"))}
    prim_ids = {r["pair_id"] for r in prim}
    unev = [r for r in allrows if not r["evaluated"]]
    silent = [r["pair_id"] for r in unev if raw[r["pair_id"]].get("scores") is not None]
    # groups with a dropped member
    badgroups = {r["group"] for r in unev}
    dropped_partners = [r for r in allrows if r["group"] in badgroups and r["evaluated"]]
    # edit sizes of everything incl. dropped
    def es(r):
        m = meta[r["pair_id"]]; return float(L.edit_size(m["base_path"], m["variant_path"]))
    info = []
    for r in unev + dropped_partners:
        m = meta[r["pair_id"]]; rw = raw[r["pair_id"]]
        info.append({"design": design, "pair_id": r["pair_id"], "label": r["label"], "role": "unevaluated" if not r["evaluated"] else "evaluated-partner-dropped-by-matched-rule",
                     "failure_kind": rw.get("failure_kind"), "failure_detail": str(rw.get("failure_detail"))[:80], "edit_size": es(r), "base_id": r["base_id"], "type": m.get("sp_type") or m["transformation_type"], "sc": m.get("sc_type")})
    tab += info
    allp = prim
    mean_edit = {lab: round(sum(r["edit"] for r in allp if r["label"] == lab) / max(1, sum(1 for r in allp if r["label"] == lab)), 3) for lab in (0, 1)}
    # bounds
    y = [r["label"] for r in allp]; res = {}
    full_ev = [r for r in allrows if r["evaluated"]]
    bounds = {}
    unev_ch = [r for r in unev if r["label"] == 1]
    for p in ("sbg_v5", "sbg_state", "edit", "coverage_size"):
        base = L.auroc([r["scores"][p] for r in allp], y)
        # re-insert: dropped partners (evaluated EQ) + unevaluated CH with worst/best
        s_ev = [r["scores"][p] for r in dropped_partners] + [r["scores"][p] for r in allp]
        y_ev = [r["label"] for r in dropped_partners] + y
        if p == "edit":
            s_u = [es(r) for r in unev_ch]; w = b = L.auroc(s_ev + s_u, y_ev + [1] * len(s_u))
        else:
            lo, hi = min(s_ev) - 1.0, max(s_ev) + 1.0
            w = L.auroc(s_ev + [lo] * len(unev_ch), y_ev + [1] * len(unev_ch)); b = L.auroc(s_ev + [hi] * len(unev_ch), y_ev + [1] * len(unev_ch))
        bounds[p] = {"primary_auroc": round(base, 4), "reinserted_worst": round(w, 4), "reinserted_best": round(b, 4)}
    out[design] = {"n_meta_pairs": len(meta), "n_unevaluated_in_file": len(unev), "unevaluated_ids": [r["pair_id"] for r in unev], "unevaluated_labels": [r["label"] for r in unev],
                   "unevaluated_rows_carrying_a_score": silent, "n_primary": len(allp), "dropped_evaluated_partners": [r["pair_id"] for r in dropped_partners],
                   "primary_mean_edit_by_label": mean_edit, "unevaluated_edit_sizes": [es(r) for r in unev], "worst_best_case_auroc_with_unevaluated_CH_reinserted": bounds}
    print(design, json.dumps(out[design], indent=1)[:2500])
with open(L.PKG / "results/tables/EXP-A3-013_unevaluated_and_dropped_pairs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(tab[0])); w.writeheader(); w.writerows(tab)
(L.PKG / "results/raw/EXP-A3-013").mkdir(parents=True, exist_ok=True)
(L.PKG / "results/raw/EXP-A3-013/missing_pairs.json").write_text(json.dumps({"summary": out, "rows": tab}, indent=1))
