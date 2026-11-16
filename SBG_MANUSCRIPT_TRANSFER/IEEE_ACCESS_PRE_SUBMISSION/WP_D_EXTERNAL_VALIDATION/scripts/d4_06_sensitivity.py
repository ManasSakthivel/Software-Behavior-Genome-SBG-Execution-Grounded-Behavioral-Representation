"""d4_06_sensitivity.py -- Task 6 (POST-HOC SENSITIVITY; none of these variants is pre-registered).

For the four score configurations  BP-v7 / BP-v8 / QC-v7 / QC-v8  (sbg_v5; v7 = committed artifacts, v8 = EXTERNAL_RESCORE_V8)
  1  pair-set adjustments : as-is, ex-SP-2, ex-invalid-SP-2 (7), ex-contaminated-bases (3 BP / 1 QC),
                            combinations, positives vs a single negative type, one bug per unit-family (dedup of
                            repeated functions such as youtube-dl js_to_json), without youtube-dl
  2  unevaluated-pair imputation (53 BugsInPy rows; 1 QuixBugs-v8 row): score 0 (prereg ALL), score 0.5, neutral
     (every pair involving an unevaluated member credited 0.5), and Manski worst/best-case bounds
  3  leave-one-cluster-out (bug, project, unit-family): min / max / sd and the most influential clusters
Outputs: raw/WPD-D4_stats/06_sensitivity.json , 06_sensitivity_table.csv
"""
import csv
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from d4_lib import *  # noqa
from d4_sets import *  # noqa

C = load_corpora()
audit = json.load(open(INPUT_FILES["EXTERNAL_NEGATIVE_AUDIT"]))
INV = invalid_sp2_ids(audit)

CONFIGS = {"BP-v7": ("bugsinpy", "s7", "ev7"), "BP-v8": ("bugsinpy", "s8", "ev8"),
           "QC-v7": ("quixbugs_canonical", "s7", "ev7"), "QC-v8": ("quixbugs_canonical", "s8", "ev8")}


def auc_of(recs, src):
    sc = vecs(recs, "sbg_v5", src, 0.0)
    lab = [r["label"] for r in recs]
    return auroc(sc, lab)


def adjust(recs, evk, flt, cont):
    ok = lambda r: bool(r[evk])
    f = {"as-is": lambda r: True,
         "ex-SP-2": lambda r: r["kind"] != "SP-2",
         "ex-invalid-SP-2(7)": lambda r: r["pair_id"] not in INV,
         "ex-contaminated-bases": lambda r: r["base_path"] not in cont,
         "ex-SP-2 & ex-contaminated": lambda r: r["kind"] != "SP-2" and r["base_path"] not in cont,
         "ex-invalid-SP-2 & ex-contaminated": lambda r: r["pair_id"] not in INV and r["base_path"] not in cont,
         "ex-SP-2 & ex-youtube-dl": lambda r: r["kind"] != "SP-2" and r["project"] != "youtube-dl",
         "ex-youtube-dl": lambda r: r["project"] != "youtube-dl"}[flt]
    return [r for r in recs if ok(r) and f(r)]


def dedup_family(recs):
    first = {}
    for r in sorted(recs, key=lambda r: r["bug"]):
        first.setdefault(r["family"], r["bug"])
    return [r for r in recs if first[r["family"]] == r["bug"]]


def with_unev(recs, evk, src, mode, drop_sp2=False):
    E = [r for r in recs if r[evk] and not (drop_sp2 and r["kind"] == "SP-2")]
    U = [r for r in recs if not r[evk] and not (drop_sp2 and r["kind"] == "SP-2")]
    if not U:
        return auc_of(E, src), 0
    Pu = sum(r["label"] for r in U)
    Nu = len(U) - Pu
    sc_e = vecs(E, "sbg_v5", src, 0.0)
    lab_e = [r["label"] for r in E]
    Pe, Ne = sum(lab_e), len(lab_e) - sum(lab_e)
    if mode in ("zero", "half", "worst", "best"):
        pv = {"zero": (0.0, 0.0), "half": (0.5, 0.5), "worst": (-1.0, 2.0), "best": (2.0, -1.0)}[mode]
        sc = sc_e + [pv[0] if r["label"] == 1 else pv[1] for r in U]
        lab = lab_e + [r["label"] for r in U]
        return auroc(sc, lab), len(U)
    if mode == "neutral":
        cred = auroc(sc_e, lab_e) * Pe * Ne
        N = (Pe + Pu) * (Ne + Nu)
        cred += 0.5 * (N - Pe * Ne)
        return cred / N, len(U)


out = {"script": "scripts/d4_06_sensitivity.py", "status": "POST-HOC SENSITIVITY", "input_manifest": input_manifest(),
       "pair_set_adjustments": {}, "unevaluated_imputation": {}, "leave_one_cluster_out": {}}
