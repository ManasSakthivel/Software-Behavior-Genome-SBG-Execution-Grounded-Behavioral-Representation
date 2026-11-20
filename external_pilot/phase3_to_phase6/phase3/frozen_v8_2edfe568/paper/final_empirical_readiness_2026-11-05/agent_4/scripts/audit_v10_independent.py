#!/usr/bin/env python3
"""Agent 4 (auditor): independent recomputation of V10 headline / robustness / ablation numbers.

Own loaders, own tie-aware AUROC (rank based, no import of sbg.statistics / evaluate_*), own bootstrap.
Read-only on the repo. Writes only tables/v10_audit.json in the agent_4 directory.
Run: PYTHONDONTWRITEBYTECODE=1 ../../../../../venvs/py313/bin/python audit_v10_independent.py   (py3.13.5: ast.unparse edit-size)
"""
import sys
sys.dont_write_bytecode = True
import ast, collections, difflib, json, math, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
OUT = HERE.parent / "tables"
OUT.mkdir(exist_ok=True)


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def auc(pos, neg):
    """Mann-Whitney with mid-rank ties (identical definition: P(p>n)+0.5P(p=n))."""
    vals = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg], key=lambda t: t[0])
    n = len(vals); rk = [0.0] * n; i = 0
    while i < n:
        j = i
        while j + 1 < n and vals[j + 1][0] == vals[i][0]:
            j += 1
        for k in range(i, j + 1):
            rk[k] = (i + j) / 2 + 1
        i = j + 1
    rs = sum(rk[k] for k in range(n) if vals[k][1])
    return (rs - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def A(rows, key):
    return auc([r[key] for r in rows if r["label"] == 1], [r[key] for r in rows if r["label"] == 0])


def edit_size(bp, vp):
    a = ast.unparse(ast.parse((REPO / bp).read_text())).splitlines()
    b = ast.unparse(ast.parse((REPO / vp).read_text())).splitlines()
    return sum(1 for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---"))


def lin(m, sc):
    z = m["bias"]
    for j, f in enumerate(m["features"]):
        z += m["weights_standardised"][j] * ((sc[f] - m["feature_means"][j]) / m["feature_stds"][j])
    return round(z, 9)


V10 = REPO / "benchmark/datasets/v10_independent"
models = json.loads((REPO / "artifacts/final/V10_MODELS_FROZEN.json").read_text())["models"]
meta = {m["pair_id"]: m for m in jl(V10 / "pairs_test.jsonl")}
scored = {r["pair_id"]: r for r in jl(REPO / "artifacts/final/pairs_v10_test_v6exp.jsonl")}
res = {"n_dataset_rows": len(meta), "n_scored_rows": len(scored),
       "n_unevaluated": sum(1 for r in scored.values() if not r["evaluated"]),
       "unevaluated_ids": [p for p, r in scored.items() if not r["evaluated"]]}
ev = []
for pid, m in meta.items():
    r = scored[pid]
    if not r["evaluated"]:
        continue
    sc = dict(r["scores"]); sc["edit"] = float(edit_size(m["base_path"], m["variant_path"]))
    ev.append({"pid": pid, "prog": m["base_id"], "label": int(m["semantic_relation"] == "CHANGED"),
               "grp": pid if m["semantic_relation"] == "EQUIVALENT" else m["matched_pair_id"],
               "tt": m["transformation_type"], "sc": sc, "v6": r["sbg_v6"], "sv6": r["sbg_state_v6"]})
res["n_evaluated_rows"] = len(ev)
g = collections.defaultdict(list)
for r in ev:
    g[r["grp"]].append(r)
pop = [x for v in g.values() if len(v) == 2 and {y["label"] for y in v} == {0, 1} for x in v]
res["n_pop"] = len(pop); res["n_sets"] = len(pop) // 2
res["n_programs"] = len({r["prog"] for r in pop})
res["n_chg"] = sum(r["label"] for r in pop); res["n_eq"] = len(pop) - res["n_chg"]
# which evaluated rows were dropped by matching
inpop = {r["pid"] for r in pop}
res["dropped_by_matching"] = [r["pid"] for r in ev if r["pid"] not in inpop]
for r in pop:
    s = r["sc"]
    r.update(v5=s["sbg_v5"], v3=s["sbg_v3"], tmp=s["sbg_temporal"], st=s["sbg_state"], edit=s["edit"],
             exc=s["exception_fraction"], cc=s["call_count"], cov=s["coverage_size"])
    r["mex"] = lin(models["EX"], s)
    r["editrev"] = -s["edit"]
    r["me_v5"] = lin(models["E+V5"], s); r["me"] = lin(models["E"], s)
    r["mexv5"] = lin(models["EX+V5"], {**s})
    r["w_no_v3"] = 0.25 * r["tmp"] + 0.25 * r["st"]
    r["w_no_tmp"] = 0.5 * r["v3"] + 0.25 * r["st"]
    r["w_no_st"] = 0.5 * r["v3"] + 0.25 * r["tmp"]
    r["v5_recomp"] = 0.5 * r["v3"] + 0.25 * r["tmp"] + 0.25 * r["st"]
    r["v6"] = r["v6"]
res["v5_formula_max_abs_diff"] = max(abs(r["v5_recomp"] - r["v5"]) for r in pop)
progs = sorted({r["prog"] for r in pop})
keys = ["v5", "edit", "editrev", "mex", "mexv5", "me", "me_v5", "v3", "tmp", "st", "w_no_v3", "w_no_tmp", "w_no_st", "exc", "cc", "cov", "v6"]
res["pooled"] = {k: round(A(pop, k), 6) for k in keys}
res["zero_rate"] = {"all": sum(r["v5"] == 0 for r in pop) / len(pop),
                    "chg": sum(r["v5"] == 0 for r in pop if r["label"]) / res["n_chg"],
                    "eq": sum(r["v5"] == 0 for r in pop if not r["label"]) / res["n_eq"]}
# per program
per = {}
for p in progs:
    rs = [r for r in pop if r["prog"] == p]
    per[p] = {"n": len(rs), "nch": sum(r["label"] for r in rs), **{k: A(rs, k) for k in ("v5", "edit", "mex", "st", "w_no_st", "w_no_tmp", "w_no_v3", "v3", "tmp")}}
res["per_program"] = {p: {k: round(v, 6) if isinstance(v, float) else v for k, v in d.items()} for p, d in per.items()}
vv = [per[p]["v5"] for p in progs]
res["per_program_v5_summary"] = {"min": min(vv), "max": max(vv), "mean": sum(vv) / len(vv), "median": sorted(vv)[len(vv) // 2],
                                 "n_lt_0.80": sum(v < 0.80 for v in vv)}


def sign_p(w, l):
    n = w + l; k = min(w, l)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def wl(a, b):
    d = [per[p][a] - per[p][b] for p in progs]
    w = sum(x > 1e-12 for x in d); l = sum(x < -1e-12 for x in d)
    return {"wins": w, "losses": l, "ties": len(d) - w - l, "mean": sum(d) / len(d), "sign_p": sign_p(w, l)}


res["winloss"] = {"v5_vs_edit": wl("v5", "edit"), "v5_vs_mex": wl("v5", "mex"), "state_vs_v5": wl("st", "v5"),
                  "v5_vs_noState": wl("v5", "w_no_st")}
# LOPO
lo = {}
for k in ("v5", "edit", "mex"):
    v = {p: A([r for r in pop if r["prog"] != p], k) for p in progs}
    lo[k] = [min(v.values()), max(v.values())]
res["lopo"] = lo
# Matched-set concordance with ties=.5
sets = collections.defaultdict(dict)
for r in pop:
    sets[r["grp"]]["ch" if r["label"] else "eq"] = r
sets = list(sets.values())


def conc(k):
    s = [(1.0 if x["ch"][k] > x["eq"][k] else 0.5 if x["ch"][k] == x["eq"][k] else 0.0) for x in sets]
    c = sum(1 for x in sets if x["ch"][k] > x["eq"][k]); t = sum(1 for x in sets if x["ch"][k] == x["eq"][k])
    return {"conc": sum(s) / len(s), "correct": c, "ties": t, "wrong": len(s) - c - t}


res["matched_concordance"] = {k: conc(k) for k in ("v5", "edit", "mex", "st", "v3", "tmp", "exc")}
res["matched_edit_diff"] = {"mean": sum(x["ch"]["edit"] - x["eq"]["edit"] for x in sets) / len(sets),
                            "frac_ch_edit_gt_eq": sum(x["ch"]["edit"] > x["eq"]["edit"] for x in sets) / len(sets)}
# edit-size stratified
ch = [r for r in pop if r["label"]]; eq = [r for r in pop if not r["label"]]
num = den = 0.0
for c in ch:
    for q in eq:
        if c["edit"] == q["edit"]:
            den += 1; num += 1.0 if c["v5"] > q["v5"] else 0.5 if c["v5"] == q["v5"] else 0.0
res["edit_exact_stratified_v5"] = {"auc": num / den, "n": den}
# within / between
w = [0.0, 0]; b = [0.0, 0]
for c in ch:
    for q in eq:
        s = 1.0 if c["v5"] > q["v5"] else 0.5 if c["v5"] == q["v5"] else 0.0
        t = w if c["prog"] == q["prog"] else b
        t[0] += s; t[1] += 1
res["within_between_v5"] = {"within_n": w[1], "between_n": b[1], "within_conc": w[0] / w[1], "between_conc": b[0] / b[1],
                            "between_share": b[1] / (w[1] + b[1]), "n_total": w[1] + b[1]}
# SC-6
sc6 = [r for r in pop if r["tt"].startswith("SC-6") or r["tt"] == "SC-6"]
res["tt_values_sample"] = sorted({r["tt"] for r in pop})
sc6 = [r for r in pop if r["tt"].startswith("SC-6+")]
res["SC6"] = {"n": len(sc6), "zero": sum(r["v5"] == 0 for r in sc6)}
rest_eq = [r for r in pop if r["label"] == 0]
rng_pop = [r for r in pop if r["label"] == 0 or r["tt"].startswith("SC-6+")]
res["SC6"]["auroc_vs_all_eq"] = A(rng_pop, "v5")

# own cluster bootstrap (program resampling), paired, seed different from library (7), B=4000
byp = {p: [r for r in pop if r["prog"] == p] for p in progs}
rng = random.Random(7)
B = 3000
dist = collections.defaultdict(list)
cmp_keys = {"v5": lambda rs: A(rs, "v5"), "edit": lambda rs: A(rs, "edit"), "mex": lambda rs: A(rs, "mex"),
            "mexv5": lambda rs: A(rs, "mexv5"), "st": lambda rs: A(rs, "st"), "me": lambda rs: A(rs, "me"), "me_v5": lambda rs: A(rs, "me_v5"),
            "w_no_st": lambda rs: A(rs, "w_no_st"), "w_no_tmp": lambda rs: A(rs, "w_no_tmp"), "w_no_v3": lambda rs: A(rs, "w_no_v3")}
for _ in range(B):
    rs = [x for p in (rng.choice(progs) for _ in progs) for x in byp[p]]
    if {r["label"] for r in rs} != {0, 1}:
        continue
    vals = {k: f(rs) for k, f in cmp_keys.items()}
    for k, v in vals.items():
        dist[k].append(v)
    dist["v5-edit"].append(vals["v5"] - vals["edit"]); dist["v5-mex"].append(vals["v5"] - vals["mex"])
    dist["mexv5-mex"].append(vals["mexv5"] - vals["mex"]); dist["me_v5-me"].append(vals["me_v5"] - vals["me"])
    dist["v5-st"].append(vals["v5"] - vals["st"]); dist["v5-w_no_st"].append(vals["v5"] - vals["w_no_st"])
    dist["v5-w_no_tmp"].append(vals["v5"] - vals["w_no_tmp"]); dist["v5-w_no_v3"].append(vals["v5"] - vals["w_no_v3"])


def pct(v):
    v = sorted(v); n = len(v)
    return [round(v[int(.025 * n)], 4), round(v[min(n - 1, int(math.ceil(.975 * n)) - 1)], 4)]


res["boot_ci"] = {k: pct(v) for k, v in dist.items()}
res["boot_ci_neff"] = len(dist["v5"])
# point deltas
P = res["pooled"]
res["deltas"] = {"v5-edit": P["v5"] - P["edit"], "v5-mex": P["v5"] - P["mex"], "mexv5-mex": P["mexv5"] - P["mex"],
                 "me_v5-me": P["me_v5"] - P["me"], "v5-st": P["v5"] - P["st"], "v5-w_no_st": P["v5"] - P["w_no_st"],
                 "v5-w_no_tmp": P["v5"] - P["w_no_tmp"], "v5-w_no_v3": P["v5"] - P["w_no_v3"]}
# a 'pair-level (iid) bootstrap' of V5 AUROC to show how naive CI would look (diagnostic of anti-conservativeness)
rng2 = random.Random(11)
naive = []
for _ in range(500):
    rs = [pop[rng2.randrange(len(pop))] for _ in pop]
    naive.append(A(rs, "v5"))
res["naive_pair_bootstrap_v5_ci"] = pct(naive)
# program-level analysis of "state-only beats V5": per-program difference sign
res["program_state_minus_v5"] = {"pos": res["winloss"]["state_vs_v5"]["wins"], "neg": res["winloss"]["state_vs_v5"]["losses"]}
(OUT / "v10_audit.json").write_text(json.dumps(res, indent=1, default=float))
print(json.dumps({k: res[k] for k in res if k not in ("per_program", "unevaluated_ids", "tt_values_sample", "dropped_by_matching")}, indent=1, default=float))
print("dropped", res["dropped_by_matching"], "unevaluated", res["unevaluated_ids"])
