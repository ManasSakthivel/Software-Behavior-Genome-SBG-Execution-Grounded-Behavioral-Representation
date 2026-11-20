#!/usr/bin/env python3
"""AGENT 2 -- per-program robustness and concentration (POST-HOC, EXPLORATORY).

Read-only on the repo: loads frozen scored files / frozen models, applies the frozen models in memory exactly as
experiments/final/evaluate_v10.py (stage_run) and evaluate_v9.py (run --split val) do, and never refits, rescoring,
or writes outside this directory.

    cd <repo>/paper/empirical_sprint_2026-11-04/agent_2
    PYTHONDONTWRITEBYTECODE=1 <venv>/bin/python program_robustness.py

Outputs (this directory): results_v10.json, results_v9cval.json, *.csv tables, inputs_sha256.json
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True

import ast
import collections
import csv
import hashlib
import itertools
import json
import math
import pathlib
import random

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
assert (REPO / "sbg" / "statistics.py").exists(), REPO
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments" / "final"))
import evaluate_v9 as e                                                   # noqa: E402  (frozen eval helpers, import only)
import evaluate_v4_dev as d4                                              # noqa: E402
from edit_size_analysis import _edit_size                                 # noqa: E402
from static_baselines import token_multiset, ast_multiset, multiset_distance   # noqa: E402
from sbg.statistics import auroc                                          # noqa: E402

SEED, B = 42, 2000
OUT = HERE


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def r6(x):
    return None if x is None else round(x, 6)


# --------------------------------------------------------------------------------------------------------------
# population reconstruction (read-only copies of the frozen logic)
# --------------------------------------------------------------------------------------------------------------
def build_v10():
    V10 = REPO / "benchmark" / "datasets" / "v10_independent"
    mf = json.loads((REPO / "artifacts/final/V10_MODELS_FROZEN.json").read_text())
    models = mf["models"]
    meta = {m["pair_id"]: m for m in e.jl(V10 / "pairs_test.jsonl")}
    scored = {r["pair_id"]: r for r in e.jl(REPO / "artifacts/final/pairs_v10_test_v6exp.jsonl")}
    rows, cache = [], {}
    for pid, m in meta.items():
        r = scored[pid]
        if not r["evaluated"]:
            rows.append({"pair_id": pid, "evaluated": False, "base_id": m["base_id"], "failure": r.get("failure")})
            continue
        sc = dict(r["scores"])
        sc["sbg_v6"], sc["sbg_state_v6"] = r["sbg_v6"], r["sbg_state_v6"]
        sc["edit"] = float(_edit_size(m["base_path"], m["variant_path"]))
        for pth in (m["base_path"], m["variant_path"]):
            if pth not in cache:
                src = (REPO / pth).read_text()
                cache[pth] = (token_multiset(src), ast_multiset(src))
        sc["static_token"] = multiset_distance(cache[m["base_path"]][0], cache[m["variant_path"]][0])
        sc["static_ast"] = multiset_distance(cache[m["base_path"]][1], cache[m["variant_path"]][1])
        rows.append({"pair_id": pid, "evaluated": True, "base_id": m["base_id"], "label": int(m["semantic_relation"] == "CHANGED"),
                     "group": m["pair_id"] if m["semantic_relation"] == "EQUIVALENT" else m["matched_pair_id"],
                     "transformation_type": m["transformation_type"], "base_path": m["base_path"], "_edit": int(sc["edit"]), "scores": sc})
    ok = collections.defaultdict(list)
    for r in rows:
        if r["evaluated"]:
            ok[r["group"]].append(r)
    pop = [x for g in ok.values() if len(g) == 2 and {y["label"] for y in g} == {0, 1} for x in g]
    for r in pop:
        r["scores"]["edit_reversed"] = -r["scores"]["edit"]
        for n, m in models.items():
            r["scores"][f"M_{n}"] = e.lin_score(m, m["features"], r["scores"])
    unevaluated = [(r["pair_id"], r.get("failure")) for r in rows if not r["evaluated"]]
    return pop, unevaluated, meta


def build_v9cval():
    models = json.loads((REPO / "artifacts/final/V9_MODELS_FROZEN.json").read_text())["models"]
    rows = e.load("v9c", "val")
    pop = e.matched_complete(rows)
    e.attach_model_scores(pop, models)
    meta = {m["pair_id"]: m for m in e.jl(e.V9 / "pairs_val.jsonl")}
    meta.update({m["pair_id"]: m for m in e.jl(e.V8 / "pairs_val.jsonl")})
    for r in pop:
        r["base_path"] = meta[r["pair_id"]]["base_path"]
    return pop, [(r["pair_id"], r.get("failure_kind")) for r in rows if not r["evaluated"]], meta


# --------------------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------------------
def category(base_id):
    return base_id.split("_")[0]


def sc_family(tt):
    return tt.split("+")[0] if "+" in tt else None


def sp_family(tt):
    return tt.split("+")[1] if "+" in tt else tt


def au(rows, k):
    return auroc([r["scores"][k] for r in rows], [r["label"] for r in rows])


def sign_test(wins, losses):
    n = wins + losses
    if n == 0:
        return None
    k = min(wins, losses)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def quantiles(v, qs=(0, .05, .25, .5, .75, .95, 1)):
    s = sorted(v)
    out = {}
    for q in qs:
        pos = q * (len(s) - 1)
        lo, hi = int(math.floor(pos)), int(math.ceil(pos))
        out[f"q{int(q * 100):03d}"] = r6(s[lo] + (s[hi] - s[lo]) * (pos - lo))
    return out


def ranks(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    rk = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j < len(o) and v[o[j]] == v[o[i]]:
            j += 1
        for k in range(i, j):
            rk[o[k]] = (i + j + 1) / 2
        i = j
    return rk


def spearman(a, b):
    if len(a) < 3 or len(set(a)) < 2 or len(set(b)) < 2:
        return None
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else None


def write_csv(name, rows, cols=None):
    cols = cols or list(rows[0].keys())
    with open(OUT / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in cols})


def cmat(rows, k):
    """concordance matrix between CHANGED (i) and EQUIVALENT (j) rows for predictor k (1/0.5/0)."""
    ch = [r for r in rows if r["label"] == 1]
    eq = [r for r in rows if r["label"] == 0]
    return ch, eq, [[1.0 if a["scores"][k] > b["scores"][k] else .5 if a["scores"][k] == b["scores"][k] else 0.0 for b in eq] for a in ch]


# --------------------------------------------------------------------------------------------------------------
# the analysis
# --------------------------------------------------------------------------------------------------------------
def analyse(tag, pop, preds, ref, headline, structure_note):
    """preds: display name -> score key.  ref: dict with roles V5, EDIT, MEX, MEXV5 -> display names."""
    progs = sorted({r["base_id"] for r in pop})
    by = {p: [r for r in pop if r["base_id"] == p] for p in progs}
    res = {"tag": tag, "n_pairs": len(pop), "n_sets": len(pop) // 2, "n_programs": len(progs),
           "n_changed": sum(r["label"] for r in pop)}
    res["pooled_auroc"] = {n: r6(au(pop, k)) for n, k in preds.items()}
    res["headline_check"] = {n: {"recomputed": r6(au(pop, preds[n])), "frozen_json": v, "match_1e-6": abs(au(pop, preds[n]) - v) < 1e-6}
                             for n, v in headline.items()}

    # ---- 1. per-program AUROC ------------------------------------------------------------------------------
    pp_rows, missing = [], []
    for p in progs:
        ps = by[p]
        nc = sum(r["label"] for r in ps)
        ne = len(ps) - nc
        row = {"program": p, "category": category(p), "n_pairs": len(ps), "n_sets": len(ps) // 2, "n_changed": nc, "n_equivalent": ne}
        if nc == 0 or ne == 0:
            missing.append(p)
            for n in preds:
                row[n] = None
        else:
            for n, k in preds.items():
                row[n] = r6(au(ps, k))
        pp_rows.append(row)
    res["programs_missing_a_class"] = missing
    write_csv(f"per_program_auroc_{tag}.csv", pp_rows)
    res["per_program"] = pp_rows
    PP = {r["program"]: r for r in pp_rows if r["program"] not in missing}

    # ---- 2. win/loss counts, sign test, cluster bootstrap of mean per-program difference --------------------
    comps = {"V5_vs_edit": (ref["V5"], ref["EDIT"]), "V5_vs_MEX": (ref["V5"], ref["MEX"]), "V5_vs_MEXV5": (ref["V5"], ref["MEXV5"]),
             "MEXV5_vs_MEX": (ref["MEXV5"], ref["MEX"])}
    wl = {}
    rng_progs = sorted(PP)
    for cn, (a, b) in comps.items():
        d = {p: PP[p][a] - PP[p][b] for p in rng_progs}
        win = sum(1 for v in d.values() if v > 0)
        loss = sum(1 for v in d.values() if v < 0)
        tie = len(d) - win - loss
        rng = random.Random(SEED)
        bs = sorted(sum(d[rng.choice(rng_progs)] for _ in rng_progs) / len(rng_progs) for _ in range(B))
        wl[cn] = {"a": a, "b": b, "a_gt_b": win, "a_lt_b": loss, "ties": tie, "sign_test_two_sided_p_exact": r6(sign_test(win, loss)),
                  "mean_per_program_diff": r6(sum(d.values()) / len(d)), "median_per_program_diff": r6(sorted(d.values())[len(d) // 2] if len(d) % 2 else
                                                                                                       sum(sorted(d.values())[len(d) // 2 - 1:len(d) // 2 + 1]) / 2),
                  "cluster_bootstrap_ci95_mean_diff": [r6(bs[int(.025 * B)]), r6(bs[int(.975 * B) - 1])],
                  "min_diff": {"program": min(d, key=d.get), "value": r6(min(d.values()))}, "max_diff": {"program": max(d, key=d.get), "value": r6(max(d.values()))},
                  "per_program_diff": {p: r6(v) for p, v in d.items()}}
    res["win_loss"] = wl
    write_csv(f"per_program_differences_{tag}.csv",
              [{"program": p, **{cn: wl[cn]["per_program_diff"][p] for cn in wl}} for p in rng_progs])

    # ---- 3. concentration: within vs between program concordance --------------------------------------------
    conc = {}
    contrib_rows = {p: {"program": p} for p in progs}
    for n, k in preds.items():
        ch, eq, M = cmat(pop, k)
        N = len(ch) * len(eq)
        C = sum(sum(r) for r in M)
        cp = collections.defaultdict(float)     # cells keyed by (program of CH, program of EQ)
        npair = collections.defaultdict(int)
        for i, a in enumerate(ch):
            for j, b in enumerate(eq):
                cp[(a["base_id"], b["base_id"])] += M[i][j]
                npair[(a["base_id"], b["base_id"])] += 1
        Cw = sum(v for (a, b), v in cp.items() if a == b)
        Nw = sum(v for (a, b), v in npair.items() if a == b)
        Cb, Nb = C - Cw, N - Nw
        # attributed contribution: within cell -> its program; between cell -> half to each of the two programs
        att_c, att_n = collections.defaultdict(float), collections.defaultdict(float)
        for (a, b), v in cp.items():
            if a == b:
                att_c[a] += v
                att_n[a] += npair[(a, b)]
            else:
                for q in (a, b):
                    att_c[q] += .5 * v
                    att_n[q] += .5 * npair[(a, b)]
        excess = {p: att_c[p] - .5 * att_n[p] for p in progs}
        tot_ex = sum(excess.values())
        within_ex = {p: cp[(p, p)] - .5 * npair[(p, p)] for p in progs}
        sh = sorted(((excess[p] / tot_ex, p) for p in progs), reverse=True)
        pw = [npair[(p, p)] / Nw for p in progs]
        conc[n] = {"pooled_auroc": r6(C / N), "n_cross_label_pairs": N,
                   "within_program": {"n_pairs": Nw, "share_of_all_cross_pairs": r6(Nw / N), "concordance": r6(Cw / Nw), "contribution_to_pooled_auroc": r6(Cw / N)},
                   "between_program": {"n_pairs": Nb, "share_of_all_cross_pairs": r6(Nb / N), "concordance": r6(Cb / Nb), "contribution_to_pooled_auroc": r6(Cb / N)},
                   "between_minus_within_concordance": r6(Cb / Nb - Cw / Nw),
                   "unweighted_mean_of_per_program_auroc": r6(sum(PP[p][n] for p in PP) / len(PP)),
                   "pair_weighted_mean_of_per_program_auroc(=within concordance)": r6(Cw / Nw),
                   "attributed_excess_over_chance_share": {p: r6(s) for s, p in sh},
                   "top3_programs_share_of_attributed_excess": r6(sum(s for s, _ in sh[:3])),
                   "top3_programs": [p for _, p in sh[:3]],
                   "effective_n_programs_inverse_HHI_of_excess_shares": r6(1 / sum(s * s for s, _ in sh)),
                   "within_cells_effective_n_programs": r6(1 / sum(w * w for w in pw))}
        for p in progs:
            contrib_rows[p][f"{n}__attr_weight"] = r6(att_n[p] / N)
            contrib_rows[p][f"{n}__attr_contribution"] = r6(att_c[p] / N)
            contrib_rows[p][f"{n}__within_cell_weight"] = r6(npair[(p, p)] / N)
            contrib_rows[p][f"{n}__within_cell_excess_over_chance"] = r6(within_ex[p] / N)
            contrib_rows[p][f"{n}__attr_excess_share"] = r6(excess[p] / tot_ex)
    res["concentration"] = conc
    write_csv(f"per_program_contribution_{tag}.csv", list(contrib_rows.values()))
    # whole-matrix between-program cells for V5
    ch, eq, M = cmat(pop, preds[ref["V5"]] if ref["V5"] in preds else ref["V5"])
    cell = collections.defaultdict(lambda: [0.0, 0])
    for i, a in enumerate(ch):
        for j, b in enumerate(eq):
            cell[(a["base_id"], b["base_id"])][0] += M[i][j]
            cell[(a["base_id"], b["base_id"])][1] += 1
    write_csv(f"v5_program_pair_concordance_{tag}.csv",
              [{"changed_program": a, "equivalent_program": b, "n_pairs": v[1], "concordance": r6(v[0] / v[1])} for (a, b), v in sorted(cell.items())])
    # between-program concordance for V5 by whether CHANGED program's own EQ is the comparison: matrix summary
    # (a) mean concordance when EQ drawn from a different program, by CHANGED program
    bcp = []
    for p in progs:
        num = sum(v[0] for (a, b), v in cell.items() if a == p and b != p)
        den = sum(v[1] for (a, b), v in cell.items() if a == p and b != p)
        num2 = sum(v[0] for (a, b), v in cell.items() if b == p and a != p)
        den2 = sum(v[1] for (a, b), v in cell.items() if b == p and a != p)
        bcp.append({"program": p, "V5_concordance_CH_of_p_vs_EQ_elsewhere": r6(num / den), "V5_concordance_EQ_of_p_vs_CH_elsewhere": r6(num2 / den2),
                    "V5_within_program_concordance": r6(cell[(p, p)][0] / cell[(p, p)][1])})
    write_csv(f"v5_between_vs_within_by_program_{tag}.csv", bcp)
    res["v5_between_vs_within_by_program"] = bcp

    # ---- 4. leave-one-program-out / leave-two-out ------------------------------------------------------------
    full = {n: au(pop, k) for n, k in preds.items()}
    dpairs = {"V5-MEX": (ref["V5"], ref["MEX"]), "V5-edit": (ref["V5"], ref["EDIT"]), "V5-MEXV5": (ref["V5"], ref["MEXV5"])}
    lopo_rows, lopo = [], {}
    for p in progs:
        sub = [r for r in pop if r["base_id"] != p]
        v = {n: au(sub, k) for n, k in preds.items()}
        row = {"dropped": p, "n_pairs_left": len(sub), **{n: r6(v[n]) for n in preds},
               **{f"d_{dn}": r6(v[a] - v[b]) for dn, (a, b) in dpairs.items()},
               **{f"shift_{n}": r6(v[n] - full[n]) for n in (ref["V5"], ref["EDIT"], ref["MEX"], ref["MEXV5"])}}
        lopo_rows.append(row)
    write_csv(f"lopo_{tag}.csv", lopo_rows)
    for n in preds:
        vals = [(r[n], r["dropped"]) for r in lopo_rows]
        lopo[n] = {"full": r6(full[n]), "min": min(vals), "max": max(vals), "range_width": r6(max(vals)[0] - min(vals)[0]),
                   "largest_downward_move_when_dropping": min(vals, key=lambda t: t[0])[1], "largest_upward_move_when_dropping": max(vals, key=lambda t: t[0])[1]}
    for dn, (a, b) in dpairs.items():
        vals = [(r[f"d_{dn}"], r["dropped"]) for r in lopo_rows]
        lopo[f"delta_{dn}"] = {"full": r6(full[a] - full[b]), "min": min(vals), "max": max(vals), "n_dropped_sets_with_delta_gt0": sum(1 for v, _ in vals if v > 0),
                               "n_dropped_sets_with_delta_lt0": sum(1 for v, _ in vals if v < 0)}
    res["lopo"] = lopo
    # leave-two-out
    l2_rows = []
    for p, q in itertools.combinations(progs, 2):
        sub = [r for r in pop if r["base_id"] not in (p, q)]
        v = {n: au(sub, k) for n, k in preds.items()}
        l2_rows.append({"dropped": f"{p} + {q}", **{n: r6(v[n]) for n in preds}, **{f"d_{dn}": r6(v[a] - v[b]) for dn, (a, b) in dpairs.items()}})
    write_csv(f"leave_two_out_{tag}.csv", l2_rows)
    l2 = {}
    for n in preds:
        lo = min(l2_rows, key=lambda r: r[n])
        hi = max(l2_rows, key=lambda r: r[n])
        l2[n] = {"n_subsets": len(l2_rows), "min": [lo[n], lo["dropped"]], "max": [hi[n], hi["dropped"]]}
    for dn in dpairs:
        lo = min(l2_rows, key=lambda r: r[f"d_{dn}"])
        hi = max(l2_rows, key=lambda r: r[f"d_{dn}"])
        l2[f"delta_{dn}"] = {"min": [lo[f"d_{dn}"], lo["dropped"]], "max": [hi[f"d_{dn}"], hi["dropped"]],
                             "n_subsets_delta_gt0": sum(1 for r in l2_rows if r[f"d_{dn}"] > 0), "n_subsets_delta_lt0": sum(1 for r in l2_rows if r[f"d_{dn}"] < 0)}
    res["leave_two_out"] = l2
    # pooled paired cluster-bootstrap deltas (repo implementation, B=2000, seed 42)
    res["pooled_delta_cluster_bootstrap"] = {}
    for dn, (a, b) in {**dpairs, "MEXV5-MEX": (ref["MEXV5"], ref["MEX"])}.items():
        res["pooled_delta_cluster_bootstrap"][dn] = e.delta(e.vec(pop, preds[a]), e.vec(pop, preds[b]))

    # ---- 5. matched-set paired differences ------------------------------------------------------------------
    g = collections.defaultdict(dict)
    for r in pop:
        g[r["group"]][r["label"]] = r
    sets = [(k, v[1], v[0]) for k, v in g.items() if 0 in v and 1 in v]
    assert len(sets) == len(pop) // 2
    ms = {}
    set_rows = [{"group": k, "program": c["base_id"], "sc_family": sc_family(c["transformation_type"]), "sp_family": sp_family(e_["transformation_type"]),
                 "edit_changed": c["_edit"], "edit_equivalent": e_["_edit"]} for k, c, e_ in sets]
    for n, k in preds.items():
        d = [c["scores"][k] - e_["scores"][k] for _, c, e_ in sets]
        for sr, v in zip(set_rows, d):
            sr[f"diff_{n}"] = r6(v)
        pos, zer, neg = sum(1 for v in d if v > 0), sum(1 for v in d if v == 0), sum(1 for v in d if v < 0)
        mc = e.matched_concordance(pop, k)
        ms[n] = {"n_sets": len(d), "frac_correct_strict(CH>EQ)": r6(pos / len(d)), "frac_exact_tie": r6(zer / len(d)), "frac_wrong(CH<EQ)": r6(neg / len(d)),
                 "n_correct": pos, "n_tie": zer, "n_wrong": neg, "concordance_ties_half": mc["concordance"], "ci95_cluster_bootstrap": mc["ci95_cluster_bootstrap"],
                 "diff_quantiles": quantiles(d), "diff_mean": r6(sum(d) / len(d)),
                 "n_programs_with_all_sets_correct": sum(1 for p in progs if all(c["scores"][k] > e_["scores"][k] for _, c, e_ in sets if c["base_id"] == p)),
                 "per_program_concordance": {p: r6(sum(1.0 if c["scores"][k] > e_["scores"][k] else .5 if c["scores"][k] == e_["scores"][k] else 0.0
                                                       for _, c, e_ in sets if c["base_id"] == p) / sum(1 for _, c, _e in sets if c["base_id"] == p)) for p in progs}}
    res["matched_set"] = ms
    write_csv(f"matched_set_diffs_{tag}.csv", set_rows)
    write_csv(f"matched_set_per_program_concordance_{tag}.csv",
              [{"program": p, "n_sets": sum(1 for _, c, _e in sets if c["base_id"] == p), **{n: ms[n]["per_program_concordance"][p] for n in preds}} for p in progs])

    # ---- 6. failure characterisation ---------------------------------------------------------------------------
    srcs, struct = {}, {}
    for p in progs:
        bp = by[p][0]["base_path"]
        tree = ast.parse((REPO / bp).read_text())
        struct[p] = {"base_loc": len(ast.unparse(tree).splitlines()),
                     "base_n_funcdefs": sum(isinstance(n_, (ast.FunctionDef, ast.AsyncFunctionDef)) for n_ in ast.walk(tree)),
                     "base_n_call_nodes": sum(isinstance(n_, ast.Call) for n_ in ast.walk(tree)),
                     "base_n_loops": sum(isinstance(n_, (ast.For, ast.While)) for n_ in ast.walk(tree)),
                     "base_n_branches": sum(isinstance(n_, ast.If) for n_ in ast.walk(tree))}
    fr = []
    for p in progs:
        ps = by[p]
        ch = [r for r in ps if r["label"] == 1]
        eq = [r for r in ps if r["label"] == 0]
        v5 = lambda r: r["scores"]["sbg_v5"]                                       # noqa: E731
        M = [[1.0 if a["scores"]["sbg_v5"] > b["scores"]["sbg_v5"] else .5 if a["scores"]["sbg_v5"] == b["scores"]["sbg_v5"] else 0.0 for b in eq] for a in ch]
        npair = len(ch) * len(eq)
        strict_wrong = sum(1 for row in M for x in row if x == 0.0)
        tie_all = sum(1 for row in M for x in row if x == .5)
        tie_both0 = sum(1 for a in ch for b in eq if v5(a) == v5(b) == 0)
        row = {"program": p, "category": category(p), "V5_auroc": PP[p]["V5"] if "V5" in PP[p] else r6(au(ps, "sbg_v5")), "n_sets": len(ch),
               "edit_mean_changed": r6(sum(r["_edit"] for r in ch) / len(ch)), "edit_mean_equivalent": r6(sum(r["_edit"] for r in eq) / len(eq)),
               "v5_zero_share_all": r6(sum(1 for r in ps if v5(r) == 0) / len(ps)),
               "v5_zero_share_changed": r6(sum(1 for r in ch if v5(r) == 0) / len(ch)),
               "v5_zero_share_equivalent": r6(sum(1 for r in eq if v5(r) == 0) / len(eq)),
               "v5_median_changed": r6(sorted(map(v5, ch))[len(ch) // 2]), "v5_median_equivalent": r6(sorted(map(v5, eq))[len(eq) // 2]),
               "v5_max_equivalent": r6(max(map(v5, eq))),
               "frac_cross_pairs_strictly_wrong": r6(strict_wrong / npair), "frac_cross_pairs_tied": r6(tie_all / npair), "frac_cross_pairs_tied_both_zero": r6(tie_both0 / npair),
               **struct[p]}
        fr.append(row)
    fr.sort(key=lambda r: r["V5_auroc"])
    write_csv(f"failure_characterisation_{tag}.csv", fr)
    res["failure_characterisation"] = fr
    # correlation of program-level V5 AUROC with candidate structural/score descriptors (descriptive, n = programs)
    desc = ["edit_mean_changed", "edit_mean_equivalent", "v5_zero_share_changed", "v5_zero_share_equivalent", "v5_median_equivalent", "v5_max_equivalent",
            "base_loc", "base_n_funcdefs", "base_n_call_nodes", "base_n_loops", "base_n_branches", "n_sets", "frac_cross_pairs_tied_both_zero"]
    res["spearman_v5_auroc_vs_descriptor_n_programs"] = {d: r6(spearman([r["V5_auroc"] for r in fr], [r[d] for r in fr])) for d in desc}
    cat = collections.defaultdict(list)
    for r in fr:
        cat[r["category"]].append(r["V5_auroc"])
    res["v5_auroc_by_category_of_program"] = {c: {"n_programs": len(v), "mean": r6(sum(v) / len(v)), "min": r6(min(v)), "max": r6(max(v))} for c, v in sorted(cat.items())}
    catpool = {}
    for c in sorted(cat):
        sub = [r for r in pop if category(r["base_id"]) == c]
        catpool[c] = {"n_pairs": len(sub), **{n: r6(au(sub, k)) for n, k in preds.items()}}
    res["pooled_auroc_by_category"] = catpool
    # zero rates by SC family (CHANGED) and SP family (CHANGED's SP part and EQUIVALENT)
    def zr(rows_):
        return {"n": len(rows_), "v5_zero_rate": r6(sum(1 for r in rows_ if r["scores"]["sbg_v5"] == 0) / len(rows_)) if rows_ else None,
                "v5_median": r6(sorted(r["scores"]["sbg_v5"] for r in rows_)[len(rows_) // 2]) if rows_ else None}
    chg = [r for r in pop if r["label"] == 1]
    eqv = [r for r in pop if r["label"] == 0]
    res["zero_rate_changed_by_sc_family"] = {k: zr([r for r in chg if sc_family(r["transformation_type"]) == k]) for k in sorted({sc_family(r["transformation_type"]) for r in chg})}
    res["zero_rate_changed_by_sp_part"] = {k: zr([r for r in chg if sp_family(r["transformation_type"]) == k]) for k in sorted({sp_family(r["transformation_type"]) for r in chg})}
    res["zero_rate_equivalent_by_sp_family"] = {k: zr([r for r in eqv if sp_family(r["transformation_type"]) == k]) for k in sorted({sp_family(r["transformation_type"]) for r in eqv})}
    # program x SC family  (changed zero rate) and program x SP family (equivalent zero rate)
    scs = sorted({sc_family(r["transformation_type"]) for r in chg})
    sps = sorted({sp_family(r["transformation_type"]) for r in eqv})
    write_csv(f"program_x_sc_family_changed_v5_zero_rate_{tag}.csv",
              [{"program": p, **{f"{k}": (lambda s: f"{sum(1 for r in s if r['scores']['sbg_v5']==0)}/{len(s)}" if s else "")([r for r in chg if r["base_id"] == p and sc_family(r["transformation_type"]) == k]) for k in scs}} for p in progs])
    write_csv(f"program_x_sp_family_equivalent_v5_nonzero_{tag}.csv",
              [{"program": p, **{f"{k}": (lambda s: f"{sum(1 for r in s if r['scores']['sbg_v5']>0)}/{len(s)}" if s else "")([r for r in eqv if r["base_id"] == p and sp_family(r["transformation_type"]) == k]) for k in sps}} for p in progs])
    # stratified AUROC by SP family of the matched set (CHANGED SP part == its EQUIVALENT partner's SP)
    strat = {}
    for k in sps:
        sub = [r for r in pop if sp_family(r["transformation_type"]) == k]
        if any(r["label"] for r in sub) and any(not r["label"] for r in sub):
            strat[k] = {"n_pairs": len(sub), **{n: r6(au(sub, kk)) for n, kk in preds.items()}}
    res["pooled_auroc_by_sp_family_of_set"] = strat
    strat2 = {}
    for k in scs:
        sub_ch = [r for r in chg if sc_family(r["transformation_type"]) == k]
        # AUROC of CH of SC family k against ALL equivalents (pooled) -- descriptive recall-style view
        sub = sub_ch + eqv
        strat2[k] = {"n_changed": len(sub_ch), **{n: r6(au(sub, kk)) for n, kk in preds.items()}}
    res["auroc_changed_sc_family_vs_all_equivalent"] = strat2
    # drop-out of the zero-score share
    res["zero_score_share"] = {n: {"all": r6(sum(1 for r in pop if r["scores"][k] == 0) / len(pop)),
                                   "changed": r6(sum(1 for r in chg if r["scores"][k] == 0) / len(chg)),
                                   "equivalent": r6(sum(1 for r in eqv if r["scores"][k] == 0) / len(eqv))} for n, k in preds.items()}
    res["structure_note"] = structure_note
    return res


def main():
    hashes = {}
    paths = ["artifacts/final/pairs_v10_test_v6exp.jsonl", "artifacts/final/V10_MODELS_FROZEN.json", "artifacts/final/FREEZE_V10.json",
             "artifacts/final/FREEZE_V10_SCORED.json", "artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json",
             "benchmark/datasets/v10_independent/pairs_test.jsonl", "benchmark/datasets/v10_independent/manifest.json",
             "artifacts/final/V9_MODELS_FROZEN.json", "artifacts/final/FREEZE_V9.json", "artifacts/paper_evidence/V9_VAL_EVALUATION.json",
             "artifacts/final/pairs_v9c_val_output_free_v8.jsonl", "artifacts/final/pairs_v8val_output_free_v8.jsonl",
             "benchmark/datasets/v9_composed/pairs_val.jsonl", "benchmark/datasets/v8/pairs_val.jsonl",
             "artifacts/final/BENCHMARK_VALIDITY_AUDIT_V9C.json", "artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json",
             "artifacts/paper_evidence/DIAGNOSTIC_V8_STALE_VARIANTS.json",
             "experiments/final/evaluate_v10.py", "experiments/final/evaluate_v9.py", "experiments/final/evaluate_v4_dev.py",
             "experiments/final/fit_weights.py", "experiments/final/edit_size_analysis.py", "experiments/final/static_baselines.py", "sbg/statistics.py"]
    for p in paths:
        hashes[p] = sha(REPO / p)
    (OUT / "inputs_sha256.json").write_text(json.dumps(hashes, indent=1) + "\n")

    # ---------------- V10 ----------------
    pop, unev, _ = build_v10()
    frozen = json.loads((REPO / "artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json").read_text())
    assert len(pop) == frozen["n_pairs"] == 638 and len(pop) // 2 == frozen["n_matched_sets"] and len({r["base_id"] for r in pop}) == 19
    cnt = {p: sum(1 for r in pop if r["base_id"] == p) for p in sorted({r["base_id"] for r in pop})}
    assert cnt == frozen["per_program_counts"]
    preds10 = {"V5": "sbg_v5", "edit": "edit", "M_EX": "M_EX", "M_EX+V5": "M_EX+V5", "coverage_size": "coverage_size",
               "exception_fraction": "exception_fraction", "call_count": "call_count"}
    headline10 = {"V5": 0.896768, "edit": 0.616046, "M_EX": 0.790789, "M_EX+V5": 0.797088,
                  "coverage_size": frozen["predictors"]["coverage_size"]["auroc"], "exception_fraction": frozen["predictors"]["exception_fraction"]["auroc"],
                  "call_count": frozen["predictors"]["call_count"]["auroc"]}
    r10 = analyse("v10", pop, preds10, {"V5": "V5", "EDIT": "edit", "MEX": "M_EX", "MEXV5": "M_EX+V5"}, headline10,
                  "V10: 19 programs, 3 pairs (V10 manifest) unevaluated (non-terminating) -> their matched partners dropped by the frozen matched-complete rule")
    # cross-check per-program AUROC vs frozen JSON
    chk = {}
    for row in r10["per_program"]:
        f = frozen["per_program_auroc"][row["program"]]
        chk[row["program"]] = {"n_match": row["n_pairs"] == f["n"], "V5_diff": r6(row["V5"] - f["sbg_v5"]), "edit_diff": r6(row["edit"] - f["edit"]), "M_EX_diff": r6(row["M_EX"] - f["M_EX"])}
    r10["crosscheck_per_program_vs_frozen_json(max abs diff, rounded 4dp in json)"] = {
        "all_n_match": all(v["n_match"] for v in chk.values()),
        "max_abs_diff": max(max(abs(v["V5_diff"]), abs(v["edit_diff"]), abs(v["M_EX_diff"])) for v in chk.values())}
    fz_mc = frozen["matched_set_concordance"]
    r10["crosscheck_matched_concordance_vs_frozen_json"] = {
        n: {"recomputed": r10["matched_set"][nm]["concordance_ties_half"], "frozen": fz_mc[k]["concordance"],
            "ci_recomputed": r10["matched_set"][nm]["ci95_cluster_bootstrap"], "ci_frozen": fz_mc[k]["ci95_cluster_bootstrap"]}
        for n, nm, k in (("V5", "V5", "sbg_v5"), ("edit", "edit", "edit"), ("exception_fraction", "exception_fraction", "exception_fraction"))}
    fz_d = frozen["supplementary_deltas_not_in_holm_family"]
    r10["crosscheck_deltas_vs_frozen_json"] = {"H3_V5_minus_edit": [r10["pooled_delta_cluster_bootstrap"]["V5-edit"], frozen["pre_declared_tests"]["deltas"]["H3_V5_minus_edit_forward"]],
                                              "H4_MEXV5_minus_MEX": [r10["pooled_delta_cluster_bootstrap"]["MEXV5-MEX"], frozen["pre_declared_tests"]["deltas"]["H4_EX+V5_minus_EX"]]}
    r10["unevaluated_pairs_in_dataset"] = unev
    (OUT / "results_v10.json").write_text(json.dumps(r10, indent=1, default=str) + "\n")

    # ---------------- V9c val ----------------
    pop9, unev9, _ = build_v9cval()
    fz9 = json.loads((REPO / "artifacts/paper_evidence/V9_VAL_EVALUATION.json").read_text())["v9c_matched"]
    assert len(pop9) == fz9["n_pairs"] == 432 and len({r["base_id"] for r in pop9}) == 11
    preds9 = {"V5": "sbg_v5", "edit": "edit", "M_EX": "M_EX", "M_ESX": "M_ESX", "coverage_size": "coverage_size",
              "exception_fraction": "exception_fraction", "call_count": "call_count"}
    headline9 = {"V5": fz9["predictors"]["sbg_v5"]["auroc"], "edit": fz9["predictors"]["edit"]["auroc"], "M_EX": fz9["predictors"]["M_EX"]["auroc"],
                 "M_ESX": fz9["predictors"]["M_ESX"]["auroc"], "coverage_size": fz9["predictors"]["coverage_size"]["auroc"],
                 "exception_fraction": fz9["predictors"]["exception_fraction"]["auroc"], "call_count": fz9["predictors"]["call_count"]["auroc"]}
    r9 = analyse("v9cval", pop9, preds9, {"V5": "V5", "EDIT": "edit", "MEX": "M_EX", "MEXV5": "M_ESX"}, headline9,
                 "V9c val: M_ESX = edit+sbg_v5+exception_fraction+call_count+coverage_size (V9 analogue of V10 M_EX+V5)")
    chk9 = {}
    for row in r9["per_program"]:
        f = fz9["per_program_auroc"][row["program"]]
        chk9[row["program"]] = max(abs(row["V5"] - f["sbg_v5"]), abs(row["edit"] - f["edit"]))
    r9["crosscheck_per_program_vs_frozen_json_max_abs_diff"] = r6(max(chk9.values()))
    r9["crosscheck_matched_concordance_vs_frozen_json"] = {k: [r9["matched_set"][nm]["concordance_ties_half"], fz9["matched_set_concordance"][k]["concordance"]]
                                                           for nm, k in (("V5", "sbg_v5"), ("edit", "edit"), ("exception_fraction", "exception_fraction"))}
    r9["crosscheck_H3_V5_minus_edit"] = [r9["pooled_delta_cluster_bootstrap"]["V5-edit"], fz9["pre_declared_tests"]["H3"]]
    (OUT / "results_v9cval.json").write_text(json.dumps(r9, indent=1, default=str) + "\n")

    print("V10 headline check:", json.dumps(r10["headline_check"]))
    print("V9cval headline check:", json.dumps(r9["headline_check"]))
    print("done")


if __name__ == "__main__":
    main()
