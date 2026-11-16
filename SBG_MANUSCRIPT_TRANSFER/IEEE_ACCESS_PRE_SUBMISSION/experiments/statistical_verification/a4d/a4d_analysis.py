"""A4D analysis engine (pure stdlib; built on a4dlib).  One `Engine` per (population, set of score columns)."""
from __future__ import annotations

import math

import a4dlib as L

HOLM_M = 19            # pre-declared family size (04_HEAD_TO_HEAD_BENCHMARK_PLAN.md section 3)
ALT_SEED = 1234
ALPHA = 0.05


def tercile_strata(edit, q=3):
    es = sorted(edit)
    cuts = [es[int(len(es) * i / q)] for i in range(1, q)]
    return [sum(1 for c in cuts if c <= e) for e in edit], cuts


class Engine:
    def __init__(self, d, cols, B=2000, seed=42, alt_seed=ALT_SEED):
        self.d, self.cols, self.B = d, cols, B
        self.res = L.Resamples(d.K, B, seed)
        self.res_alt = L.Resamples(d.K, B, alt_seed)
        self._mat, self._vec, self._vec_alt, self._smat = {}, {}, {}, {}
        self.q3, self.q3_cuts = tercile_strata(d.edit) if d.edit else (None, None)

    # ---- cached matrices / bootstrap vectors
    def mat(self, k):
        if k not in self._mat:
            self._mat[k] = L.pair_matrices(self.d, self.cols[k])
        return self._mat[k]

    def vec(self, k, alt=False):
        store = self._vec_alt if alt else self._vec
        if k not in store:
            store[k] = L.boot_vec(*self.mat(k), self.res_alt if alt else self.res)
        return store[k]

    def smat(self, k, kind, only=None):
        key = (k, kind, only)
        if key not in self._smat:
            st = self.d.edit if kind == "edit" else self.q3
            self._smat[key] = L.pair_matrices(self.d, self.cols[k], st, only)
        return self._smat[key]

    def auroc(self, k):
        return L.auroc_from_matrices(*self.mat(k))

    # ---- single predictor summary
    def single(self, k, thr=None):
        s, y, d = self.cols[k], self.d.y, self.d
        out = {"auroc": self.auroc(k), "auroc_ms": L.auroc(s, y), "ci95": L.pct_ci(self.vec(k)), "ci95_alt_seed": L.pct_ci(self.vec(k, True)),
               "ci95_interp": L.pct_ci(self.vec(k), "interp"), "boot_sd": L.sd(self.vec(k)), "auprc": L.auprc(s, y), "cliffs_delta": L.cliffs_delta(s, y),
               "n_unique_scores": len(set(s))}
        if thr is not None:
            out["prf_at_train_thr"] = {"thr": thr, **L.prf(s, y, thr)}
        out["perm_p_one_sided_vs_0.5"] = L.perm_label_auroc_p(d, s, B=self.B)
        if d.edit:
            out["exact_edit_auroc"] = self.strat_point(k, "edit")
            out["terciles"] = self.tercile_table(k)
        if d.group:
            out["matched_concordance"] = L.concordance_boot(L.matched_sets(d, s), None, d.K, self.res)
        return out

    def strat_point(self, k, kind, only=None):
        U, D = self.smat(k, kind, only)
        pt = L.auroc_from_matrices(U, D)
        vec = L.boot_vec(U, D, self.res)
        return {"auroc": pt, "ci95": L.pct_ci(vec) if pt is not None else [None, None], "n_cross_pairs": sum(sum(r) for r in D)}

    def tercile_table(self, k):
        return [dict(self.strat_point(k, "q3", t), stratum=t, n=sum(1 for z in self.q3 if z == t)) for t in range(3)]

    # ---- paired comparison a - b
    def compare(self, a, b, full=True):
        d = self.d
        pa, pb = self.auroc(a), self.auroc(b)
        r = L.delta_boot(pa, pb, self.vec(a), self.vec(b))
        r["delta_alt_seed"] = L.delta_boot(pa, pb, self.vec(a, True), self.vec(b, True))
        r["auroc_a"], r["auroc_b"] = pa, pb
        r["ci95_a"], r["ci95_b"] = L.pct_ci(self.vec(a)), L.pct_ci(self.vec(b))
        if not full:
            return r
        jk = L.jackknife_delta(d, *self.mat(a), *self.mat(b))
        r["jackknife_t"] = {k: v for k, v in jk.items() if k != "loo"}
        # LOPO influence on delta
        loo = jk["loo"]
        r["lopo"] = {"delta_without": {key: loo[i] for i, key in enumerate(d.keys)},
                     "min": min(x for x in loo if x is not None), "max": max(x for x in loo if x is not None),
                     "max_abs_influence": max(abs(r["delta"] - x) for x in loo if x is not None),
                     "most_influential": max(range(d.K), key=lambda i: abs(r["delta"] - loo[i]) if loo[i] is not None else -1),
                     "sign_flips": sum(1 for x in loo if x is not None and x * r["delta"] < 0)}
        r["lopo"]["most_influential"] = d.keys[r["lopo"]["most_influential"]]
        sa, sb = self.cols[a], self.cols[b]
        dl = L.delong_test(sa, sb, d.y)
        r["delong"] = dl
        r["se_ratio_cluster_over_delong"] = r["boot_sd"] / dl["se"] if dl["se"] else None
        r["design_effect_delta"] = (r["boot_sd"] / dl["se"]) ** 2 if dl["se"] else None
        pl = [x - z for x, z in zip(L.placements(sa, d.y), L.placements(sb, d.y))]
        icc, n0, k_, *_ = L.icc1(pl, d.cluster)
        r["icc_placement_diff"] = {"icc1": icc, "n0": n0, "design_effect": 1 + (d.n / d.K - 1) * icc}
        r["perm_label_delta_p"] = L.perm_label_delta_p(d, sa, sb, B=self.B)
        # per-program
        ppa, ppb = L.per_program_auroc(d, sa), L.per_program_auroc(d, sb)
        dif = [ppa[k] - ppb[k] if ppa[k] is not None and ppb[k] is not None else None for k in d.keys]
        sp, w, l = L.sign_test_p(dif)
        wp, _ = L.wilcoxon_exact_p(dif)
        wts = L.program_weights(d)
        r["per_program"] = {"a_higher": w, "a_lower": l, "ties": len([x for x in dif if x is not None]) - w - l, "sign_p": sp, "wilcoxon_p": wp,
                            "signflip_weighted_p": L.signflip_weighted_p(dif, [wts[k] for k in d.keys]),
                            "mean_diff": sum(x for x in dif if x is not None) / len([x for x in dif if x is not None]),
                            "diffs": {k: x for k, x in zip(d.keys, dif)}}
        # matched-set concordance (clustered by program)
        if d.group:
            r["matched_concordance"] = L.concordance_boot(L.matched_sets(d, sa), L.matched_sets(d, sb), d.K, self.res)
        # edit-size stratified delta with cluster CI
        if d.edit:
            r["exact_edit"] = self._strat_delta(a, b, "edit")
            r["terciles"] = [dict(self._strat_delta(a, b, "q3", t), stratum=t) for t in range(3)]
        # power / MDE
        K = d.K
        se = r["boot_sd"]
        r["power"] = {"se_cluster_boot": se, "df": K - 1, **L.mde(se, K - 1), **{f"holm19_{k}": v for k, v in L.mde(se, K - 1, ALPHA / HOLM_M).items()},
                      "power_at_0.03": L.power_at(0.03, se, K - 1), "power_at_0.05": L.power_at(0.05, se, K - 1), "power_at_0.10": L.power_at(0.10, se, K - 1)}
        return r

    def _strat_delta(self, a, b, kind, only=None):
        Ua, Da = self.smat(a, kind, only)
        Ub, Db = self.smat(b, kind, only)
        pa, pb = L.auroc_from_matrices(Ua, Da), L.auroc_from_matrices(Ub, Db)
        if pa is None:
            return {"a": None, "b": None, "delta": None}
        va, vb = L.boot_vec(Ua, Da, self.res), L.boot_vec(Ub, Db, self.res)
        r = L.delta_boot(pa, pb, va, vb)
        return {"a": pa, "b": pb, "delta": r["delta"], "ci95": r["ci95"], "p_boot_plain": r["p_boot_plain"], "p_boot_corrected": r["p_boot_corrected"],
                "n_cross_pairs": sum(sum(x) for x in Da)}


