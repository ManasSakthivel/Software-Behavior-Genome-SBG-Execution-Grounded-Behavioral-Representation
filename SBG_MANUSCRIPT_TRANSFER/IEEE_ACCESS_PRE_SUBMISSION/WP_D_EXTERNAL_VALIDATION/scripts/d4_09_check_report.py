"""d4_09_check_report.py -- assert that headline narrative numbers in STATS_REPORT.md match the JSON/CSV outputs.
Reads only raw/WPD-D4_stats/*. Exit code 1 on any mismatch."""
import csv
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "raw" / "WPD-D4_stats"
rep = (OUT / "STATS_REPORT.md").read_text()
J = lambda n: json.load(open(OUT / n))
inf = J("02_inference.json")["results"]
zd = {r["set"]: r for r in csv.DictReader(open(OUT / "03_zero_decomposition.csv"))}
bl = J("04_baselines.json")["sets"]
pw = J("05_power.json")
sens = list(csv.DictReader(open(OUT / "06_sensitivity_table.csv")))
fk = J("07_forking_paths.json")
bad = []


def need(label, text):
    if text not in rep:
        bad.append((label, text))


def r(x, nd):
    return f"{x:.{nd}f}"


# headline AUROC / CI / p
for sid, lv, tag in [("BP-v7-EVAL", "bug", "a"), ("BP-v7-EVAL", "project", "b"), ("QC-v7-ALL", "bug", "c"), ("BP-v8-exSP2", "bug", "d"),
                     ("BP-v8-exSP2", "project", "e"), ("QC-v8-exSP2", "bug", "f"), ("QD-v7-EVAL", "bug", "g"), ("QD-v7-ALL", "bug", "h")]:
    d = inf[sid]["levels"][lv]
    lo, hi = d["ci95"]["percentile"]
    need(f"{sid}/{lv} CI", f"[{r(lo, 3)}, {r(hi, 3)}]")
    need(f"{sid} auroc", r(inf[sid]["auroc"], 4))

pl = lambda sid, lv: inf[sid]["levels"][lv]["perm_within_cluster"]
checks = [
    ("BP-v7-EVAL p lower bug", r(pl("BP-v7-EVAL", "bug")["p_auroc_lt_0.5_lower_tail"], 3), "0.015"),
    ("BP-v7-EVAL p lower project", r(pl("BP-v7-EVAL", "project")["p_auroc_lt_0.5_lower_tail"], 3), "0.031"),
    ("QC-v7-ALL p lower", r(pl("QC-v7-ALL", "bug")["p_auroc_lt_0.5_lower_tail"], 3), "0.007"),
    ("QC-v8-exSP2 p lower", r(pl("QC-v8-exSP2", "bug")["p_auroc_lt_0.5_lower_tail"], 3), "0.087"),
    ("BP-v8-exSP2 p lower", r(pl("BP-v8-exSP2", "bug")["p_auroc_lt_0.5_lower_tail"], 2), "0.53"),
    ("BP-v8-exSP2 p upper", r(pl("BP-v8-exSP2", "bug")["p_auroc_gt_0.5_upper_tail"], 2), "0.47"),
    ("QD-v7-EVAL p upper", r(pl("QD-v7-EVAL", "bug")["p_auroc_gt_0.5_upper_tail"], 4), "0.0003"),
    ("QD-v7-ALL p upper", r(pl("QD-v7-ALL", "bug")["p_auroc_gt_0.5_upper_tail"], 3), "0.011"),
    ("BP-v8-exSP2 project P(theta>=0.6)", r(inf["BP-v8-exSP2"]["levels"]["project"]["boot_P(theta*>=x)"]["0.6"], 3), "0.023"),
    ("BP-v8-exSP2 one-sided upper project", r(inf["BP-v8-exSP2"]["levels"]["project"]["one_sided_95_upper_bound"], 3), "0.579"),
    ("BP-v8-exSP2 one-sided upper bug", r(inf["BP-v8-exSP2"]["levels"]["bug"]["one_sided_95_upper_bound"], 3), "0.577"),
]
for lab, got, want in checks:
    if got != want:
        bad.append((lab + " computed != narrative", f"{got} vs {want}"))

# zero decomposition
for sid, fz in [("BP-v7-EVAL", "0.020"), ("QC-v7-ALL", "0.0007")]:
    got = r(float(zd[sid]["fisher_p2"]), 3 if fz == "0.020" else 4)
    if got != fz:
        bad.append((f"fisher {sid}", f"{got} vs {fz}"))
if r(float(zd["QC-v8-exSP2"]["auroc_ties0"]), 3) != "0.177" or r(float(zd["QC-v8-exSP2"]["auroc_ties1"]), 3) != "0.712":
    bad.append(("QC ties", ""))
if r(float(zd["BP-v8-exSP2"]["auroc_ties0"]), 3) != "0.334" or r(float(zd["BP-v8-exSP2"]["auroc_ties1"]), 3) != "0.660":
    bad.append(("BP ties", ""))
vals = [float(x["auroc_gt0_only_POSTHOC"]) for x in zd.values()]
if not (0.55 <= min(vals) and max(vals) <= 0.96):
    bad.append(("gt0 range", f"{min(vals)}..{max(vals)}"))

