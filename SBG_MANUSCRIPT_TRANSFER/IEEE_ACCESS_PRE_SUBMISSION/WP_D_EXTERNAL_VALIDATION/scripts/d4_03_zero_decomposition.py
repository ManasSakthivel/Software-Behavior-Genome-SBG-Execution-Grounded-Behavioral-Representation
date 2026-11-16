"""d4_03_zero_decomposition.py -- Task 3 (POST-HOC DESCRIPTIVE / EXPLORATORY; nothing here is pre-registered).

For sbg_v5 on every analysis set:
  * fraction of positives vs negatives with score exactly 0 (Wilson CI, Fisher exact both directions,
    cluster-bootstrap CI of the hurdle difference);
  * exact AUROC identity   AUROC = w_pos>0,neg=0  +  0.5 * w_both0  +  w_both>0 * AUROC(cond)  [+ 0 * w_pos0,neg>0];
  * tie mass and AUROC under ties->0 / 0.5 / 1 (tie-handling bounds);
  * AUROC restricted to pairs with score>0 ("observable subset").  THIS CONDITIONS ON THE OUTCOME-SIDE SCORE:
    it is a post-hoc selection and NOT an unbiased estimate of anything; reported for decomposition only.
  * AUROC of the binary detector 1[score>0].
Outputs: raw/WPD-D4_stats/03_zero_decomposition.json , 03_zero_decomposition.csv
"""
import csv
import json
import random
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from d4_lib import *  # noqa
from d4_sets import *  # noqa

B = 5000
C = load_corpora()
audit = json.load(open(INPUT_FILES["EXTERNAL_NEGATIVE_AUDIT"]))
S = get_sets(C, audit)


def hurdle_stat(sc, lab, idx):
    p = [sc[i] > 0 for i in idx if lab[i] == 1]
    n = [sc[i] > 0 for i in idx if lab[i] == 0]
    if not p or not n:
        return None
    return sum(p) / len(p) - sum(n) / len(n)


def boot_hurdle(sc, lab, groups, seed):
    rng = random.Random(seed)
    G = len(groups)
    vals = []
    for _ in range(B):
        idx = []
        for _g in range(G):
            idx.extend(groups[rng.randrange(G)])
        v = hurdle_stat(sc, lab, idx)
        if v is not None:
            vals.append(v)
    vals.sort()
    return [round(quantile(vals, .025), 4), round(quantile(vals, .975), 4)]


out = {"script": "scripts/d4_03_zero_decomposition.py", "status": "POST-HOC DESCRIPTIVE", "B": B,
       "input_manifest": input_manifest(), "sets": {}}
