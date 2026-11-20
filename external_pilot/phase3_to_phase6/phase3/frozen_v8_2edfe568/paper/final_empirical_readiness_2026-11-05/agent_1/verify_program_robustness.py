#!/usr/bin/env python3
"""Final-sprint Agent 1: independent re-derivation of V10 program-robustness numbers.

Read-only on the repo. Own AUROC / win-loss / LOPO / within-between code (does NOT import the previous-sprint
program_robustness.py or sbg.statistics.auroc). Only reuses frozen helpers to *load* the frozen population
(evaluate_v9 loaders, _edit_size, frozen V10 linear models) exactly as the frozen evaluator does.

Run:  PYTHONDONTWRITEBYTECODE=1 python3 verify_program_robustness.py
Writes: verification_v10.json, verification_v10_checks.csv (this directory only).
"""
import sys
sys.dont_write_bytecode = True
import collections, csv, json, math, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
PREV = REPO / "paper/empirical_sprint_2026-11-04/agent_2"
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "experiments/final"))
import evaluate_v9 as e                         # frozen helpers (import only)
from edit_size_analysis import _edit_size       # noqa

# ---------------- own statistics ----------------
def auc(pos, neg):
    """P(pos>neg)+0.5P(tie); O(n log n) rank-based."""
    allv = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    ranks = {}
    i = 0
    n = len(allv)
    rk = [0.0] * n
    while i < n:
        j = i
        while j + 1 < n and allv[j + 1][0] == allv[i][0]:
            j += 1
        for k in range(i, j + 1):
            rk[k] = (i + j) / 2 + 1
        i = j + 1
    rs = sum(rk[k] for k in range(n) if allv[k][1] == 1)
    return (rs - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))

def A(rows, key):
    return auc([r[key] for r in rows if r["label"] == 1], [r[key] for r in rows if r["label"] == 0])

def sign_p(w, l):
    n = w + l; k = min(w, l)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)

# ---------------- load frozen V10 population ----------------
V10 = REPO / "benchmark/datasets/v10_independent"
models = json.loads((REPO / "artifacts/final/V10_MODELS_FROZEN.json").read_text())["models"]
meta = {m["pair_id"]: m for m in e.jl(V10 / "pairs_test.jsonl")}
scored = {r["pair_id"]: r for r in e.jl(REPO / "artifacts/final/pairs_v10_test_v6exp.jsonl")}
ev = []
for pid, m in meta.items():
    r = scored[pid]
    if not r["evaluated"]:
        continue
    sc = dict(r["scores"])
    sc["edit"] = float(_edit_size(m["base_path"], m["variant_path"]))
    ev.append({"pair_id": pid, "prog": m["base_id"], "label": int(m["semantic_relation"] == "CHANGED"),
               "group": pid if m["semantic_relation"] == "EQUIVALENT" else m["matched_pair_id"], "sc": sc, "tt": m["transformation_type"]})
g = collections.defaultdict(list)
for r in ev: g[r["group"]].append(r)
pop = [x for v in g.values() if len(v) == 2 and {y["label"] for y in v} == {0, 1} for x in v]
for r in pop:
    r["v5"] = r["sc"]["sbg_v5"]; r["edit"] = r["sc"]["edit"]
    mm = models["EX"]; r["mex"] = e.lin_score(mm, mm["features"], r["sc"])