rows = []
for cname, (corpus, src, evk) in CONFIGS.items():
    recs = C[corpus]
    cont = contaminated(recs)
    d = {}
    for flt in ["as-is", "ex-SP-2", "ex-invalid-SP-2(7)", "ex-contaminated-bases", "ex-SP-2 & ex-contaminated",
                "ex-invalid-SP-2 & ex-contaminated", "ex-youtube-dl", "ex-SP-2 & ex-youtube-dl"]:
        if corpus != "bugsinpy" and ("youtube" in flt or "invalid" in flt):
            continue
        sub = adjust(recs, evk, flt, cont)
        a = auc_of(sub, src)
        d[flt] = {"n": len(sub), "n_pos": sum(r["label"] for r in sub), "auroc": round(a, 4),
                  "n_clusters_bug": len({r["bug"] for r in sub})}
    base = adjust(recs, evk, "as-is", cont)
    for tag, sub in (("one-bug-per-unit-family", dedup_family(base)),
                     ("one-bug-per-unit-family & ex-SP-2", [r for r in dedup_family(base) if r["kind"] != "SP-2"])):
        d[tag] = {"n": len(sub), "n_pos": sum(r["label"] for r in sub), "auroc": round(auc_of(sub, src), 4),
                  "n_clusters_bug": len({r["bug"] for r in sub})}
    kinds = sorted({r["kind"] for r in base if r["kind"] != "real"})
    d["positives_vs_single_negative_type"] = {}
    for k in kinds:
        sub = [r for r in base if r["kind"] in ("real", k)]
        d["positives_vs_single_negative_type"][k] = {"n_neg": sum(1 for r in sub if r["label"] == 0),
                                                      "auroc": round(auc_of(sub, src), 4)}
    out["pair_set_adjustments"][cname] = d
    for k, v in d.items():
        if k != "positives_vs_single_negative_type":
            rows.append([cname, "pair-set", k, v["n"], v["n_pos"], v["auroc"]])
    for k, v in d["positives_vs_single_negative_type"].items():
        rows.append([cname, "pos-vs-single-negative-type", k, v["n_neg"], "", v["auroc"]])
    imp = {}
    for drop in (False, True):
        key = "ex-SP-2" if drop else "all-negative-types"
        imp[key] = {}
        for mode in ("zero", "half", "neutral", "worst", "best"):
            a, nu = with_unev(recs, evk, src, mode, drop)
            imp[key][mode] = round(a, 4)
            rows.append([cname, "unevaluated-imputation(%s)" % key, mode, nu, "", round(a, 4)])
        imp[key]["n_unevaluated_rows"] = nu
    out["unevaluated_imputation"][cname] = imp
    loco = {}
    for flt in ("as-is", "ex-SP-2"):
        sub = adjust(recs, evk, flt, cont)
        sc = vecs(sub, "sbg_v5", src, 0.0)
        lab = [r["label"] for r in sub]
        theta = auroc(sc, lab)
        for lv, cl in (("bug", bug_cluster(sub)), ("project", project_cluster(sub)), ("unit_family", family_cluster(sub))):
            if lv == "project" and corpus != "bugsinpy":
                continue
            g = {}
            for i, c in enumerate(cl):
                g.setdefault(c, []).append(i)
            keys = list(g)
            jk = jackknife_clusters(sc, lab, list(g.values()))
            vals = [(keys[gi], a) for gi, a in jk if a is not None]
            av = [a for _, a in vals]
            vals_sorted = sorted(vals, key=lambda t: abs(t[1] - theta), reverse=True)
            loco["%s|%s" % (flt, lv)] = {"theta": round(theta, 4), "n_clusters": len(keys), "min": round(min(av), 4),
                                         "max": round(max(av), 4), "sd": round(statistics.pstdev(av), 4),
                                         "n_loco_ge_0.5": sum(1 for a in av if a >= 0.5),
                                         "n_degenerate_dropped": len(jk) - len(vals),
                                         "most_influential": [(k, round(a, 4)) for k, a in vals_sorted[:4]]}
            rows.append([cname, "LOCO %s" % lv, flt, len(keys), "", "%.4f..%.4f" % (min(av), max(av))])
    out["leave_one_cluster_out"][cname] = loco
    print(cname, json.dumps({k: v["auroc"] for k, v in d.items() if k != "positives_vs_single_negative_type"}), flush=True)
    print("   imputation", json.dumps(imp), flush=True)
    print("   single-type", json.dumps({k: v["auroc"] for k, v in d["positives_vs_single_negative_type"].items()}), flush=True)
    for k, v in loco.items():
        print("   LOCO", k, v["min"], v["max"], v["most_influential"][:2], flush=True)
write_json("06_sensitivity.json", out)
with open(OUT / "06_sensitivity_table.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["config", "kind", "variant", "n", "n_pos", "auroc_or_range"])
    w.writerows(rows)