csvrows = []
for sid, s in S.items():
    recs = s["recs"]
    sc = vecs(recs, "sbg_v5", s["src"], s["impute"])
    lab = [r["label"] for r in recs]
    pos = [x for x, y in zip(sc, lab) if y == 1]
    neg = [x for x, y in zip(sc, lab) if y == 0]
    npos, nneg = len(pos), len(neg)
    pz, nz = sum(1 for x in pos if x == 0), sum(1 for x in neg if x == 0)
    hurdle_pos, hurdle_neg = (npos - pz) / npos, (nneg - nz) / nneg
    fe = fisher_exact(npos - pz, pz, nneg - nz, nz)  # a=pos nonzero, c=neg nonzero
    # pair-level identity
    w1 = w2 = w3 = w4 = 0
    gt4 = eq4 = 0
    for p in pos:
        for q in neg:
            if p > 0 and q == 0:
                w1 += 1
            elif p == 0 and q == 0:
                w2 += 1
            elif p == 0 and q > 0:
                w3 += 1
            else:
                w4 += 1
                gt4 += p > q
                eq4 += p == q
    N = npos * nneg
    theta = auroc(sc, lab)
    cond_auc = (gt4 + 0.5 * eq4) / w4 if w4 else None
    ident = (w1 + 0.5 * w2 + (gt4 + 0.5 * eq4)) / N
    lo, mid, hi = auroc_tie_bounds(sc, lab)
    # restricted to score>0
    keep = [i for i, x in enumerate(sc) if x > 0]
    sc_r = [sc[i] for i in keep]
    lab_r = [lab[i] for i in keep]
    cond_set_auc = auroc(sc_r, lab_r)
    cond_ci = None
    if cond_set_auc is not None:
        rr = [recs[i] for i in keep]
        g = groups_of(bug_cluster(rr))
        bt = cluster_boot({"x": sc_r}, lab_r, g, B=B, seed=zlib.crc32(sid.encode()) + 3)["x"]
        cond_ci = ci_from_boot(cond_set_auc, bt)["percentile"]
    # binary detector AUROC and hurdle CI
    bin_sc = [1.0 if x > 0 else 0.0 for x in sc]
    d = {"status": s["status"], "n_pos": npos, "n_neg": nneg, "auroc": round(theta, 4),
         "pos_zero": pz, "pos_zero_frac": round(pz / npos, 4), "pos_zero_wilson95": wilson(pz, npos),
         "neg_zero": nz, "neg_zero_frac": round(nz / nneg, 4), "neg_zero_wilson95": wilson(nz, nneg),
         "P(score>0|pos)": round(hurdle_pos, 4), "P(score>0|neg)": round(hurdle_neg, 4),
         "hurdle_diff": round(hurdle_pos - hurdle_neg, 4),
         "hurdle_diff_cluster_boot_ci95_bug": boot_hurdle(sc, lab, groups_of(bug_cluster(recs)), zlib.crc32(sid.encode()) + 4),
         "fisher_exact_p_two_sided": round(fe["p_two_sided"], 6),
         "fisher_p_posNonzero_less_than_expected(pos<neg)": round(fe["p_a_le"], 6),
         "fisher_p_posNonzero_greater_than_expected(pos>neg)": round(fe["p_a_ge"], 6),
         "pair_decomposition": {"pos>0&neg=0": w1, "both=0 (tie)": w2, "pos=0&neg>0 (loss)": w3,
                                "both>0": w4, "n_pairs": N,
                                "shares": {"pos>0&neg=0": round(w1 / N, 4), "both=0": round(w2 / N, 4),
                                           "pos=0&neg>0": round(w3 / N, 4), "both>0": round(w4 / N, 4)},
                                "auroc_both_pos_cond(post-hoc-selected)": None if cond_auc is None else round(cond_auc, 4),
                                "identity_check": round(ident, 6)},
         "tie_mass_all_ties": round((w2 + eq4) / N, 4),
         "tie_mass_at_zero": round(w2 / N, 4),
         "auroc_ties_as_0 / 0.5 / 1": [round(lo, 4), round(mid, 4), round(hi, 4)],
         "auroc_restricted_to_score_gt_0 (POST-HOC SELECTION ON SCORE; biased)": {
             "n": len(keep), "n_pos": sum(lab_r), "n_neg": len(lab_r) - sum(lab_r),
             "auroc": None if cond_set_auc is None else round(cond_set_auc, 4),
             "bug_cluster_boot_ci95": cond_ci},
         "auroc_binary_detector_1[score>0]": round(auroc(bin_sc, lab), 4)}
    out["sets"][sid] = d
    csvrows.append([sid, s["status"], npos, nneg, d["pos_zero_frac"], d["neg_zero_frac"], d["hurdle_diff"],
                    d["fisher_exact_p_two_sided"], d["tie_mass_all_ties"], d["auroc"],
                    d["auroc_ties_as_0 / 0.5 / 1"][0], d["auroc_ties_as_0 / 0.5 / 1"][2],
                    d["auroc_restricted_to_score_gt_0 (POST-HOC SELECTION ON SCORE; biased)"]["auroc"],
                    d["auroc_binary_detector_1[score>0]"]])
    print(sid, "pos0=%.2f neg0=%.2f ties=%.2f auc=%.3f cond=%s bounds=%s ident=%.4f" % (
        d["pos_zero_frac"], d["neg_zero_frac"], d["tie_mass_all_ties"], theta,
        d["auroc_restricted_to_score_gt_0 (POST-HOC SELECTION ON SCORE; biased)"]["auroc"],
        d["auroc_ties_as_0 / 0.5 / 1"], ident))
write_json("03_zero_decomposition.json", out)
with open(OUT / "03_zero_decomposition.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["set", "status", "n_pos", "n_neg", "pos_zero_frac", "neg_zero_frac", "hurdle_diff", "fisher_p2",
                "tie_mass", "auroc", "auroc_ties0", "auroc_ties1", "auroc_gt0_only_POSTHOC", "auroc_binary_detector"])
    w.writerows(csvrows)