progs = sorted({r["prog"] for r in pop})
out = {"n_pairs": len(pop), "n_sets": len(pop) // 2, "n_programs": len(progs)}

# ---------------- pooled ----------------
pooled = {k: A(pop, k) for k in ("v5", "edit", "mex")}
out["pooled"] = {k: round(v, 6) for k, v in pooled.items()}

# ---------------- per-program AUROC, sample sizes ----------------
per = {}
for p in progs:
    rs = [r for r in pop if r["prog"] == p]
    per[p] = {"n_pairs": len(rs), "n_chg": sum(r["label"] for r in rs), "n_eq": sum(1 - r["label"] for r in rs),
              **{k: A(rs, k) for k in ("v5", "edit", "mex")}}
out["per_program"] = {p: {k: (round(v, 6) if isinstance(v, float) else v) for k, v in d.items()} for p, d in per.items()}

# ---------------- win / loss ----------------
def wl(a, b):
    d = [per[p][a] - per[p][b] for p in progs]
    w = sum(x > 1e-12 for x in d); l = sum(x < -1e-12 for x in d)
    return {"wins": w, "losses": l, "ties": len(d) - w - l, "mean_diff": round(sum(d) / len(d), 6),
            "median_diff": round(sorted(d)[len(d) // 2], 6), "sign_test_p": sign_p(w, l)}
out["win_loss"] = {"V5_vs_edit": wl("v5", "edit"), "V5_vs_MEX": wl("v5", "mex")}
rng = random.Random(42)
for nm, (a, b) in {"V5_vs_edit": ("v5", "edit"), "V5_vs_MEX": ("v5", "mex")}.items():
    d = [per[p][a] - per[p][b] for p in progs]
    bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(5000))
    out["win_loss"][nm]["program_bootstrap_ci95_mean_diff"] = [round(bs[int(.025 * 5000)], 4), round(bs[int(.975 * 5000)], 4)]
out["win_loss"]["V5_vs_MEX"]["sign_test_note"] = "Not significant at 0.05; no multiplicity claim"

# ---------------- LOPO ----------------
lo = {}
for k in ("v5", "edit", "mex"):
    vals = {p: A([r for r in pop if r["prog"] != p], k) for p in progs}
    lo[k] = {"min": [round(min(vals.values()), 6), min(vals, key=vals.get)], "max": [round(max(vals.values()), 6), max(vals, key=vals.get)]}
dv5e = [A([r for r in pop if r["prog"] != p], "v5") - A([r for r in pop if r["prog"] != p], "edit") for p in progs]
dv5m = [A([r for r in pop if r["prog"] != p], "v5") - A([r for r in pop if r["prog"] != p], "mex") for p in progs]
lo["delta_v5_edit_range"] = [round(min(dv5e), 6), round(max(dv5e), 6)]
lo["delta_v5_mex_range"] = [round(min(dv5m), 6), round(max(dv5m), 6)]
out["lopo"] = lo

# ---------------- within / between ----------------
def concord(key):
    ch = [r for r in pop if r["label"] == 1]; eq = [r for r in pop if r["label"] == 0]
    w = [0.0, 0]; b = [0.0, 0]
    for c in ch:
        for q in eq:
            s = 1.0 if c[key] > q[key] else 0.5 if c[key] == q[key] else 0.0
            t = w if c["prog"] == q["prog"] else b
            t[0] += s; t[1] += 1
    tot = w[1] + b[1]
    return {"n_cross": tot, "within_n": w[1], "between_n": b[1], "within_share": round(w[1] / tot, 6),
            "between_share": round(b[1] / tot, 6), "within_conc": round(w[0] / w[1], 6), "between_conc": round(b[0] / b[1], 6),
            "pooled_check": round((w[0] + b[0]) / tot, 6),
            "within_contrib": round(w[0] / tot, 6), "between_contrib": round(b[0] / tot, 6)}
out["within_between"] = {k: concord(k) for k in ("v5", "edit", "mex")}

# between-program signal is attributable to what? (descriptive) per-program mean V5 on CHANGED vs EQUIVALENT
mean_by = {p: (sum(r["v5"] for r in pop if r["prog"] == p and r["label"] == 1) / per[p]["n_chg"],
               sum(r["v5"] for r in pop if r["prog"] == p and r["label"] == 0) / per[p]["n_eq"]) for p in progs}
out["program_mean_v5_changed_vs_equivalent"] = {p: [round(a, 4), round(b, 4)] for p, (a, b) in mean_by.items()}

# ---------------- cluster-bootstrap pooled CI (own, 4000 resamples of programs) ----------------
rng = random.Random(7)
byp = {p: [r for r in pop if r["prog"] == p] for p in progs}
def boot(fn, B=1500):
    vs = []
    for _ in range(B):
        rs = [x for p in (rng.choice(progs) for _ in progs) for x in byp[p]]
        if {r["label"] for r in rs} == {0, 1}:
            vs.append(fn(rs))
    vs.sort(); return [round(vs[int(.025 * len(vs))], 4), round(vs[int(.975 * len(vs))], 4)], len(vs)
out["pooled_cluster_bootstrap_ci95"] = {"v5": boot(lambda r: A(r, "v5"))[0],
    "v5_minus_edit": boot(lambda r: A(r, "v5") - A(r, "edit"))[0],
    "v5_minus_mex": boot(lambda r: A(r, "v5") - A(r, "mex"))[0]}
(HERE / "verification_v10.json").write_text(json.dumps(out, indent=1))

# ---------------- compare to previous-sprint outputs ----------------
prev = json.loads((PREV / "results_v10.json").read_text())
rows = []
def chk(name, mine, theirs, tol=1.5e-6):
    ok = abs(mine - theirs) <= tol
    rows.append([name, mine, theirs, "OK" if ok else "MISMATCH"])
for k, kk in (("V5", "v5"), ("edit", "edit"), ("M_EX", "mex")):
    chk(f"pooled_{k}", pooled[kk], prev["pooled_auroc"][k])
for pp in prev["per_program"]:
    for k, kk in (("V5", "v5"), ("edit", "edit"), ("M_EX", "mex")):
        chk(f"per_program/{pp['program']}/{k}", per[pp["program"]][kk], pp[k])
for nm in ("V5_vs_edit", "V5_vs_MEX"):
    o = out["win_loss"][nm]; pr = prev["win_loss"][nm]
    chk(f"wl/{nm}/wins", o["wins"], pr["a_gt_b"], 0); chk(f"wl/{nm}/losses", o["losses"], pr["a_lt_b"], 0)
    chk(f"wl/{nm}/mean_diff", o["mean_diff"], pr["mean_per_program_diff"]); chk(f"wl/{nm}/sign_p", o["sign_test_p"], pr["sign_test_two_sided_p_exact"], 1e-6)
pl = prev["lopo"]
chk("lopo/V5/min", lo["v5"]["min"][0], pl["V5"]["min"][0]); chk("lopo/V5/max", lo["v5"]["max"][0], pl["V5"]["max"][0])
chk("lopo/edit/min", lo["edit"]["min"][0], pl["edit"]["min"][0]); chk("lopo/edit/max", lo["edit"]["max"][0], pl["edit"]["max"][0])
chk("lopo/M_EX/min", lo["mex"]["min"][0], pl["M_EX"]["min"][0]); chk("lopo/M_EX/max", lo["mex"]["max"][0], pl["M_EX"]["max"][0])
pw = prev["concentration"]["V5"]
chk("wb/V5/within_n", out["within_between"]["v5"]["within_n"], pw["within_program"]["n_pairs"], 0)
chk("wb/V5/between_n", out["within_between"]["v5"]["between_n"], pw["between_program"]["n_pairs"], 0)
chk("wb/V5/within_conc", out["within_between"]["v5"]["within_conc"], pw["within_program"]["concordance"])
chk("wb/V5/between_conc", out["within_between"]["v5"]["between_conc"], pw["between_program"]["concordance"])
chk("wb/V5/between_share", out["within_between"]["v5"]["between_share"], pw["between_program"]["share_of_all_cross_pairs"])
with open(HERE / "verification_v10_checks.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["check", "recomputed_now", "previous_sprint", "status"]); w.writerows(rows)
print("checks:", len(rows), "mismatch:", sum(r[3] != "OK" for r in rows))
print(json.dumps({k: out[k] for k in ("pooled", "win_loss", "lopo", "within_between", "pooled_cluster_bootstrap_ci95")}, indent=1))
