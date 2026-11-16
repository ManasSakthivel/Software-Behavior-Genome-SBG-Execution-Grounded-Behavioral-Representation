#!/usr/bin/env python3
"""EXP-A3-004b: label-conflicting pairs (CHANGED variant with the SAME normalised AST as an EQUIVALENT variant) and de-duplication
sensitivity of the headline numbers (post-hoc, exploratory; the frozen analysis is NOT altered).
  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a3_004b_dedup_sensitivity.py
"""
import ast
import collections
import csv
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L  # noqa: E402

RAW = L.PKG / "results" / "raw" / "EXP-A3-004"
TAB = L.PKG / "results" / "tables"


def ahash(path):
    return hashlib.sha256(ast.dump(ast.parse((L.REPO / path).read_text())).encode()).hexdigest()


def load(name):
    if name == "v10_test":
        _, pop = L.build_v10()
        mf = json.loads((L.ART / "V10_MODELS_FROZEN.json").read_text())["models"]
        meta = {m["pair_id"]: m for m in L.jl(L.V10D / "pairs_test.jsonl")}
        eq_of = lambda r: meta[r["pair_id"]]["matched_pair_id"]   # noqa: E731
    else:
        _, pop = L.build_v9c("val")
        mf = json.loads((L.ART / "V9_MODELS_FROZEN.json").read_text())["models"]
        meta = {m["pair_id"]: m for m in L.jl(L.V9D / "pairs_val.jsonl")}
        eq_of = lambda r: meta[r["pair_id"]]["matched_equivalent_pair_id"]  # noqa: E731
    for r in pop:
        for n, m in mf.items():
            r["scores"][f"M_{n}"] = L.lin_score({"features": m["features"], **m}, r["scores"])
        r["ast"] = ahash(r["variant_path"])
    byid = {r["pair_id"]: r for r in pop}
    eq_ast_prog = collections.defaultdict(set)
    for r in pop:
        if r["label"] == 0:
            eq_ast_prog[r["base_id"]].add(r["ast"])
    for r in pop:
        r["conflict_partner"] = bool(r["label"] == 1 and byid[eq_of(r)]["ast"] == r["ast"])
        r["conflict_any"] = bool(r["label"] == 1 and r["ast"] in eq_ast_prog[r["base_id"]])
    return pop


def stats(pop, preds, tag, plan):
    y = [r["label"] for r in pop]
    c = [r["base_id"] for r in pop]
    out = {"tag": tag, "n": len(pop), "n_programs": len(set(c)), "n_changed": sum(y)}
    for p in preds:
        s = [r["scores"][p] for r in pop]
        out[p] = round(L.auroc(s, y), 4)
        out[p + "_ci"] = L.boot_ci(s, y, c, plan=plan)[:2]
    return out


def main():
    res, rows_out = {}, []
    for name in ("v10_test", "v9c_val"):
        pop = load(name)
        preds = ["sbg_v5", "sbg_state", "edit", "coverage_size", "M_EX"] + (["M_EX+V5", "M_E+V5"] if name == "v10_test" else ["M_ESX", "M_ES"])
        # group-level duplicate structure
        g = collections.Counter((r["base_id"], r["label"], r["ast"]) for r in pop)
        for r in pop:
            r["dupsize"] = g[(r["base_id"], r["label"], r["ast"])]
        n_conf_p = sum(r["conflict_partner"] for r in pop)
        n_conf_a = sum(r["conflict_any"] for r in pop)
        info = {"n_primary": len(pop), "ch_identical_AST_to_own_EQ_partner": n_conf_p, "ch_identical_AST_to_any_EQ_variant_same_program": n_conf_a,
                "rows_in_dup_AST_groups(label,program)": sum(1 for r in pop if r["dupsize"] > 1), "distinct_(program,label,AST)": len(g),
                "ch_conflict_by_sc": dict(collections.Counter(r["sc_type"] for r in pop if r["conflict_any"])),
                "ch_conflict_by_sp": dict(collections.Counter(r["sp_type"] for r in pop if r["conflict_any"])),
                "conflict_pairs_v5_scores": sorted({round(r["scores"]["sbg_v5"], 4) for r in pop if r["conflict_partner"]})[:10],
                "conflict_by_program": dict(collections.Counter(r["base_id"] for r in pop if r["conflict_any"]))}
        plan = L.resample_plan(len({r["base_id"] for r in pop}))
        variants = {"A_primary_as_reported": pop}
        bad_groups = {r["group"] for r in pop if r["conflict_any"]}
        variants["B_drop_label_conflicting_sets(CH==some EQ AST)"] = [r for r in pop if r["group"] not in bad_groups]
        seen, ded = set(), []
        for r in pop:
            k = (r["base_id"], r["label"], r["ast"])
            if k not in seen:
                seen.add(k)
                ded.append(r)
        variants["C_dedup_rows_(program,label,AST)"] = ded
        seen, ded2 = set(), []
        for r in variants["B_drop_label_conflicting_sets(CH==some EQ AST)"]:
            k = (r["base_id"], r["label"], r["ast"])
            if k not in seen:
                seen.add(k)
                ded2.append(r)
        variants["D_B_then_dedup"] = ded2
        tbl = []
        for tag, pp in variants.items():
            st = stats(pp, preds, tag, plan)
            tbl.append(st)
            rows_out.append({"design": name, **{k: (str(v) if isinstance(v, list) else v) for k, v in st.items()}})
        res[name] = {"info": info, "variants": tbl}
        print(name, json.dumps(info)[:600])
        for st in tbl:
            print("  ", st["tag"], "n", st["n"], {p: st[p] for p in preds})
    (RAW / "dedup_sensitivity.json").write_text(json.dumps(res, indent=1, default=str))
    keys = sorted({k for r in rows_out for k in r})
    with open(TAB / "EXP-A3-004b_dedup_sensitivity.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows_out)


if __name__ == "__main__":
    main()