def verdict(delta, ci, holm_p, mde_t):
    """Pre-declared rule (see 05b report): Holm-adjusted two-sided cluster-bootstrap p < .05 AND raw CI excludes 0 -> SUPERIOR/INFERIOR by sign;
    otherwise NOT DISTINGUISHABLE (with the MDE caveat)."""
    sig = holm_p is not None and holm_p < ALPHA and (ci[0] > 0 or ci[1] < 0)
    if sig:
        return "SUPERIOR" if delta > 0 else "INFERIOR"
    return "NOT DISTINGUISHABLE"


def robustness(res):
    """Does the verdict direction also hold under independent inference methods? Returns dict of boolean flags (raw alpha=.05, not family-adjusted)."""
    d = res["delta"]
    s = 1 if d > 0 else -1
    return {"alt_seed_ci_excludes0": (res["delta_alt_seed"]["ci95"][0] > 0 or res["delta_alt_seed"]["ci95"][1] < 0),
            "jackknife_t_p<.05": res["jackknife_t"]["p_t"] < ALPHA,
            "delong_p<.05(anticonservative)": res["delong"]["p"] < ALPHA,
            "perm_label_p<.05": res["perm_label_delta_p"] < ALPHA,
            "per_program_signflip_p<.05": res["per_program"]["signflip_weighted_p"] < ALPHA,
            "sign_test_p<.05": res["per_program"]["sign_p"] < ALPHA,
            "wilcoxon_p<.05": res["per_program"]["wilcoxon_p"] < ALPHA,
            "lopo_no_sign_flip": res["lopo"]["sign_flips"] == 0,
            "direction": s}


