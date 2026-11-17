#!/usr/bin/env python
"""Figures from results/processed + results/statistics (EXPLORATORY DEVELOPMENT data). Writes PDF+PNG to results/figures."""
import json, collections
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd

OUT = Path("results/figures"); OUT.mkdir(parents=True, exist_ok=True)
D = pd.read_csv("results/processed/dev_pairs_per_system.csv", dtype=str, keep_default_na=False)
SM = pd.read_csv("results/statistics/system_metrics.csv")
RC = pd.read_csv("results/statistics/risk_coverage.csv")
K1 = [json.loads(l) for l in open("results/processed/k1_spike_per_pair.jsonl")]
K1 = [r for r in K1 if r["tag"] == "run1"]
SYS = ["V7-B", "B1", "B1+rep", "B3", "B4"]
COL = {"V7-B": "#0072B2", "B1": "#E69F00", "B1+rep": "#009E73", "B3": "#CC79A7", "B4": "#999999"}
NOTE = "EXPLORATORY DEVELOPMENT data (non-pristine; V7-B shaped by these pairs)"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})

def save(fig, name):
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)

# 1 verdict/sufficiency distribution per dataset (V7-B)
v = D[D.system == "V7-B"].copy()
v["cat"] = np.where(v.verdict == "NO_DIVERGENCE_OBSERVED", "NO_DIV " + v.sufficiency,
           np.where(v.verdict == "", "NOT_DRIVEN", v.verdict))
v["cat"] = v.cat.replace({"DIVERGENT_OBSERVABLE": "DIVERGENT", "NO_DIV S1": "NO_DIV S1", "NO_DIV S2": "NO_DIV S2"})
cats = ["DIVERGENT", "NO_DIV S1", "NO_DIV S2", "INSUFFICIENT", "NOT_DRIVEN"]
cc = ["#0072B2", "#9ecae1", "#56B4E9", "#D55E00", "#999999"]
ct = pd.crosstab(v.dataset, v.cat).reindex(columns=cats, fill_value=0)
fig, ax = plt.subplots(figsize=(6.5, 3))
left = np.zeros(len(ct))
for c, col in zip(cats, cc):
    ax.barh(ct.index, ct[c], left=left, color=col, label=c)
    for i, (l, n) in enumerate(zip(left, ct[c])):
        if n >= 4: ax.text(l + n / 2, i, int(n), ha="center", va="center", fontsize=7, color="white" if col in ("#0072B2", "#D55E00") else "black")
    left += ct[c].to_numpy()
ax.set_xlabel("pairs (V7-B, run 1)"); ax.legend(ncol=3, fontsize=7, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False)
fig.text(0.01, -0.03, NOTE, fontsize=6.5); save(fig, "fig_verdict_sufficiency_by_dataset")

# 2 INSUFFICIENT primary reasons
ds = {r["pair"]: ("quixbugs_buggy_fixed" if r["arm"] == "quixbugs" else "quixbugs_sp_negatives" if r["arm"] == "quixbugs_neg" else "bugsinpy_units" if r["arm"] == "bugsinpy_units" else "synthetic") for r in K1}
cnt = collections.Counter((ds[r["pair"]], r["primary"]) for r in K1 if r["verdict"] == "INSUFFICIENT")
rt = pd.Series(cnt).unstack(fill_value=0)
rt = rt.loc[:, rt.sum().sort_values(ascending=False).index]
fig, ax = plt.subplots(figsize=(6.5, 3))
rt.T.plot.barh(stacked=True, ax=ax, colormap="tab10", width=0.7)
ax.invert_yaxis(); ax.set_xlabel("INSUFFICIENT pairs (primary reason code)"); ax.legend(fontsize=7, frameon=False)
fig.text(0.01, -0.03, NOTE + "; SP-2 renames and generator functions are known unimplemented-harness gaps", fontsize=6.5)
save(fig, "fig_insufficient_reasons")

