#!/usr/bin/env python3
"""EXP-A3-003: statistical dependence, Monte-Carlo stability of CIs, unit-of-resampling sensitivity, leave-one-program-out,
per-program table, AUROC-vs-AUPRC sensitivity, H4 power / equivalence analysis.  Pure stdlib (a3lib only).

  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a3_003_dependence.py
Outputs: results/raw/EXP-A3-003/*.json ; results/tables/EXP-A3-003_*.csv
"""
import collections
import csv
import json
import math
import multiprocessing as mp
import pathlib
import random
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L  # noqa: E402

RAW = L.PKG / "results" / "raw" / "EXP-A3-003"
TAB = L.PKG / "results" / "tables"
RAW.mkdir(parents=True, exist_ok=True)
G = {}


def load_v10():
    allr, pop = L.build_v10()
    mf = json.loads((L.ART / "V10_MODELS_FROZEN.json").read_text())
    for r in pop:
        r["scores"]["edit_reversed"] = -r["scores"]["edit"]
        for n, m in mf["models"].items():
            r["scores"][f"M_{n}"] = L.lin_score({"features": m["features"], **m}, r["scores"])
    return pop


def load_v9c_val():
    allr, pop = L.build_v9c("val")
    models = json.loads((L.ART / "V9_MODELS_FROZEN.json").read_text())["models"]
    for r in pop:
        for n, m in models.items():
            r["scores"][f"M_{n}"] = L.lin_score({"features": m["features"], **m}, r["scores"])
    return pop


def write_csv(path, rows, fields=None):
    fields = fields or list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


# ------------------------------------------------------------------ resampling schemes -> list of index lists
def idx_program(pop, rng):
    d = L.by_cluster([r["base_id"] for r in pop])
    ks = sorted(d)
    return [i for _ in ks for i in d[ks[rng.randrange(len(ks))]]]


def idx_set(pop, rng):
    d = L.by_cluster([r["group"] for r in pop])
    ks = sorted(d)
    return [i for _ in ks for i in d[ks[rng.randrange(len(ks))]]]


def idx_pair(pop, rng):
    n = len(pop)
    return [rng.randrange(n) for _ in range(n)]


def idx_two_stage(pop, rng):
    prog = collections.defaultdict(lambda: collections.defaultdict(list))
    for i, r in enumerate(pop):
        prog[r["base_id"]][r["group"]].append(i)
    ps = sorted(prog)
    out = []
    for _ in ps:
        sets = prog[ps[rng.randrange(len(ps))]]
        sk = sorted(sets)
        for _ in sk:
            out.extend(sets[sk[rng.randrange(len(sk))]])
    return out


SCHEMES = {"pair_iid": idx_pair, "matched_set": idx_set, "program_cluster": idx_program, "two_stage_program_then_set": idx_two_stage}


def boot_scheme(job):
    """job = (scheme, kind, a, b, seed, B) ; kind in auroc|delta|auprc|auprc_delta"""
    scheme, kind, a, b, seed, nb = job
    pop = G["pop"]
    y_all = [r["label"] for r in pop]
    sa = [r["scores"][a] for r in pop]
    sb = [r["scores"][b] for r in pop] if b else None
    rng = random.Random(seed)
    f = SCHEMES[scheme]
    vals = []
    for _ in range(nb):
        idx = f(pop, rng)
        yy = [y_all[i] for i in idx]
        if not (0 < sum(yy) < len(yy)):
            continue
        xa = [sa[i] for i in idx]
        if kind == "auroc":
            vals.append(L.auroc(xa, yy))
        elif kind == "auprc":
            vals.append(L.auprc(xa, yy))
        elif kind == "delta":
            vals.append(L.auroc(xa, yy) - L.auroc([sb[i] for i in idx], yy))
        elif kind == "auprc_delta":
            vals.append(L.auprc(xa, yy) - L.auprc([sb[i] for i in idx], yy))
    lo, hi, n = L.pct_ci(vals)
    m = statistics.mean(vals)
    sd = statistics.pstdev(vals)
    n_le = sum(1 for d in vals if d <= 0)
    n_ge = sum(1 for d in vals if d >= 0)
    p = min(1.0, 2 * min(n_le + 1, n_ge + 1) / (n + 1))
    q05 = sorted(vals)[int(0.05 * n)]
    q95 = sorted(vals)[min(n - 1, int(math.ceil(0.95 * n)) - 1)]
    return {"scheme": scheme, "kind": kind, "a": a, "b": b, "seed": seed, "B": nb, "ci_lo": lo, "ci_hi": hi, "width": hi - lo, "boot_sd": sd, "p_two_sided": p,
            "ci90": [q05, q95]}


