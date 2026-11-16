#!/usr/bin/env python3
"""ab02 -- INDEPENDENT dev/train statistical re-analysis of the saved A4C predictions (EXP-A4R-003).

Pure stdlib; does NOT import eval_lib / a4dlib / a4c_*  (own implementations of AUROC, AUPRC, cluster bootstrap, Holm, exact sign-flip test), so
agreement with EXP-A4C-004 / EXP-A4D-005 is a genuine cross-check.  Reads saved predictions only (no model is run, no held-out file is touched).
Populations analysed: v9c_dev (selection/exploratory) and v9c_train (development; reduced -- math_gray_code excluded).  v9c_val / v10_test are refused.

Outputs -> WP_A_B_COMPARATIVE_BENCHMARK/raw/EXP-A4R-003/ and tables/
"""
from __future__ import annotations

import csv
import json
import math
import pathlib
import random
import sys
import time
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
WP = HERE.parent
PKG = WP.parent
RAW = PKG / "results" / "raw"
PRED = RAW / "EXP-A4C-003" / "predictions"
OUT = WP / "raw" / "EXP-A4R-003"
TAB = WP / "tables"
OUT.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)
POPS = ("v9c_dev", "v9c_train")          # held-out populations are refused by construction
B = 4000
SEED = 20260115                           # differs from A4C/A4D (42 / 1234) on purpose