# 3 risk-coverage (descriptive)
fig, ax = plt.subplots(figsize=(4.6, 3.4))
for s in SYS:
    r = RC[RC.system == s]
    if s == "V7-B":
        ax.errorbar(r.coverage, r.risk, yerr=[r.risk - r.risk_lo, r.risk_hi - r.risk], fmt="-o", color=COL[s], capsize=2, label=s + " (none, S1, S2, S3)")
        for _, x in r.iterrows(): ax.annotate(x.min_sufficiency_for_NDO, (x.coverage, x.risk), fontsize=6, xytext=(3, 4), textcoords="offset points")
    else:
        x = r[r.min_sufficiency_for_NDO == "none"].iloc[0]
        ax.errorbar(x.coverage, x.risk, yerr=[[x.risk - x.risk_lo], [x.risk_hi - x.risk]], fmt="s", color=COL[s], capsize=2, label=s + " (no sufficiency levels)")
ax.set_xlabel("coverage (decided / eligible)"); ax.set_ylabel("error risk (errors / decided)"); ax.legend(fontsize=6.5, frameon=False)
fig.text(0.01, -0.06, "Project-cluster bootstrap 95% CI. Labels are generator labels; K=101 but one 113-pair QuixBugs cluster.\n" + NOTE, fontsize=6); save(fig, "fig_risk_coverage")

# 4 detection: QuixBugs and all DIV pairs, cluster CIs
import sys; sys.path.insert(0, "scripts"); import analyze_results as ar
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3), sharey=True)
qb = D[(D.dataset == "quixbugs_buggy_fixed") & (D.truth == "DIV")]
for i, s in enumerate(SYS):
    q = qb[qb.system == s]; k = int((q.verdict == "DIVERGENT_OBSERVABLE").sum()); n = len(q)
    axs[0].bar(i, k / n, color=COL[s]); axs[0].text(i, k / n + 0.02, f"{k}/{n}", ha="center", fontsize=7)
    m = SM[(SM.system == s) & (SM.outcome == "detection")].iloc[0]
    axs[1].errorbar(i, m.est, yerr=[[m.est - m.lo], [m.hi - m.est]], fmt="o", color=COL[s], capsize=3)
    axs[1].text(i + 0.12, m.est, f"{m.est:.2f}", fontsize=7, va="center")
for a in axs: a.set_xticks(range(len(SYS))); a.set_xticklabels(SYS, rotation=30)
axs[0].set_ylim(0, 1.1); axs[0].set_ylabel("detection rate")
axs[0].set_title("QuixBugs buggy/fixed (witness by declared tests)\nK=1 project: cluster CI undefined, none shown", fontsize=7)
axs[1].set_title("All DIV-labelled pairs (QuixBugs + synthetic CHANGED)\n95% project-cluster bootstrap CI, K=78", fontsize=7)
fig.text(0.01, -0.04, NOTE + "; V7-B abstains instead of detecting on 2 QuixBugs pairs", fontsize=6.5); save(fig, "fig_detection_quixbugs_vs_baselines")

# 5 runtime
fig, ax = plt.subplots(figsize=(5, 3))
data = [pd.to_numeric(D[(D.system == s) & (D.cpu_s != "")].cpu_s).clip(lower=1e-3) for s in SYS]
bp = ax.boxplot(data, tick_labels=SYS, patch_artist=True, showfliers=True, flierprops=dict(markersize=2))
for p, s in zip(bp["boxes"], SYS): p.set_facecolor(COL[s])
ax.set_yscale("log"); ax.set_ylabel("CPU seconds per pair (log; B4 ~0 clipped at 1e-3)")
fig.text(0.01, -0.06, "V7-B CPU = child processes only (lower bound; parent overhead unmeasured). Memory not recorded.\n" + NOTE, fontsize=6); save(fig, "fig_runtime")
print(sorted(p.name for p in OUT.iterdir()))
