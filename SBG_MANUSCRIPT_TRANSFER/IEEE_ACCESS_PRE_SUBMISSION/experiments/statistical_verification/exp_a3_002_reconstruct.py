#!/usr/bin/env python3
"""EXP-A3-002: independent reconstruction of every reported V10-test, V9c-val and V8-test number from raw files, with
digit-level comparison to the reported result JSONs.  Pure stdlib, imports only a3lib (own code).

  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a3_002_reconstruct.py [v10|v9c_val|v8_test|all]
Outputs: results/raw/EXP-A3-002/<design>_reconstruction.json ; results/tables/EXP-A3-002_<design>_comparison.csv
"""
import csv
import json
import multiprocessing as mp
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L  # noqa: E402

RAW = L.PKG / "results" / "raw" / "EXP-A3-002"
TAB = L.PKG / "results" / "tables"
RAW.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)
G = {}


def _auroc_ci(pred):
    s, y, c = L.vec(G["pop"], pred)
    return pred, L.boot_ci(s, y, c, plan=G["plan"])


def _delta(job):
    name, a, b = job
    sa, y, c = L.vec(G["pop"], a)
    sb = L.vec(G["pop"], b)[0]
    return name, L.paired_delta(sa, sb, y, c, plan=G["plan"])


def _pool(fn, jobs, nproc=4):
    with mp.get_context("fork").Pool(nproc) as p:
        return p.map(fn, jobs)


class Cmp:
    def __init__(self):
        self.rows = []

    def add(self, name, mine, ref, tol=None):
        if mine is None or ref is None:
            d = None if (mine is None and ref is None) else float("inf")
        else:
            d = abs(float(mine) - float(ref))
        self.rows.append({"quantity": name, "independent": mine, "reported": ref, "abs_diff": d})

    def write(self, path):
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["quantity", "independent", "reported", "abs_diff"])
            w.writeheader()
            w.writerows(self.rows)

    def max_diff(self, prefix=""):
        v = [r["abs_diff"] for r in self.rows if r["abs_diff"] is not None and r["quantity"].startswith(prefix)]
        return max(v) if v else None