def run_pool(jobs, n=4):
    with mp.get_context("fork").Pool(n) as p:
        return p.map(boot_scheme, jobs)


def per_program_table(pop, preds):
    rows = []
    for p in sorted({r["base_id"] for r in pop}):
        sub = [r for r in pop if r["base_id"] == p]
        yy = [r["label"] for r in sub]
        row = {"program": p, "n_pairs": len(sub), "n_sets": len(sub) // 2}
        for k in preds:
            row[k] = round(L.auroc([r["scores"][k] for r in sub], yy), 4)
        rows.append(row)
    return rows


def sign_counts(rows, a, b):
    lt = sum(1 for r in rows if r[a] < r[b])
    gt = sum(1 for r in rows if r[a] > r[b])
    eq = len(rows) - lt - gt
    # exact two-sided sign test (ties dropped)
    n = lt + gt
    k = min(lt, gt)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return {"a": a, "b": b, "a_lt_b": lt, "a_gt_b": gt, "ties": eq, "n_programs": len(rows), "sign_test_p_two_sided": p}


def lopo(pop, preds):
    out = {}
    progs = sorted({r["base_id"] for r in pop})
    for k in preds:
        vals = {}
        for p in progs:
            sub = [r for r in pop if r["base_id"] != p]
            vals[p] = L.auroc([r["scores"][k] for r in sub], [r["label"] for r in sub])
        out[k] = {"min": min(vals.values()), "max": max(vals.values()), "argmin_removed": min(vals, key=vals.get), "argmax_removed": max(vals, key=vals.get),
                  "full": L.auroc([r["scores"][k] for r in pop], [r["label"] for r in pop])}
    return out


def icc_oneway(groups):
    """groups: dict cluster -> list of values; ANOVA ICC(1) with unbalanced n0."""
    k = len(groups)
    N = sum(len(v) for v in groups.values())
    gm = sum(sum(v) for v in groups.values()) / N
    ssb = sum(len(v) * (sum(v) / len(v) - gm) ** 2 for v in groups.values())
    ssw = sum(sum((x - sum(v) / len(v)) ** 2 for x in v) for v in groups.values())
    msb, msw = ssb / (k - 1), ssw / (N - k)
    n0 = (N - sum(len(v) ** 2 for v in groups.values()) / N) / (k - 1)
    icc = (msb - msw) / (msb + (n0 - 1) * msw) if (msb + (n0 - 1) * msw) else 0.0
    return {"icc1": icc, "n0": n0, "msb": msb, "msw": msw, "k": k, "N": N, "design_effect": 1 + (N / k - 1) * max(icc, 0.0)}


def set_level_outcomes(pop, a, b=None):
    g = collections.defaultdict(dict)
    for r in pop:
        g[r["group"]][r["label"]] = r
    out = collections.defaultdict(list)
    for v in g.values():
        if 0 in v and 1 in v:
            d = v[1]["scores"][a] - v[0]["scores"][a]
            out[v[1]["base_id"]].append((1.0 if d > 0 else 0.5 if d == 0 else 0.0, d))
    return out


def h4_power(pop, a, b, sims=20000, seed=7):
    """Per-program delta distribution + normal/t power simulation + MDE + equivalence."""
    rows = []
    for p in sorted({r["base_id"] for r in pop}):
        sub = [r for r in pop if r["base_id"] == p]
        yy = [r["label"] for r in sub]
        rows.append(L.auroc([r["scores"][a] for r in sub], yy) - L.auroc([r["scores"][b] for r in sub], yy))
    k = len(rows)
    mean, sd = statistics.mean(rows), statistics.stdev(rows)
    se = sd / math.sqrt(k)
    tcrit = {19: 2.101, 11: 2.228}.get(k, 2.1)  # df = k-1 : 18 -> 2.101 ; 10 -> 2.228
    rng = random.Random(seed)
    power = {}
    for delta in (0.0, 0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10):
        rej = 0
        for _ in range(sims):
            x = [rng.gauss(delta, sd) for _ in range(k)]
            m, s = statistics.mean(x), statistics.stdev(x)
            if s > 0 and abs(m / (s / math.sqrt(k))) > tcrit:
                rej += 1
        power[delta] = rej / sims
    return {"k_programs": k, "per_program_delta": rows, "mean_per_program_delta": mean, "sd_per_program_delta": sd, "se_mean_delta": se,
            "t_stat": mean / se, "mde_80pct_power_alpha05_two_sided": 2.8 * se, "mde_80pct_power_alpha_holm_first(0.05/6)": (1.96 + 0.84) * se * 1.0,  # placeholder replaced below
            "power_by_true_delta_t_test": power,
            "programs_needed_for_80pct_power": {str(d): math.ceil(((2.8 * sd) / d) ** 2) for d in (0.005, 0.01, 0.02, 0.03, 0.05)}}


def main():
    res = {}
    pop10 = load_v10()
    pop9 = load_v9c_val()
    summary_rows = []
    for name, pop, specs in (
        ("v10_test", pop10, [("auroc", "sbg_v5", None), ("auroc", "sbg_state", None), ("auroc", "M_EX", None), ("auroc", "M_EX+V5", None),
                             ("delta", "M_EX+V5", "M_EX"), ("delta", "M_E+V5", "M_E"), ("delta", "sbg_v6", "sbg_v5"), ("delta", "sbg_v5", "M_EX"), ("delta", "sbg_v5", "edit"),
                             ("delta", "sbg_state", "sbg_v5")]),
        ("v9c_val", pop9, [("auroc", "sbg_v5", None), ("auroc", "sbg_state", None), ("auroc", "M_EX", None), ("auroc", "M_ESX", None),
                           ("delta", "M_ESX", "M_EX"), ("delta", "M_ES", "M_E"), ("delta", "sbg_v5", "M_EX"), ("delta", "sbg_v5", "edit"), ("delta", "sbg_state", "sbg_v5")])):
        G["pop"] = pop
        # 1. unit-of-resampling comparison (seed 42, B=2000)
        jobs = [(sch, kind, a, b, 42, 2000) for kind, a, b in specs for sch in SCHEMES]
        unit = run_pool(jobs)
        write_csv(TAB / f"EXP-A3-003_{name}_resampling_unit_comparison.csv", [{**u, "ci90": str(u["ci90"])} for u in unit])
        # 2. seed stability for the program-cluster scheme (identical algorithm, 12 seeds) + one B=20000 run
        seeds = [42, 1, 2, 3, 5, 7, 11, 123, 2024, 31337, 99991, 271828]
        jobs = [("program_cluster", kind, a, b, s, 2000) for kind, a, b in specs for s in seeds]
        stab = run_pool(jobs)
        jobs = [("program_cluster", kind, a, b, 424242, 20000) for kind, a, b in specs]
        big = run_pool(jobs)
        stab_tbl = []
        for kind, a, b in specs:
            sel = [u for u in stab if u["kind"] == kind and u["a"] == a and u["b"] == b]
            bg = [u for u in big if u["kind"] == kind and u["a"] == a and u["b"] == b][0]
            stab_tbl.append({"kind": kind, "a": a, "b": b, "seed42_lo": [u for u in sel if u["seed"] == 42][0]["ci_lo"], "seed42_hi": [u for u in sel if u["seed"] == 42][0]["ci_hi"],
                             "lo_min": min(u["ci_lo"] for u in sel), "lo_max": max(u["ci_lo"] for u in sel), "hi_min": min(u["ci_hi"] for u in sel), "hi_max": max(u["ci_hi"] for u in sel),
                             "p_min": min(u["p_two_sided"] for u in sel), "p_max": max(u["p_two_sided"] for u in sel),
                             "B20000_lo": bg["ci_lo"], "B20000_hi": bg["ci_hi"], "B20000_p": bg["p_two_sided"]})
        write_csv(TAB / f"EXP-A3-003_{name}_seed_stability.csv", stab_tbl)
        # 3. LOPO + per-program table
        preds = ["sbg_v5", "sbg_state", "sbg_v3", "sbg_temporal", "edit", "coverage_size", "exception_fraction", "call_count"] + (["sbg_v6", "M_EX", "M_E+V5", "M_EX+V5"] if name == "v10_test" else ["M_EX", "M_E", "M_ES", "M_ESX"])
        lp = lopo(pop, preds)
        pp = per_program_table(pop, preds)
        write_csv(TAB / f"EXP-A3-003_{name}_per_program_auroc.csv", pp)
        signs = [sign_counts(pp, "sbg_v5", "sbg_state"), sign_counts(pp, "sbg_v5", "M_EX"), sign_counts(pp, "sbg_v5", "coverage_size"), sign_counts(pp, "sbg_v5", "edit")]
        if name == "v10_test":
            signs += [sign_counts(pp, "M_EX+V5", "M_EX"), sign_counts(pp, "sbg_v6", "sbg_v5")]
        else:
            signs += [sign_counts(pp, "M_ESX", "M_EX")]
        # 4. ICC / design effect
        sl = set_level_outcomes(pop, "sbg_v5")
        icc_conc = icc_oneway({k: [c for c, _ in v] for k, v in sl.items()})
        icc_diff = icc_oneway({k: [d for _, d in v] for k, v in sl.items()})
        sl_ex = set_level_outcomes(pop, "M_EX")
        icc_ex = icc_oneway({k: [c for c, _ in v] for k, v in sl_ex.items()})
        pair_w = [u for u in unit if u["scheme"] == "pair_iid" and u["kind"] == "auroc" and u["a"] == "sbg_v5"][0]
        prog_w = [u for u in unit if u["scheme"] == "program_cluster" and u["kind"] == "auroc" and u["a"] == "sbg_v5"][0]
        de_boot = (prog_w["boot_sd"] / pair_w["boot_sd"]) ** 2
        # 5. power
        pw = h4_power(pop, "M_EX+V5" if name == "v10_test" else "M_ESX", "M_EX")
        h4u = [u for u in unit if u["kind"] == "delta" and u["a"] == ("M_EX+V5" if name == "v10_test" else "M_ESX") and u["b"] == "M_EX"]
        h4_prog = [u for u in h4u if u["scheme"] == "program_cluster"][0]
        pw["pooled_boot_sd_program_cluster"] = h4_prog["boot_sd"]
        pw["mde_80pct_pooled_boot_sd_alpha05"] = 2.8 * h4_prog["boot_sd"]
        pw["mde_80pct_pooled_boot_sd_alpha_0.0083_holm_rank1"] = (2.638 + 0.84) * h4_prog["boot_sd"]
        pw["ci90_program_cluster_bootstrap"] = h4_prog["ci90"]
        pw["tost_equivalence_bound_supported_by_90pct_ci"] = max(abs(h4_prog["ci90"][0]), abs(h4_prog["ci90"][1]))
        del pw["mde_80pct_power_alpha_holm_first(0.05/6)"]
        # 6. AUPRC sensitivity of H-tests
        G["pop"] = pop
        if name == "v10_test":
            hs = [("H2 E+V5-E", "M_E+V5", "M_E"), ("H3 V5-edit", "sbg_v5", "edit"), ("H4 EX+V5-EX", "M_EX+V5", "M_EX"), ("H5 V6-V5", "sbg_v6", "sbg_v5"), ("H6 EX+V6-EX", "M_EX+V6", "M_EX")]
        else:
            hs = [("H2 ES-E", "M_ES", "M_E"), ("H3 V5-edit", "sbg_v5", "edit"), ("H4 ESX-EX", "M_ESX", "M_EX")]
        jobs = [("program_cluster", "auprc_delta", a, b, 42, 2000) for _, a, b in hs] + [("matched_set", "delta", a, b, 42, 2000) for _, a, b in hs] + \
               [("matched_set", "auprc_delta", a, b, 42, 2000) for _, a, b in hs]
        sens = run_pool(jobs)
        y = [r["label"] for r in pop]
        sens_tbl = []
        for (h, a, b) in hs:
            sa, sb = [r["scores"][a] for r in pop], [r["scores"][b] for r in pop]
            row = {"hypothesis": h, "delta_auroc": L.auroc(sa, y) - L.auroc(sb, y), "delta_auprc": L.auprc(sa, y) - L.auprc(sb, y)}
            for lab, kind, sch in (("auprc_program", "auprc_delta", "program_cluster"), ("auroc_matched_set", "delta", "matched_set"), ("auprc_matched_set", "auprc_delta", "matched_set")):
                u = [x for x in sens if x["kind"] == kind and x["scheme"] == sch and x["a"] == a and x["b"] == b][0]
                row[f"{lab}_ci"] = f"[{u['ci_lo']:+.4f},{u['ci_hi']:+.4f}]"
                row[f"{lab}_p"] = u["p_two_sided"]
            sens_tbl.append(row)
        write_csv(TAB / f"EXP-A3-003_{name}_auprc_and_unit_sensitivity.csv", sens_tbl)
        write_csv(TAB / f"EXP-A3-003_{name}_power_h4.csv", [{"true_delta": k, "power_t_test": v} for k, v in pw["power_by_true_delta_t_test"].items()])
        res[name] = {"unit_comparison": unit, "seed_stability": stab_tbl, "lopo": lp, "sign_tests": signs, "icc_set_concordance_v5": icc_conc, "icc_set_score_diff_v5": icc_diff,
                     "icc_set_concordance_M_EX": icc_ex, "design_effect_from_bootstrap_var_ratio_v5": de_boot, "power_h4": pw, "auprc_sensitivity": sens_tbl}
        print(name, "done")
    (RAW / "dependence_and_power.json").write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