# ---------------------------------------------------------------- metrics (own implementations)
def midranks(s):
    order = sorted(range(len(s)), key=s.__getitem__)
    r = [0.0] * len(s)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and s[order[j + 1]] == s[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


def auroc(s, y):
    P = sum(y)
    N = len(y) - P
    if P == 0 or N == 0:
        return float("nan")
    r = midranks(s)
    return (sum(r[i] for i in range(len(y)) if y[i]) - P * (P + 1) / 2) / (P * N)


def tie_stats(s, y):
    """share of pos-neg pairs that are exactly tied, and AUROC bounds (ties counted as 0 / 1)."""
    pos = sorted(a for a, b in zip(s, y) if b)
    neg = sorted(a for a, b in zip(s, y) if not b)
    import bisect
    gt = eq = 0
    for p in pos:
        lo = bisect.bisect_left(neg, p)
        hi = bisect.bisect_right(neg, p)
        gt += lo
        eq += hi - lo
    tot = len(pos) * len(neg)
    return {"tie_pair_share": eq / tot, "auroc_lower": gt / tot, "auroc_upper": (gt + eq) / tot,
            "n_distinct": len(set(s)), "modal_share": max(sum(1 for a in s if a == v) for v in set(s)) / len(s) if len(set(s)) < 50 else 0.0}


def ap(s, y):
    """average precision (step-wise), tied scores enter jointly"""
    P = sum(y)
    if not P:
        return float("nan")
    order = sorted(range(len(s)), key=lambda i: -s[i])
    tp = fp = 0
    res = prev_rec = 0.0
    i = 0
    while i < len(order):
        j = i
        while j < len(order) and s[order[j]] == s[order[i]]:
            j += 1
        for k in order[i:j]:
            tp += y[k]
            fp += 1 - y[k]
        rec = tp / P
        res += (rec - prev_rec) * tp / (tp + fp)
        prev_rec = rec
        i = j
    return res


def youden(s, y):
    P = sum(y)
    N = len(y) - P
    best, thr = -9, None
    for t in sorted(set(s)):
        tpr = sum(1 for a, b in zip(s, y) if b and a >= t) / P
        fpr = sum(1 for a, b in zip(s, y) if not b and a >= t) / N
        if tpr - fpr > best + 1e-12:
            best, thr = tpr - fpr, t
    return thr


def holm(p):
    names = sorted(p, key=p.get)
    m = len(names)
    run, out = 0.0, {}
    for i, k in enumerate(names):
        run = max(run, min(1.0, (m - i) * p[k]))
        out[k] = run
    return out


# ---------------------------------------------------------------- cluster decomposition (exact pooled AUROC from cluster-pair matrices)
class Clu:
    def __init__(self, base, y):
        self.keys = sorted(set(base))
        self.idx = {k: [i for i, b in enumerate(base) if b == k] for k in self.keys}
        self.K = len(self.keys)
        self.P = [sum(y[i] for i in self.idx[k]) for k in self.keys]
        self.N = [len(self.idx[k]) - p for k, p in zip(self.keys, self.P)]
        self.y = y

    def matrix(self, s):
        """C[k][l] = concordance(+0.5 ties) of positives of cluster k vs negatives of cluster l"""
        y = self.y
        pos = [[s[i] for i in self.idx[k] if y[i]] for k in self.keys]
        neg = [sorted(s[i] for i in self.idx[k] if not y[i]) for k in self.keys]
        import bisect
        C = [[0.0] * self.K for _ in range(self.K)]
        for k in range(self.K):
            for l in range(self.K):
                c = 0.0
                for p in pos[k]:
                    lo = bisect.bisect_left(neg[l], p)
                    hi = bisect.bisect_right(neg[l], p)
                    c += lo + 0.5 * (hi - lo)
                C[k][l] = c
        return C

    def auroc_w(self, C, w):
        num = sum(w[k] * w[l] * C[k][l] for k in range(self.K) if w[k] for l in range(self.K) if w[l])
        den = sum(w[k] * w[l] * self.P[k] * self.N[l] for k in range(self.K) if w[k] for l in range(self.K) if w[l])
        return num / den if den else float("nan")

    def per_cluster(self, s):
        out = {}
        for k, key in enumerate(self.keys):
            ii = self.idx[key]
            out[key] = auroc([s[i] for i in ii], [self.y[i] for i in ii])
        return out


def resample_weights(K, B, seed):
    rng = random.Random(seed)
    W = []
    for _ in range(B):
        w = [0] * K
        for _ in range(K):
            w[rng.randrange(K)] += 1
        W.append(w)
    return W


def pct(v, q):
    v = sorted(x for x in v if x == x)
    n = len(v)
    return v[min(n - 1, max(0, int(round(q * (n - 1)))))]


# ---------------------------------------------------------------- IO
def load_pop(pop):
    meta = json.loads((PRED / "meta.json").read_text())["methods"]
    cols, rows0 = {}, None
    for f in sorted((PRED / pop).glob("*.json")):
        if f.name.startswith("_"):
            continue
        d = json.loads(f.read_text())
        rows = d["rows"]
        sig = [(r["pair_id"], r["label"], r["base_id"], r["group"]) for r in rows]
        if rows0 is None:
            rows0 = sig
        elif sig != rows0:
            raise SystemExit(f"row/label mismatch in {f.name}")
        cols[d["method"]] = [r["score"] for r in rows]
    info = json.loads((PRED / pop / "_population_info.json").read_text())
    return meta, cols, rows0, info


def main():
    t0 = time.time()
    fc = json.loads((RAW / "EXP-A4C-002" / "frozen_config.json").read_text())
    reps = fc["representatives"]                      # family -> method key
    report = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "B_dev": B, "B_train": 1000, "seed": SEED, "populations": {}}
    a4d = {r["method"]: r for r in csv.DictReader(open(PKG / "results" / "tables" / "EXP-A4D-005_v9c_dev_recomputed_metrics.csv"))}
    for pop in POPS:
        meta, cols, rows, info = load_pop(pop)
        pair, y, base, group = ([r[i] for r in rows] for i in range(4))
        cl = Clu(base, y)
        n, P = len(y), sum(y)
        popinfo = {"n_rows": n, "n_pos": P, "n_neg": n - P, "n_programs": cl.K, "n_groups": len(set(group)),
                   "n_dropped_missing_trace": info.get("n_dropped_missing_trace"), "dropped_examples": info.get("dropped", [])[:5],
                   "pos_per_program": {k: [p, nn] for k, p, nn in zip(cl.keys, cl.P, cl.N)}, "n_methods": len(cols)}
        # per-method point estimates
        Bp = B if pop == 'v9c_dev' else 1000
        W = resample_weights(cl.K, Bp, SEED)
        mats = {}
        res = {}
        for m, s in cols.items():
            ts = tie_stats(s, y)
            C = cl.matrix(s)
            mats[m] = C
            res[m] = {"auroc": auroc(s, y), "auprc": ap(s, y), **ts, "auroc_from_matrix": cl.auroc_w(C, [1] * cl.K),
                      "role": meta[next(k for k, v in meta.items() if v["method"] == m)]["role"] if any(v["method"] == m for v in meta.values()) else "?",
                      "privileged": next((v["privileged_output_reading"] for v in meta.values() if v["method"] == m), None)}
            if abs(res[m]["auroc"] - res[m]["auroc_from_matrix"]) > 1e-9:
                raise SystemExit(f"matrix decomposition mismatch {m}")
            per = cl.per_cluster(s)
            vals = [v for v in per.values() if v == v]
            res[m]["macro_auroc"] = sum(vals) / len(vals) if vals else float("nan")
            res[m]["n_programs_auroc_gt_half"] = sum(1 for v in vals if v > 0.5)
            res[m]["per_program"] = per
        # bootstrap CIs for the representative set + references + diagnostics
        focus = sorted(set(reps.values()) | {"sbg_v5", "oracle|frac11", "changeguard_cmp|frac11", "edit_rev"})
        focus = [m for m in focus if m in cols]
        for m in focus:
            bs = [cl.auroc_w(mats[m], w) for w in W]
            res[m]["ci95"] = [pct(bs, 0.025), pct(bs, 0.975)]
        v5 = "sbg_v5"
        fam = {}
        for f, m in reps.items():
            if m not in cols:
                continue
            d_obs = res[v5]["auroc"] - res[m]["auroc"]
            ds = [cl.auroc_w(mats[v5], w) - cl.auroc_w(mats[m], w) for w in W]
            ds_ok = [x for x in ds if x == x]
            nle = sum(1 for x in ds_ok if x <= 0)
            nge = sum(1 for x in ds_ok if x >= 0)
            p_boot = min(1.0, 2 * (min(nle, nge) + 1) / (len(ds_ok) + 1))
            # exact sign-flip randomisation test on per-program AUROC differences (programs with both classes)
            pv, pm = res[v5]["per_program"], res[m]["per_program"]
            dk = [pv[k] - pm[k] for k in cl.keys if pv[k] == pv[k] and pm[k] == pm[k]]
            K = len(dk)
            obs = sum(dk) / K
            cnt = 0
            if K <= 16:                                   # exact enumeration of all 2^K sign patterns
                for mask in range(1 << K):
                    tot = sum(d if (mask >> i) & 1 else -d for i, d in enumerate(dk))
                    if abs(tot / K) >= abs(obs) - 1e-12:
                        cnt += 1
                p_sf = cnt / (1 << K)
            else:                                         # Monte-Carlo sign flips (100k), +1 smoothing
                rr = random.Random(SEED + 7)
                for _ in range(100000):
                    tot = sum(d if rr.random() < 0.5 else -d for d in dk)
                    if abs(tot / K) >= abs(obs) - 1e-12:
                        cnt += 1
                p_sf = (cnt + 1) / 100001
            fam[f] = {"method": m, "delta_v5_minus": d_obs, "ci95": [pct(ds_ok, 0.025), pct(ds_ok, 0.975)], "p_boot": p_boot,
                      "macro_delta": obs, "n_prog": K, "n_prog_v5_better": sum(1 for d in dk if d > 0), "n_prog_competitor_better": sum(1 for d in dk if d < 0),
                      "p_signflip_exact": p_sf, "frac_boot_delta_le0": nle / len(ds_ok)}
        hb = holm({f: v["p_boot"] for f, v in fam.items() if f != "sbg_v5"})
        hs = holm({f: v["p_signflip_exact"] for f, v in fam.items()})
        for f in fam:
            fam[f]["p_boot_holm_m%d" % len(fam)] = hb.get(f)
            fam[f]["p_signflip_holm_m%d" % len(fam)] = hs.get(f)
        # edit-size strata (terciles of edit score from the 'edit' method)
        e = cols["edit"]
        cuts = sorted(e)[int(n / 3)], sorted(e)[int(2 * n / 3)]
        strat = [0 if v < cuts[0] else 1 if v < cuts[1] else 2 for v in e]
        strata = {}
        for m in ("sbg_v5", "sbg_state", "forest|RF_d4|EXx", "pathspectra|shape|covset|max", "LR_EX", "edit", "trace_len_mean", "oracle|frac11", "output_indep|frac40"):
            if m not in cols:
                continue
            strata[m] = {}
            for st in range(3):
                ii = [i for i in range(n) if strat[i] == st]
                strata[m][f"tercile{st + 1}"] = {"n": len(ii), "pos": sum(y[i] for i in ii), "auroc": auroc([cols[m][i] for i in ii], [y[i] for i in ii])}
        # matched-set concordance (groups of 1 pos + 1 neg)
        gm = defaultdict(list)
        for i, g in enumerate(group):
            gm[g].append(i)
        matched = {}
        for m in ("sbg_v5", "sbg_state", "forest|RF_d4|EXx", "pathspectra|shape|covset|max", "LR_EX", "edit", "oracle|frac11"):
            if m not in cols:
                continue
            conc = tot = ties = 0
            for g, ii in gm.items():
                ps = [cols[m][i] for i in ii if y[i]]
                ns = [cols[m][i] for i in ii if not y[i]]
                for a in ps:
                    for b in ns:
                        tot += 1
                        conc += a > b
                        ties += a == b
            matched[m] = {"n_pairs": tot, "concordant": conc, "tied": ties, "strict": conc / tot, "ties_half": (conc + ties / 2) / tot}
        # family-level selection spread (selection-on-dev optimism)
        spread = {}
        if pop == "v9c_dev":
            for f, mkey in reps.items():
                members = [v["method"] for v in meta.values() if v.get("family") == f.rstrip("*") or v.get("family") == f]
                members = [m for m in members if m in res]
                if len(members) > 1:
                    a = sorted(res[m]["auroc"] for m in members)
                    spread[f] = {"n_configs": len(a), "min": a[0], "median": a[len(a) // 2], "max": a[-1], "representative": mkey}
        # cross-check vs A4D-005 recomputed metrics (dev only)
        xcheck = {}
        if pop == "v9c_dev":
            diffs = []
            for m in cols:
                key = m.replace("|", "__")
                if key in a4d:
                    diffs.append((abs(res[m]["auroc"] - float(a4d[key]["auroc"])), abs(res[m]["auprc"] - float(a4d[key]["auprc"])), m))
            xcheck = {"n_compared": len(diffs), "max_abs_auroc_diff": max(d[0] for d in diffs), "max_abs_auprc_diff": max(d[1] for d in diffs),
                      "worst_auroc_method": max(diffs)[2]}
        report["populations"][pop] = {"info": popinfo, "methods": res, "holm_family": fam, "edit_strata": strata, "edit_tercile_cuts": cuts,
                                      "matched_sets": matched, "family_spread": spread, "xcheck_vs_A4D005": xcheck}
        print(pop, "done", round(time.time() - t0), "s", xcheck)
    # strip per-program from main json size? keep (small)
    (OUT / "independent_stats.json").write_text(json.dumps(report, indent=1, sort_keys=True, default=str))
    # tables
    for pop in POPS:
        R = report["populations"][pop]
        with open(TAB / f"EXP-A4R-003_{pop}_methods.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["method", "role", "privileged", "auroc", "ci_lo", "ci_hi", "macro_auroc", "n_prog_auroc_gt_half", "auprc", "tie_pair_share", "auroc_lower_ties0", "auroc_upper_ties1", "n_distinct"])
            for m, v in sorted(R["methods"].items(), key=lambda kv: -kv[1]["auroc"]):
                ci = v.get("ci95", ["", ""])
                w.writerow([m, v["role"], v["privileged"], f"{v['auroc']:.4f}", ci[0] if ci[0] == "" else f"{ci[0]:.4f}", ci[1] if ci[1] == "" else f"{ci[1]:.4f}", f"{v['macro_auroc']:.4f}",
                            v["n_programs_auroc_gt_half"], f"{v['auprc']:.4f}", f"{v['tie_pair_share']:.4f}", f"{v['auroc_lower']:.4f}", f"{v['auroc_upper']:.4f}", v["n_distinct"]])
        with open(TAB / f"EXP-A4R-003_{pop}_holm_family.csv", "w", newline="") as f:
            w = csv.writer(f)
            hk = [k for k in next(iter(R["holm_family"].values())) if k.startswith("p_") and "holm" in k]
            w.writerow(["family", "method", "delta_v5_minus", "ci_lo", "ci_hi", "p_boot", *[k for k in hk if "boot" in k], "macro_delta", "n_prog", "n_v5_better", "n_comp_better", "p_signflip_exact", *[k for k in hk if "signflip" in k]])
            for fam_, v in sorted(R["holm_family"].items(), key=lambda kv: kv[1]["delta_v5_minus"]):
                w.writerow([fam_, v["method"], f"{v['delta_v5_minus']:+.4f}", f"{v['ci95'][0]:+.4f}", f"{v['ci95'][1]:+.4f}", f"{v['p_boot']:.4f}",
                            *[("" if v[k] is None else f"{v[k]:.4f}") for k in hk if "boot" in k], f"{v['macro_delta']:+.4f}", v["n_prog"], v["n_prog_v5_better"], v["n_prog_competitor_better"],
                            f"{v['p_signflip_exact']:.5f}", *[("" if v[k] is None else f"{v[k]:.4f}") for k in hk if "signflip" in k]])
    print("written", OUT / "independent_stats.json", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
