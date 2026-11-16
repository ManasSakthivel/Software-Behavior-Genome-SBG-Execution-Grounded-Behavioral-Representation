#!/usr/bin/env python3
"""EXP-A3-001: independent re-derivation of the V10-test / V9c-{val,dev,train} / V8-test populations from raw files and
comparison with PKG/configs/populations/*.json (built by the repo loader).

  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a3_001_populations.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L  # noqa: E402

OUT = L.PKG / "results"
(OUT / "raw" / "EXP-A3-001").mkdir(parents=True, exist_ok=True)
(OUT / "tables").mkdir(parents=True, exist_ok=True)
(OUT / "processed").mkdir(parents=True, exist_ok=True)


def compare(name, mine_all, mine_prim, key_scores):
    ref = json.loads((L.PKG / "configs" / "populations" / f"{name}.json").read_text())
    ref_rows = {r["pair_id"]: r for r in ref["rows"]}
    ref_prim = {r["pair_id"]: r for r in ref["rows"] if r.get("in_primary_population")}
    mine_rows = {r["pair_id"]: r for r in mine_all}
    prim = {r["pair_id"]: r for r in mine_prim}
    diffs = {"rows_only_mine": sorted(set(mine_rows) - set(ref_rows)), "rows_only_ref": sorted(set(ref_rows) - set(mine_rows)),
             "primary_only_mine": sorted(set(prim) - set(ref_prim)), "primary_only_ref": sorted(set(ref_prim) - set(prim)),
             "label_mismatch": [], "group_mismatch": [], "edit_mismatch": [], "score_max_abs_diff": {}, "base_id_mismatch": []}
    for pid in set(prim) & set(ref_prim):
        a, b = prim[pid], ref_prim[pid]
        if a["label"] != b["label"]:
            diffs["label_mismatch"].append(pid)
        if a["group"] != b["group"]:
            diffs["group_mismatch"].append(pid)
        if a["base_id"] != b["base_id"]:
            diffs["base_id_mismatch"].append(pid)
        if a["edit"] != b["edit"]:
            diffs["edit_mismatch"].append((pid, a["edit"], b["edit"]))
        for k in key_scores:
            d = abs(a["scores"][k] - b["scores"][k])
            diffs["score_max_abs_diff"][k] = max(diffs["score_max_abs_diff"].get(k, 0.0), d)
    prog = lambda rr: len({r["base_id"] for r in rr})  # noqa: E731
    return {"population": name, "mine": {"rows": len(mine_all), "evaluated": sum(1 for r in mine_all if r["evaluated"]), "primary": len(mine_prim),
                                         "matched_sets": len(mine_prim) // 2, "programs": prog(mine_prim), "changed": sum(r["label"] for r in mine_prim)},
            "ref": {"rows": ref["n_rows"], "primary": ref["n_primary"], "programs": ref["n_programs"]}, "diffs": diffs}


def main():
    res = {}
    allr, prim = L.build_v10()
    keys = ["sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction", "call_count", "n_functions", "coverage_size", "static_token", "static_ast", "sbg_v6", "sbg_state_v6"]
    res["v10_test"] = compare("v10_test", allr, prim, keys)
    pids = {p["pair_id"] for p in prim}
    res["v10_test"]["waterfall"] = {"dataset_rows": len(allr), "evaluated": sum(1 for r in allr if r["evaluated"]),
                                    "unevaluated_pair_ids": [r["pair_id"] for r in allr if not r["evaluated"]],
                                    "evaluated_but_dropped_by_matching_rule": [r["pair_id"] for r in allr if r["evaluated"] and r["pair_id"] not in pids], "primary": len(prim)}
    k9 = ["sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction", "call_count", "n_functions", "coverage_size", "static_token", "static_ast"]
    for split in ("val", "dev", "train"):
        allr9, prim9 = L.build_v9c(split)
        res[f"v9c_{split}"] = compare(f"v9c_{split}", allr9, prim9, k9)
        pids = {p["pair_id"] for p in prim9}
        res[f"v9c_{split}"]["waterfall"] = {"rows_after_stale_exclusion": len(allr9), "evaluated": sum(1 for r in allr9 if r["evaluated"]),
                                            "valid": sum(1 for r in allr9 if r["_valid"]), "primary": len(prim9),
                                            "unevaluated": [(r["pair_id"], r.get("failure_kind")) for r in allr9 if not r["evaluated"]],
                                            "dropped_by_matching": [r["pair_id"] for r in allr9 if r["_valid"] and r["pair_id"] not in pids]}
    all8, prim8 = L.build_v8_test()
    res["v8_test"] = {"rows_after_stale_exclusion": len(all8), "evaluated": sum(1 for r in all8 if r["evaluated"]), "valid": len(prim8),
                      "programs": len({r["base_id"] for r in prim8}), "changed": sum(r["label"] for r in prim8),
                      "unevaluated": [(r["pair_id"], r.get("failure_kind")) for r in all8 if not r["evaluated"]]}
    (OUT / "raw" / "EXP-A3-001" / "population_reconstruction.json").write_text(json.dumps(res, indent=1, default=str))
    for k, v in res.items():
        if "diffs" in v:
            d = v["diffs"]
            print(k, v["mine"], "ref", v["ref"], "| only_mine", len(d["primary_only_mine"]), "only_ref", len(d["primary_only_ref"]), "label_mm", len(d["label_mismatch"]),
                  "group_mm", len(d["group_mismatch"]), "edit_mm", len(d["edit_mismatch"]), "max score diff", max(d["score_max_abs_diff"].values()))
            print("   waterfall", v["waterfall"])
        else:
            print(k, v)


if __name__ == "__main__":
    main()