def run_v10():
    t0 = time.time()
    allr, pop = L.build_v10()
    rep = json.loads((L.EV / "V10_INDEPENDENT_EVALUATION.json").read_text())
    mf = json.loads((L.ART / "V10_MODELS_FROZEN.json").read_text())
    models, thr = mf["models"], mf["thresholds_youden_train"]
    for r in pop:
        r["scores"]["edit_reversed"] = -r["scores"]["edit"]
        for n, m in models.items():
            r["scores"][f"M_{n}"] = L.lin_score({"features": m["features"], **m}, r["scores"])
    G["pop"] = pop
    y = [r["label"] for r in pop]
    G["plan"] = L.resample_plan(len({r["base_id"] for r in pop}))
    single = ["sbg_v5", "sbg_v6", "sbg_state", "sbg_state_v6", "edit", "exception_fraction", "call_count", "coverage_size", "static_ast", "static_token"]
    preds = single + ["edit_reversed"] + [f"M_{n}" for n in models]
    cmp = Cmp()
    cis = dict(_pool(_auroc_ci, preds))
    out = {"design": "v10_test", "n_rows": len(allr), "n_pairs": len(pop), "n_sets": len(pop) // 2, "n_programs": len({r["base_id"] for r in pop}), "n_changed": sum(y), "predictors": {}}
    for k, v in (("n_pairs_in_dataset", len(allr)), ("n_unevaluated", sum(1 for r in allr if not r["evaluated"])), ("n_pairs", len(pop)), ("n_matched_sets", len(pop) // 2),
                 ("n_programs", out["n_programs"]), ("n_changed", sum(y)), ("n_equivalent", len(y) - sum(y))):
        cmp.add(k, v, rep[k])
    pc = {p: sum(1 for r in pop if r["base_id"] == p) for p in sorted({r["base_id"] for r in pop})}
    cmp.add("per_program_counts_max_abs_diff", max(abs(pc[p] - rep["per_program_counts"][p]) for p in pc), 0)
    for lab, name in ((1, "CHANGED"), (0, "EQUIVALENT")):
        cmp.add(f"mean_edit.{name}", round(sum(r["edit"] for r in pop if r["label"] == lab) / sum(1 for r in pop if r["label"] == lab), 3), rep["mean_edit"][name])
    for p in preds:
        s = [r["scores"][p] for r in pop]
        P, N = sum(y), len(y) - sum(y)
        a, ci = L.auroc(s, y), cis[p]
        d = {"auroc": a, "ci95": [ci[0], ci[1]], "pr_auc": L.auprc(s, y)}
        if p in thr:
            t = thr[p]
            d["sens"] = sum(1 for a_, b in zip(s, y) if b and a_ >= t) / P
            d["spec"] = sum(1 for a_, b in zip(s, y) if not b and a_ < t) / N
            d["prf_at_frozen_thr"] = L.prf_at(s, y, t)
        d["zero_rate"] = sum(1 for v in s if v == 0) / len(s)
        out["predictors"][p] = d
        R = rep["predictors"][p]
        cmp.add(f"{p}.auroc", round(a, 6), R["auroc"])
        cmp.add(f"{p}.ci_lo", ci[0], R["ci95_cluster_bootstrap"][0])
        cmp.add(f"{p}.ci_hi", ci[1], R["ci95_cluster_bootstrap"][1])
        cmp.add(f"{p}.pr_auc", round(d["pr_auc"], 6), R["pr_auc"])
        if p in thr:
            cmp.add(f"{p}.sens", round(d["sens"], 4), R["sensitivity"])
            cmp.add(f"{p}.spec", round(d["spec"], 4), R["specificity"])
        cmp.add(f"{p}.exact_zero_rate", round(d["zero_rate"], 4), R["exact_zero_rate"])
    sv = [r["scores"]["sbg_v5"] for r in pop]
    c = [r["base_id"] for r in pop]
    pp = L.perm_p(sv, y, c)
    out["H1_perm_p"] = pp
    cmp.add("H1.permutation_p", round(pp, 6), rep["predictors"]["sbg_v5"]["permutation_p_one_sided_vs_0.5"])
    jobs = [("H2_E+V5_minus_E", "M_E+V5", "M_E"), ("H3_V5_minus_edit_forward", "sbg_v5", "edit"), ("H4_EX+V5_minus_EX", "M_EX+V5", "M_EX"),
            ("H5_V6_minus_V5", "sbg_v6", "sbg_v5"), ("H6_EX+V6_minus_EX", "M_EX+V6", "M_EX")]
    sup = [("V5_minus_edit_reversed", "sbg_v5", "edit_reversed"), ("V5_minus_exception_fraction", "sbg_v5", "exception_fraction"), ("V5_minus_static_ast", "sbg_v5", "static_ast"),
           ("V5_minus_static_token", "sbg_v5", "static_token"), ("EX_minus_E", "M_EX", "M_E"), ("state_V6_minus_state_V5", "sbg_state_v6", "sbg_state"),
           ("E+V6_minus_E", "M_E+V6", "M_E"), ("EX+V6_minus_EX+V5", "M_EX+V6", "M_EX+V5"),
           ("V5_minus_state (extra)", "sbg_v5", "sbg_state"), ("V5_minus_M_EX (extra)", "sbg_v5", "M_EX"), ("V5_minus_coverage_size (extra)", "sbg_v5", "coverage_size"),
           ("state_minus_M_EX (extra)", "sbg_state", "M_EX")]
    dl = dict(_pool(_delta, jobs + sup))
    out["deltas"] = dl
    for name, _, _ in jobs + sup:
        if "(extra)" in name:
            continue
        sect = rep["pre_declared_tests"]["deltas"] if name in rep["pre_declared_tests"]["deltas"] else rep["supplementary_deltas_not_in_holm_family"]
        R = sect[name]
        for k, kk in (("delta", "delta"), ("ci_lower", "ci_lower"), ("ci_upper", "ci_upper"), ("p_two_sided", "p_two_sided")):
            cmp.add(f"{name}.{k}", dl[name][kk], R[k])
    ps = {"H1_sbg_v5_above_chance": round(pp, 6), **{k: dl[k]["p_two_sided"] for k, _, _ in jobs}}
    hm = L.holm(ps)
    out["holm"] = hm
    for k, v in hm.items():
        cmp.add(f"holm.{k}.p_adjusted", v["p_adjusted"], rep["pre_declared_tests"]["holm"][k]["p_adjusted"])
    out["strat"] = {p: dict(zip(("auroc", "n_cross"), L.exact_edit_stratified(pop, lambda r, p=p: r["scores"][p]))) for p in ("sbg_v5", "sbg_v6", "edit")}
    for p, v in out["strat"].items():
        cmp.add(f"strat.{p}.auroc", v["auroc"], rep["edit_size_exact_stratified"][p]["auroc"])
        cmp.add(f"strat.{p}.n_cross", v["n_cross"], rep["edit_size_exact_stratified"][p]["n_cross_label_comparisons"])
    out["concordance"] = {p: L.matched_concordance(pop, lambda r, p=p: r["scores"][p]) for p in ("sbg_v5", "sbg_v6", "edit", "exception_fraction")}
    for p, v in out["concordance"].items():
        R = rep["matched_set_concordance"][p]
        cmp.add(f"concordance.{p}.value", v["concordance"], R["concordance"])
        cmp.add(f"concordance.{p}.ci_lo", v["ci95"][0], R["ci95_cluster_bootstrap"][0])
        cmp.add(f"concordance.{p}.ci_hi", v["ci95"][1], R["ci95_cluster_bootstrap"][1])
    per = {}
    for p in sorted({r["base_id"] for r in pop}):
        ps_ = [r for r in pop if r["base_id"] == p]
        yy = [r["label"] for r in ps_]
        per[p] = {"n": len(ps_), **{k: round(L.auroc([r["scores"][k] for r in ps_], yy), 4) for k in ("sbg_v5", "sbg_v6", "edit", "M_EX")}}
        for k in ("sbg_v5", "sbg_v6", "edit", "M_EX"):
            cmp.add(f"per_program.{p}.{k}", per[p][k], rep["per_program_auroc"][p][k])
    out["per_program"] = per
    # AUROC differences between posthoc reported deltas and point AUROC differences
    out["runtime_s"] = time.time() - t0
    (RAW / "v10_test_reconstruction.json").write_text(json.dumps(out, indent=1))
    cmp.write(TAB / "EXP-A3-002_v10_test_comparison.csv")
    print("V10: compared", len(cmp.rows), "quantities; max |diff| =", cmp.max_diff(), "; time", round(out["runtime_s"], 1))
    worst = sorted([r for r in cmp.rows if r["abs_diff"]], key=lambda r: -r["abs_diff"])[:8]
    for r in worst:
        print("   ", r)
    return out


def run_v9c_val():
    t0 = time.time()
    allr, pop = L.build_v9c("val")
    rep = json.loads((L.EV / "V9_VAL_EVALUATION.json").read_text())["v9c_matched"]
    models = json.loads((L.ART / "V9_MODELS_FROZEN.json").read_text())["models"]
    for r in pop:
        for n, m in models.items():
            r["scores"][f"M_{n}"] = L.lin_score({"features": m["features"], **m}, r["scores"])
        r["scores"]["edit_reversed"] = -r["scores"]["edit"]
    G["pop"] = pop
    y = [r["label"] for r in pop]
    G["plan"] = L.resample_plan(len({r["base_id"] for r in pop}))
    single = ["sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction", "call_count", "coverage_size", "static_ast", "static_token"]
    preds = single + [f"M_{n}" for n in models] + ["edit", "edit_reversed"]
    cis = dict(_pool(_auroc_ci, preds))
    cmp = Cmp()
    out = {"design": "v9c_val", "n_pairs": len(pop), "n_programs": len({r["base_id"] for r in pop}), "predictors": {}}
    for k in ("n_pairs", "n_matched_sets", "n_programs", "n_changed", "n_equivalent"):
        mine = {"n_pairs": len(pop), "n_matched_sets": len(pop) // 2, "n_programs": out["n_programs"], "n_changed": sum(y), "n_equivalent": len(y) - sum(y)}[k]
        cmp.add(k, mine, rep[k])
    for p in preds:
        s = [r["scores"][p] for r in pop]
        a, ci = L.auroc(s, y), cis[p]
        out["predictors"][p] = {"auroc": a, "ci95": [ci[0], ci[1]], "auprc": L.auprc(s, y)}
        cmp.add(f"{p}.auroc", round(a, 6), rep["predictors"][p]["auroc"])
        cmp.add(f"{p}.ci_lo", ci[0], rep["predictors"][p]["ci95_cluster_bootstrap"][0])
        cmp.add(f"{p}.ci_hi", ci[1], rep["predictors"][p]["ci95_cluster_bootstrap"][1])
    sv = [r["scores"]["sbg_v5"] for r in pop]
    c = [r["base_id"] for r in pop]
    pp = L.perm_p(sv, y, c)
    out["H1_perm_p"] = pp
    cmp.add("H1.permutation_p", round(pp, 6), rep["predictors"]["sbg_v5"]["permutation_p_one_sided_vs_0.5"])
    H = [("H2", "M_ES", "M_E"), ("H3", "sbg_v5", "edit"), ("H4", "M_ESX", "M_EX")]
    sec = [(f"sbg_v5_minus_{p}", "sbg_v5", p) for p in ("sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction", "call_count", "coverage_size", "static_ast", "static_token", "edit")]
    comp = [(f"comp_{m}", f"M_{m}", "M_E") for m in ("E+v3", "E+temporal", "E+state", "ES")]
    extra = [("V5_minus_M_EX (extra)", "sbg_v5", "M_EX"), ("state_minus_M_EX (extra)", "sbg_state", "M_EX")]
    dl = dict(_pool(_delta, H + sec + comp + extra))
    out["deltas"] = dl
    for h, _, _ in H:
        for k in ("delta", "ci_lower", "ci_upper", "p_two_sided"):
            cmp.add(f"{h}.{k}", dl[h][k], rep["pre_declared_tests"][h][k])
    for name, _, _ in sec:
        for k in ("delta", "ci_lower", "ci_upper", "p_two_sided"):
            cmp.add(f"{name}.{k}", dl[name][k], rep["paired_deltas_sbg_v5_minus"][name.replace("sbg_v5_minus_", "")][k])
    for name, _, _ in comp:
        for k in ("delta", "ci_lower", "ci_upper", "p_two_sided"):
            cmp.add(f"{name}.{k}", dl[name][k], rep["component_increments_over_edit_only_model"][name.replace("comp_", "")][k])
    ps = {"H1_sbg_v5_above_chance": round(pp, 6), "H2_edit_plus_sbg_minus_edit": dl["H2"]["p_two_sided"], "H3_sbg_v5_minus_edit_forward": dl["H3"]["p_two_sided"],
          "H4_edit_exec_plus_sbg_minus_edit_exec": dl["H4"]["p_two_sided"]}
    hm = L.holm(ps)
    out["holm"] = hm
    for k, v in hm.items():
        cmp.add(f"holm.{k}.p_adjusted", v["p_adjusted"], rep["pre_declared_tests"]["holm"][k]["p_adjusted"])
    hb = L.holm({n.replace("sbg_v5_minus_", ""): dl[n]["p_two_sided"] for n, _, _ in sec if n.replace("sbg_v5_minus_", "") in ("exception_fraction", "call_count", "coverage_size", "static_ast", "static_token", "edit")})
    for k, v in hb.items():
        cmp.add(f"holm_baselines.{k}.p_adjusted", v["p_adjusted"], rep["paired_deltas_holm_over_baselines"][k]["p_adjusted"])
    out["strat"] = {p: dict(zip(("auroc", "n_cross"), L.exact_edit_stratified(pop, lambda r, p=p: r["scores"][p]))) for p in ("sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state")}
    for p, v in out["strat"].items():
        cmp.add(f"strat.{p}.auroc", v["auroc"], rep["edit_size_exact_stratified"][p]["auroc"])
        cmp.add(f"strat.{p}.n_cross", v["n_cross"], rep["edit_size_exact_stratified"][p]["n_cross_label_comparisons"])
    out["concordance"] = {p: L.matched_concordance(pop, lambda r, p=p: r["scores"][p]) for p in ("sbg_v5", "edit", "sbg_state", "exception_fraction")}
    for p, v in out["concordance"].items():
        R = rep["matched_set_concordance"][p]
        cmp.add(f"concordance.{p}.value", v["concordance"], R["concordance"])
        cmp.add(f"concordance.{p}.ci_lo", v["ci95"][0], R["ci95_cluster_bootstrap"][0])
        cmp.add(f"concordance.{p}.ci_hi", v["ci95"][1], R["ci95_cluster_bootstrap"][1])
    for lab, name in ((1, "CHANGED"), (0, "EQUIVALENT")):
        cmp.add(f"mean_edit.{name}", round(sum(r["edit"] for r in pop if r["label"] == lab) / sum(1 for r in pop if r["label"] == lab), 3), rep["mean_edit_size"][name])
    cmp.add("fraction_sbg_v5_exactly_zero", round(sum(1 for r in pop if r["scores"]["sbg_v5"] == 0) / len(pop), 4), rep["fraction_sbg_v5_exactly_zero"])
    per = {}
    for p in sorted({r["base_id"] for r in pop}):
        ps_ = [r for r in pop if r["base_id"] == p]
        yy = [r["label"] for r in ps_]
        per[p] = {"n": len(ps_), **{k: round(L.auroc([r["scores"][k] for r in ps_], yy), 4) for k in ("sbg_v5", "edit")}}
        for k in ("sbg_v5", "edit"):
            cmp.add(f"per_program.{p}.{k}", per[p][k], rep["per_program_auroc"][p][k])
    out["per_program"] = per
    out["runtime_s"] = time.time() - t0
    (RAW / "v9c_val_reconstruction.json").write_text(json.dumps(out, indent=1))
    cmp.write(TAB / "EXP-A3-002_v9c_val_comparison.csv")
    print("V9c-val: compared", len(cmp.rows), "quantities; max |diff| =", cmp.max_diff(), "; time", round(out["runtime_s"], 1))
    for r in sorted([r for r in cmp.rows if r["abs_diff"]], key=lambda r: -r["abs_diff"])[:8]:
        print("   ", r)
    return out


def run_v8_test():
    t0 = time.time()
    allr, pop = L.build_v8_test()
    rep = json.loads((L.EV / "V8_TEST_EVALUATION.json").read_text())["VALID"]
    G["pop"] = pop
    G["plan"] = L.resample_plan(len({r["base_id"] for r in pop}))
    y = [r["label"] for r in pop]
    preds = ["sbg_v5", "edit_size_reversed", "exception_fraction", "call_count", "coverage_size", "static_ast", "static_token"]
    cis = dict(_pool(_auroc_ci, preds))
    cmp = Cmp()
    out = {"design": "v8_test", "n_pairs": len(pop), "n_programs": len({r["base_id"] for r in pop}), "predictors": {}}
    cmp.add("n_pairs", len(pop), rep["n_pairs"])
    cmp.add("n_changed", sum(y), rep["n_changed"])
    cmp.add("n_programs", out["n_programs"], rep["n_programs"])
    for p in preds:
        s = [r["scores"][p] for r in pop]
        a, ci = L.auroc(s, y), cis[p]
        out["predictors"][p] = {"auroc": a, "ci95": [ci[0], ci[1]], "auprc": L.auprc(s, y)}
        cmp.add(f"{p}.auroc", round(a, 6), rep["predictors"][p]["auroc"])
        cmp.add(f"{p}.ci_lo", ci[0], rep["predictors"][p]["ci95_cluster_bootstrap"][0])
        cmp.add(f"{p}.ci_hi", ci[1], rep["predictors"][p]["ci95_cluster_bootstrap"][1])
    sv = [r["scores"]["sbg_v5"] for r in pop]
    c = [r["base_id"] for r in pop]
    pp = L.perm_p(sv, y, c)
    cmp.add("sbg_v5.permutation_p", round(pp, 6), rep["predictors"]["sbg_v5"]["permutation_p_one_sided"])
    dl = dict(_pool(_delta, [("sbg_v5_minus_edit_size_reversed", "sbg_v5", "edit_size_reversed")]))
    for k in ("delta", "ci_lower", "ci_upper", "p_two_sided"):
        cmp.add(f"sbg_v5_minus_edit_size_reversed.{k}", dl["sbg_v5_minus_edit_size_reversed"][k], rep["paired_deltas"]["sbg_v5_minus_edit_size_reversed"][k])
    st = L.exact_edit_stratified(pop, lambda r: r["scores"]["sbg_v5"])
    cmp.add("strat.sbg_v5", st[0], rep["edit_size_exact_stratified"]["sbg_v5_auroc"])
    cmp.add("strat.n_cross", st[1], rep["edit_size_exact_stratified"]["n_cross_label_comparisons"])
    for lab, name in ((1, "changed"), (0, "equivalent")):
        cmp.add(f"mean_edit.{name}", round(sum(r["edit"] for r in pop if r["label"] == lab) / sum(1 for r in pop if r["label"] == lab), 3), rep["mean_edit_size"][name])
    out["deltas"] = dl
    out["H1_perm_p"] = pp
    out["runtime_s"] = time.time() - t0
    (RAW / "v8_test_reconstruction.json").write_text(json.dumps(out, indent=1))
    cmp.write(TAB / "EXP-A3-002_v8_test_comparison.csv")
    print("V8-test: compared", len(cmp.rows), "quantities; max |diff| =", cmp.max_diff(), "; time", round(out["runtime_s"], 1))
    for r in sorted([r for r in cmp.rows if r["abs_diff"]], key=lambda r: -r["abs_diff"])[:8]:
        print("   ", r)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("v10", "all"):
        run_v10()
    if which in ("v9c_val", "all"):
        run_v9c_val()
    if which in ("v8_test", "all"):
        run_v8_test()
