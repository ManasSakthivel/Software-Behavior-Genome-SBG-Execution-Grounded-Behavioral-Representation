#!/usr/bin/env python3
"""POST-HOC, DESCRIPTIVE supplement to V10_INDEPENDENT_EVALUATION.json (computed AFTER the single frozen run; not in the Holm family; no decision depends on it).

Adds: SBG V5 vs the strongest execution baselines (coverage_size, M_X, M_EX), matched-set concordance with the edit-minus-SBG gap, performance on the
oracle-observable-by-design caveat (what fraction of CHANGED pairs score exactly 0), and AUROC restricted to EQUIVALENT families that are not pure renames.
Reads only the scored file + frozen models; does not modify any frozen artifact.   PYTHONHASHSEED=0 python experiments/final/posthoc_v10_supplement.py
"""
import collections, json, pathlib, sys
REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "experiments" / "final"))
import evaluate_v9 as e                                                                # noqa: E402
import evaluate_v10 as v                                                               # noqa: E402
from edit_size_analysis import _edit_size                                              # noqa: E402
from static_baselines import token_multiset, ast_multiset, multiset_distance           # noqa: E402
from sbg.statistics import auroc                                                       # noqa: E402


def main():
    mf = json.loads(v.MODELS.read_text())["models"]
    meta = {m["pair_id"]: m for m in e.jl(v.V10 / "pairs_test.jsonl")}
    rows = []
    for r in e.jl(v.SCORED):
        if not r["evaluated"]:
            continue
        m = meta[r["pair_id"]]
        sc = dict(r["scores"]); sc["sbg_v6"] = r["sbg_v6"]; sc["edit"] = float(_edit_size(m["base_path"], m["variant_path"]))
        bs, vs = (REPO / m["base_path"]).read_text(), (REPO / m["variant_path"]).read_text()
        sc["static_token"] = multiset_distance(token_multiset(bs), token_multiset(vs)); sc["static_ast"] = multiset_distance(ast_multiset(bs), ast_multiset(vs))
        rows.append({"label": int(m["semantic_relation"] == "CHANGED"), "base_id": m["base_id"], "scores": sc, "tt": m["transformation_type"],
                     "group": m["pair_id"] if m["semantic_relation"] == "EQUIVALENT" else m["matched_pair_id"]})
    g = collections.defaultdict(list)
    for r in rows:
        g[r["group"]].append(r)
    pop = [x for a in g.values() if len(a) == 2 for x in a]
    for r in pop:
        for n, mm in mf.items():
            r["scores"][f"M_{n}"] = e.lin_score(mm, mm["features"], r["scores"])
    D = lambda a, b: e.delta(e.vec(pop, a), e.vec(pop, b))                             # noqa: E731
    out = {"artifact": "V10_POSTHOC_SUPPLEMENT", "status": "POST-HOC / DESCRIPTIVE (computed after the frozen single run; exploratory)", "n_pairs": len(pop),
           "deltas": {k: D(*p) for k, p in {"V5_minus_coverage_size": ("sbg_v5", "coverage_size"), "V5_minus_M_X": ("sbg_v5", "M_X"), "V5_minus_M_EX": ("sbg_v5", "M_EX"),
                                            "V5_minus_M_EX+V5": ("sbg_v5", "M_EX+V5")}.items()}}
    # matched-set concordance paired difference (edit - sbg_v5)
    sets = collections.defaultdict(dict)
    for r in pop:
        sets[r["group"]][r["label"]] = r
    def conc(p):
        return [(s[1]["base_id"], 1.0 if s[1]["scores"][p] > s[0]["scores"][p] else .5 if s[1]["scores"][p] == s[0]["scores"][p] else 0.0) for s in sets.values()]
    import random
    ce, cs = conc("edit"), conc("sbg_v5")
    by = collections.defaultdict(list)
    for (b, x), (_, y) in zip(ce, cs):
        by[b].append(x - y)
    ks, rng, vals = sorted(by), random.Random(42), []
    for _ in range(2000):
        s = [c for k in (rng.choice(ks) for _ in ks) for c in by[k]]
        vals.append(sum(s) / len(s))
    vals.sort()
    out["matched_concordance_edit_minus_sbg_v5"] = {"delta": round(sum(x - y for (_, x), (_, y) in zip(ce, cs)) / len(ce), 6), "ci95": [round(vals[50], 6), round(vals[1949], 6)]}
    # fraction of matched sets in which CHANGED has the strictly larger edit
    out["fraction_sets_changed_edit_gt_equivalent_edit"] = round(sum(1 for s in sets.values() if s[1]["scores"]["edit"] > s[0]["scores"]["edit"]) / len(sets), 4)
    out["fraction_sets_sbg_v5_changed_gt_equivalent"] = round(sum(1 for s in sets.values() if s[1]["scores"]["sbg_v5"] > s[0]["scores"]["sbg_v5"]) / len(sets), 4)
    # pooled AUROC with the pure-rename EQUIVALENT families removed (SP-1, SP-2, SP-4, SP-6, SP-12): hardest negatives only
    hard = {"SP-3", "SP-5", "SP-8", "SP-11"}
    keep = [r for r in pop if r["label"] == 0 and r["tt"] in hard]
    kg = {r["group"] for r in keep}
    sub = [r for r in pop if r["group"] in kg]
    s, y, c = e.vec(sub, "sbg_v5")
    se, _, _ = e.vec(sub, "edit")
    sc_, _, _ = e.vec(sub, "coverage_size")
    out["rewrite_only_equivalents_SP3_SP5_SP8_SP11"] = {"n_pairs": len(sub), "n_sets": len(sub) // 2, "auroc_sbg_v5": round(auroc(s, y), 4), "ci95": e.ci(s, y, c),
                                                         "auroc_edit_forward": round(auroc(se, y), 4), "auroc_coverage_size": round(auroc(sc_, y), 4)}
    ren = [r for r in pop if r["label"] == 0 and r["tt"] not in hard]
    rg = {r["group"] for r in ren}
    sub = [r for r in pop if r["group"] in rg]
    s, y, c = e.vec(sub, "sbg_v5")
    se, _, _ = e.vec(sub, "edit")
    out["rename_style_equivalents_SP1_SP2_SP4_SP6_SP12"] = {"n_pairs": len(sub), "n_sets": len(sub) // 2, "auroc_sbg_v5": round(auroc(s, y), 4), "ci95": e.ci(s, y, c), "auroc_edit_forward": round(auroc(se, y), 4)}
    (v.EV / "V10_POSTHOC_SUPPLEMENT.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