# ----------------------------------------------------------------------------------------------- population-level driver
def dedup_indices(rows):
    """Keep first (by pair_id) of every (program, label, variant-AST) group."""
    seen, keep = set(), []
    for i in sorted(range(len(rows)), key=lambda i: rows[i]["pair_id"]):
        r = rows[i]
        key = (r["base_id"], r["label"], L.ast_hash(r["variant_path"]))
        if key not in seen:
            seen.add(key)
            keep.append(i)
    return sorted(keep)


def clean_val_indices(rows, scenario):
    """v9c_val clean-label subsets from A3's noisy-pair list (EXP-A3-008, read-only): S1 drop sets with an output-differing EQUIVALENT,
    S2 drop sets with a CHANGED pair that shows no output difference, S3 both.  Whole matched sets are removed."""
    import json
    pl = {r["pair_id"]: r for r in json.loads((L.PKG / "results/raw/EXP-A3-008/v9c_val_pair_level.json").read_text())}
    bad_groups = set()
    for r in rows:
        a = pl[r["pair_id"]]["cmp"]["any_strict"] > 0
        if r["label"] == 0 and a and scenario in ("S1", "S3"):
            bad_groups.add(r["group"])
        if r["label"] == 1 and not a and scenario in ("S2", "S3"):
            bad_groups.add(r["group"])
    return [i for i, r in enumerate(rows) if r["group"] not in bad_groups]


def subset_cols(cols, idx):
    return {k: [v[i] for i in idx] for k, v in cols.items()}