# bootstrap tail: >=0.7 / 0.75 / 0.897 <= 0.001 in all BugsInPy & QC sets
for sid, v in inf.items():
    if sid.startswith(("BP", "QC")):
        for lv, d in v["levels"].items():
            for t in ("0.7", "0.75", "0.897"):
                if d["boot_P(theta*>=x)"][t] > 0.001:
                    bad.append(("tail>0", f"{sid} {lv} {t} {d['boot_P(theta*>=x)'][t]}"))

# baselines
b = bl["BP-v7-EVAL"]["levels"]["bug"]
sa = b["paired_vs_sbg_v5"]["static_ast"]
if (r(sa["delta"], 3), sa["holm_adj_p_over_prereg_family"]) != ("0.226", 0.002):
    bad.append(("static_ast delta/holm", str(sa)))
for p in ("static_token", "exception_fraction", "call_count", "sbg_v3"):
    if b["paired_vs_sbg_v5"][p]["holm_adj_p_over_prereg_family"] < 0.05:
        bad.append(("BP baseline significant but narrative says not", p))
q = bl["QC-v7-ALL"]["levels"]["bug"]
for p in ("call_count", "exception_fraction"):
    if not (q["paired_vs_sbg_v5"][p]["holm_adj_p_over_prereg_family"] < 0.05 and q["paired_vs_sbg_v5"][p]["delta"] > 0):
        bad.append(("QC baseline should beat sbg_v5 after Holm", p + str(q["paired_vs_sbg_v5"][p])))
if q["predictors"]["static_token"]["auroc"] != 0.2095:
    bad.append(("QC static_token", ""))

# power
for sid, want in {"BP-v7-EVAL": (0.614, 0.648, 0.642, 0.671), "BP-v8-exSP2": (0.63, 0.658, 0.661, 0.683),
                  "QC-v7-ALL": (0.635, 0.644, None, None), "QC-v8-exSP2": (0.639, 0.651, None, None)}.items():
    allm = []
    for sc in pw["simulation"][sid]["scenarios"].values():
        allm += [v for v in sc["MDE_theta_at_80pct_power"].values() if v]
    if not (0.60 <= min(allm) and max(allm) <= 0.69):
        bad.append(("MDE range", sid))
sizes = [v for d in pw["simulation"].values() for sc in d["scenarios"].values() for v in sc["size_at_mu0"].values()]
if not (0.022 <= min(sizes) and max(sizes) <= 0.040):
    bad.append(("size range", f"{min(sizes)} {max(sizes)}"))

# sensitivity
S = {(x["config"], x["variant"], x["kind"]): x["auroc_or_range"] for x in sens}
exp = [(("BP-v8", "as-is", "pair-set"), "0.4159"), (("BP-v8", "ex-SP-2", "pair-set"), "0.497"), (("BP-v8", "ex-invalid-SP-2(7)", "pair-set"), "0.4453"),
       (("BP-v8", "ex-contaminated-bases", "pair-set"), "0.4059"), (("BP-v8", "ex-SP-2 & ex-contaminated", "pair-set"), "0.4953"),
       (("QC-v8", "as-is", "pair-set"), "0.3842"), (("QC-v8", "ex-SP-2", "pair-set"), "0.4444"), (("QC-v8", "ex-contaminated-bases", "pair-set"), "0.3704"),
       (("BP-v8", "one-bug-per-unit-family", "pair-set"), "0.4817"), (("BP-v8", "one-bug-per-unit-family & ex-SP-2", "pair-set"), "0.5484"),
       (("BP-v8", "ex-youtube-dl", "pair-set"), "0.4486"), (("BP-v8", "ex-SP-2 & ex-youtube-dl", "pair-set"), "0.5146"),
       (("BP-v8", "SP-2", "pos-vs-single-negative-type"), "0.282"), (("QC-v8", "SP-2", "pos-vs-single-negative-type"), "0.2756"),
       (("BP-v8", "worst", "unevaluated-imputation(all-negative-types)"), "0.2266"), (("BP-v8", "best", "unevaluated-imputation(all-negative-types)"), "0.6817"),
       (("BP-v8", "worst", "unevaluated-imputation(ex-SP-2)"), "0.2574"), (("BP-v8", "best", "unevaluated-imputation(ex-SP-2)"), "0.7395"),
       (("BP-v8", "LOCO", "x"), None)]
for k, w in exp:
    if w is None:
        continue
    if S.get(k) != w:
        bad.append(("sens", f"{k} {S.get(k)} vs {w}"))
if S[("BP-v8", "ex-SP-2", "LOCO project")] != "0.4786..0.5219" or S[("BP-v8", "ex-SP-2", "LOCO bug")] != "0.4805..0.5096" \
        or S[("QC-v8", "ex-SP-2", "LOCO bug")] != "0.4256..0.4558":
    bad.append(("LOCO", ""))

# forking
sm = fk["summary"]
if (sm["BugsInPy"]["all_variants"]["n_lt_0.5"], sm["BugsInPy"]["all_variants"]["k"], sm["QuixBugs canonical"]["all_variants"]["k"],
        sm["QuixBugs declared"]["all_variants"]["k"]) != (9, 11, 7, 3):
    bad.append(("forking counts", str(sm)))

if bad:
    print("MISMATCHES:")
    for x in bad:
        print("  ", x)
    sys.exit(1)
print("OK: all checked narrative numbers match outputs")