def analyse(pop, rows, cols, ref, others, family, thr=None, subsets=None, B=2000, log=print):
    """Full verification of `ref` vs each of `others` on one population.  Holm/BH over `family` (subset of `others`), declared m = HOLM_M."""
    d = L.data_from_rows(rows)
    E = Engine(d, cols, B=B)
    thr = thr or {}
    out = {"pop": pop, "n": d.n, "programs": d.K, "single": {}, "cmp": {}}
    for k in [ref] + others:
        out["single"][k] = E.single(k, thr.get(k))
    for o in others:
        out["cmp"][o] = E.compare(ref, o)
        log(f"  [{pop}] {ref} - {o}: d={out['cmp'][o]['delta']:+.4f}", flush=True)
    for pkey in ("p_boot_plain", "p_boot_corrected"):
        fam = {o: out["cmp"][o][pkey] for o in family if o in out["cmp"]}
        out[f"holm_{pkey}"] = {"adj": L.holm(fam, m=max(HOLM_M, len(fam))), "adj_over_available_only": L.holm(fam), "bh_sensitivity": L.benjamini_hochberg(fam, m=max(HOLM_M, len(fam)))}
    for o in others:
        c = out["cmp"][o]
        hp = out["holm_p_boot_corrected"]["adj"].get(o)
        c["holm_p"] = hp
        c["holm_p_plain"] = out["holm_p_boot_plain"]["adj"].get(o)
        c["verdict"] = verdict(c["delta"], c["ci95"], hp, c["power"]["mde_t"]) if hp is not None else "NOT IN FAMILY (descriptive)"
        c["robustness"] = robustness(c)
    if subsets:
        out["subsets"] = {}
        for sn, idx in subsets.items():
            sd_ = L.data_from_rows([rows[i] for i in idx])
            Es = Engine(sd_, subset_cols(cols, idx), B=B)
            sub = {"n": sd_.n, "programs": sd_.K, "ref_auroc": Es.auroc(ref), "cmp": {}}
            for o in others:
                r = Es.compare(ref, o, full=False)
                sub["cmp"][o] = {"auroc_o": r["auroc_b"], "delta": r["delta"], "ci95": r["ci95"], "p_boot_corrected": r["p_boot_corrected"]}
            out["subsets"][sn] = sub
    return out


# ----------------------------------------------------------------------------------------------- incremental value
LEARNERS = ("lr", "zsum", "rankavg")


def _fit(kind, X, y):
    if kind == "lr":                      # repo-recipe objective (penalty 2*L2*w/n), exact optimum by Newton
        return L.fit_logistic_newton(X, y, l2=2.0)
    if kind == "zsum":
        return L.fit_zsum(X, y)
    if kind == "rankavg":
        return L.fit_rankavg(X, y)
    raise ValueError(kind)


def _apply(kind, m, x):
    return {"lr": L.logit_apply, "zsum": L.zsum_apply, "rankavg": L.rankavg_apply}[kind](m, x)


def combiner_scores(kind, feats, tr_cols, ytr, pop_cols):
    """Fit combiner `kind` on TRAIN columns (feats = list of column names) and score the held-out columns."""
    Xtr = [[tr_cols[f][i] for f in feats] for i in range(len(ytr))]
    m = _fit(kind, Xtr, ytr)
    n = len(pop_cols[feats[0]])
    return [_apply(kind, m, [pop_cols[f][i] for f in feats]) for i in range(n)], m


def incremental_matrix(E, tr_cols, ytr, bases, xs, learners=LEARNERS):
    """For each base feature set (name -> list of columns), each extra component x and each learner:  AUROC(base+x) - AUROC(base) on the Engine's
    population (paired cluster bootstrap, same resamples).  Combined columns are added to the engine."""
    out = []
    for bn, bf in bases.items():
        for kind in learners:
            sb, _ = combiner_scores(kind, bf, tr_cols, ytr, E.cols)
            kb = f"__inc_{kind}_{bn}"
            E.cols[kb] = sb
            for x in xs:
                if x in bf:
                    continue
                sa, _ = combiner_scores(kind, bf + [x], tr_cols, ytr, E.cols)
                ka = f"__inc_{kind}_{bn}+{x}"
                E.cols[ka] = sa
                r = E.compare(ka, kb, full=False)
                out.append({"base": bn, "x": x, "learner": kind, "auroc_base": r["auroc_b"], "auroc_aug": r["auroc_a"], "delta": r["delta"], "ci95": r["ci95"],
                            "p_boot_plain": r["p_boot_plain"], "p_boot_corrected": r["p_boot_corrected"], "boot_sd": r["boot_sd"]})
    return out
