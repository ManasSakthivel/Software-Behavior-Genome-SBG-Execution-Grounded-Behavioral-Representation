"""Publication figures + LaTeX ablation table from audit/stats_summary.json (written by stats_recompute.py).
All data: DEVELOPMENT DATA (datasets/v8/dev_records.jsonl, linux branch, unfixed profile), seed 0 unless stated. No titles inside plots.
usage: <python> paper/IEEE_ACCESS_V8_FINAL/scripts/make_stat_figures.py
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); BASE = os.path.dirname(HERE)
S = json.load(open(os.path.join(BASE, "audit/stats_summary.json")))
FIG = os.path.join(BASE, "figures"); TAB = os.path.join(BASE, "tables"); os.makedirs(FIG, exist_ok=True); os.makedirs(TAB, exist_ok=True)

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"], "mathtext.fontset": "stix",
                     "font.size": 8, "axes.labelsize": 8, "legend.fontsize": 6.5, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "axes.linewidth": 0.6, "lines.linewidth": 1.0, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.02})
W = 3.5
# Okabe-Ito (colour-blind safe)
OI = {"black": "#000000", "orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442", "blue": "#0072B2", "verm": "#D55E00", "purple": "#CC79A7", "grey": "#999999"}
MOD = [("b7_cov_calibration", "Coverage-only calib. (B7)", OI["orange"], (0, (4, 1.5))),
       ("abl_mult_only", "Multiplicity-only", OI["green"], (0, (1, 1))),
       ("b9_cec_no_ers", "CEC w/o ERS (B9)", OI["sky"], (0, (6, 2, 1, 2))),
       ("b8_full_cec", "CEC + ERS (B8)", OI["blue"], "-")]
RUL = [("b1_plain_dt", "Plain DT (B1)", "o"), ("b3_v7b_gate", "V7-B gate (B3)", "s"), ("b4_cov_gate", "Coverage gate (B4)", "^"), ("b5_cov_gated_b1", "Cov.-gated B1 (B5)", "v")]
R0 = S["seed0_recomputed"]


def rc_panel(ax, pol, legend):
    r = R0[pol]; c7 = r["v7b_gate_coverage"]
    for n, lab, col, ls in MOD:
        cur = np.array(r["models"][n]["risk_coverage_curve"])
        ax.plot(np.r_[0, cur[:, 0]], np.r_[cur[0, 1], cur[:, 1]], color=col, ls=ls, label=lab, drawstyle="steps-post")
    for n, lab, mk in RUL:
        x = r["rules"][n]; lo, hi = x["risk_ci95_cluster"]
        ax.errorbar(x["coverage"], x["risk"], yerr=[[x["risk"] - lo], [hi - x["risk"]]], fmt=mk, ms=3.5, mfc="white", mec=OI["black"], ecolor=OI["grey"], elinewidth=0.6, capsize=1.5, label=lab)
    b6 = r["b6_random_abstention"]["risk_expectation"]
    ax.axhline(b6, color=OI["grey"], lw=0.6, ls=":", label="Random abstention (B6)")
    ax.axvline(c7, color=OI["verm"], lw=0.6, ls="--"); ax.text(c7 + 0.008, 0.62, r"$c^*$", color=OI["verm"], fontsize=7)
    ax.set_xlim(0, 0.75); ax.set_ylim(0, 0.7); ax.set_ylabel(r"FA risk $\hat R$ = P(F=1 | NDO)")
    ax.grid(alpha=0.25, lw=0.4)


fig, axs = plt.subplots(2, 1, figsize=(W, 4.6), sharex=True)
rc_panel(axs[0], "soft_v8.0", True); rc_panel(axs[1], "strict_v8.0s", False)
axs[1].set_xlabel("Coverage (share of 258 labelled pairs issued NDO)")
for ax, t in zip(axs, ["(a) soft blockers (v8.0), 85 eligible", "(b) strict blockers (v8.0s = v8.1), 61 eligible"]):
    ax.text(0.99, 0.97, t, transform=ax.transAxes, fontsize=7, va="top", ha="right")
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.0), handlelength=2.2, columnspacing=0.8, fontsize=6)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_risk_coverage.pdf")); plt.close(fig)

# ---- calibration / reliability ----
fig, ax = plt.subplots(figsize=(W, 2.7))
ax.plot([0, 1], [0, 1], color=OI["grey"], lw=0.6, ls="--")
off = {"b7_cov_calibration": -0.008, "abl_mult_only": -0.003, "b9_cec_no_ers": 0.003, "b8_full_cec": 0.008}
for n, lab, col, ls in MOD:
    m = R0["soft_v8.0"]["models"][n]; b = m["reliability_q5"]
    x = np.array([q["mean_pred"] for q in b]) + off[n]; yv = np.array([q["obs_rate"] for q in b])
    lo = np.array([q["wilson95"][0] for q in b]); hi = np.array([q["wilson95"][1] for q in b])
    ax.errorbar(x, yv, yerr=[yv - lo, hi - yv], color=col, ls=ls, marker="o", ms=2.5, elinewidth=0.5, capsize=1.2,
                label=f"{lab}: slope {m['calib_slope']:.2f}")
ax.set_xlim(0, 0.8); ax.set_ylim(0, 1); ax.set_xlabel("Mean predicted risk (quantile bins, 5 x ~17 pairs)"); ax.set_ylabel("Observed miss rate")
ax.grid(alpha=0.25, lw=0.4); ax.legend(frameon=False, loc="upper left")
fig.savefig(os.path.join(FIG, "fig_calibration.pdf")); plt.close(fig)

# ---- forest: contrasts at c* (soft & strict), seed-0 CI + seeds 0-4 points ----
L = S["linux_multiseed_saved"]
rows = []  # (label, policy, point, lo, hi, seeds)
for pol, key in (("soft", "soft"), ("strict", "strict")):
    ps = L[key]["per_seed"]
    for c, lab in (("vs_b7", "B7 cov.-only calib."), ("vs_b3", "B3 V7-B gate"), ("vs_b6", "B6 random abstention")):
        rows.append((lab, pol, ps[0][c]["diff_b_minus_a"], *ps[0][c]["ci95_pct"], [p[c]["diff_b_minus_a"] for p in ps], ps[0]["holm"][["vs_b7", "vs_b3", "vs_b6"].index(c)]))
    rows.append(("B9 CEC w/o ERS", pol, ps[0]["ers_matched_b9_minus_b8_gate"]["diff_b_minus_a"], *ps[0]["ers_matched_b9_minus_b8_gate"]["ci95_pct"],
                 [p["ers_matched_b9_minus_b8_gate"]["diff_b_minus_a"] for p in ps], None))
fig, axs = plt.subplots(1, 2, figsize=(W, 2.3), gridspec_kw={"width_ratios": [1.35, 1]}, sharey=True)
yk = np.arange(len(rows) // 2)[::-1]
for j, pol in enumerate(("soft", "strict")):
    sub = [r for r in rows if r[1] == pol]
    ax = axs[0]; col = OI["blue"] if pol == "soft" else OI["verm"]; dy = 0.15 if pol == "soft" else -0.15
    for k, r in zip(yk, sub):
        ax.plot([100 * r[3], 100 * r[4]], [k + dy] * 2, color=col, lw=1.0)
        ax.plot(100 * r[2], k + dy, "o", color=col, ms=3.5, mfc=col if pol == "soft" else "white")
        ax.plot(100 * np.array(r[5]), [k + dy] * len(r[5]), "|", color=col, ms=4, alpha=0.6)
    ax.plot([], [], "o-", color=col, ms=3, mfc=col if pol == "soft" else "white", label="soft (v8.0)" if pol == "soft" else "strict (v8.0s)")
ax = axs[0]; ax.axvline(0, color=OI["black"], lw=0.5); ax.axvline(5, color=OI["grey"], lw=0.5, ls=":")
ax.set_yticks(yk); ax.set_yticklabels([r[0] for r in rows if r[1] == "soft"]); ax.set_xlabel(r"$\Delta\hat R$ at $c^*$ (pp)")
ax.grid(axis="x", alpha=0.25, lw=0.4)
fig.legend(*axs[0].get_legend_handles_labels(), frameon=False, loc="lower center", bbox_to_anchor=(0.55, 0.98), ncol=2, fontsize=6.5)
# right: log-loss contrasts (seed 0 recomputed CIs)
ax = axs[1]
lab2 = [("logloss_b7_cov_calibration_minus_b8_full_cec", 0), ("logloss_b7_cov_calibration_minus_b8_full_cec", 1), ("logloss_b7_cov_calibration_minus_b8_full_cec", 2),
        ("logloss_b9_cec_no_ers_minus_b8_full_cec", 3)]
for pol, dy, col in (("soft_v8.0", 0.15, OI["blue"]), ("strict_v8.0s", -0.15, OI["verm"])):
    C = R0[pol]["contrasts_own_bootstrap"]
    for key, k in (("logloss_b7_cov_calibration_minus_b8_full_cec", yk[0]), ("logloss_b9_cec_no_ers_minus_b8_full_cec", yk[3])):
        d = C[key]; ax.plot(d["ci95"], [k + dy] * 2, color=col, lw=1.0); ax.plot(d["diff"], k + dy, "o", color=col, ms=3.5, mfc=col if pol.startswith("soft") else "white")
ax.axvline(0, color=OI["black"], lw=0.5); ax.set_xlabel(r"$\Delta$ log loss"); ax.grid(axis="x", alpha=0.25, lw=0.4)
fig.subplots_adjust(wspace=0.12)
fig.savefig(os.path.join(FIG, "fig_ablation_forest.pdf")); plt.close(fig)

# ---- power: MDE vs number of issued NDO ----
P = R0["soft_v8.0"]["power"]; deff = P["deff"]; p0 = P["risk"]
ns = np.arange(40, 1601, 10); za, zb = 1.959964, 0.841621
fig, ax = plt.subplots(figsize=(W, 2.2))
for q, col, ls in ((0.10, OI["green"], "-"), (0.15, OI["blue"], "--"), (0.25, OI["orange"], ":")):
    mde = [next((d for d in np.arange(0.005, 0.5, 0.001) if d * d < q and ((za * np.sqrt(q) + zb * np.sqrt(q - d * d)) / d) ** 2 * deff <= n), np.nan) for n in ns]
    ax.plot(ns, 100 * np.array(mde), color=col, ls=ls, label=f"paired, discordant share {q:.2f}")
ax.axvline(P["n_ndo"], color=OI["verm"], lw=0.6, ls="--"); ax.text(P["n_ndo"] + 15, 26, f"n = {P['n_ndo']}", color=OI["verm"], fontsize=7)
ax.axhline(5, color=OI["grey"], lw=0.6, ls=":"); ax.text(1000, 5.6, "5 pp (H2 margin)", fontsize=6.5, color=OI["grey"])
ax.set_xscale("log"); ax.set_xticks([50, 100, 200, 400, 800, 1600]); ax.set_xticklabels(["50", "100", "200", "400", "800", "1600"])
ax.set_xlabel(f"Issued NDO verdicts (design effect {deff:.2f})"); ax.set_ylabel("MDE (pp), 80% power"); ax.set_ylim(0, 30)
ax.grid(alpha=0.25, lw=0.4); ax.legend(frameon=False, fontsize=6.5)
fig.savefig(os.path.join(FIG, "fig_power_mde.pdf")); plt.close(fig)


# ---- LaTeX table ----
def f3(x): return "--" if x is None else f"{x:.3f}"
def ci(x): return "--" if x is None or x[0] is None else f"[{x[0]:.3f}, {x[1]:.3f}]"
NAMES = {"b1_plain_dt": "Plain differential testing (B1)", "b2_b1_repetition": "B1 + repetition (B2)", "b3_v7b_gate": "V7-B sufficiency gate (B3)",
         "b4_cov_gate": "Coverage-only gate (B4)", "b5_cov_gated_b1": "Coverage-gated B1 (B5)", "b7_cov_calibration": "Coverage-only calibration (B7)",
         "abl_cov_rep": "\\quad + repetition", "abl_cov_infl": "\\quad + influence proxy", "abl_cov_prov": "\\quad + provenance", "abl_cov_mult": "\\quad + multiplicity",
         "abl_mult_only": "Multiplicity only", "b9_cec_no_ers": "CEC without ERS (B9)", "b8_full_cec": "CEC with ERS (B8)"}
lines = []
for pol, head in (("soft_v8.0", "\\multicolumn{7}{l}{\\emph{Soft blockers (v8.0): 85 eligible labelled pairs}}"),
                  ("strict_v8.0s", "\\multicolumn{7}{l}{\\emph{Strict blockers (v8.0s $\\equiv$ v8.1): 61 eligible labelled pairs}}")):
    r = R0[pol]; lines.append("\\hline\n" + head + " \\\\")
    if pol == "soft_v8.0":
        lines[-1] = "\\hline\n\\multicolumn{7}{l}{\\emph{Rule baselines (all 258 labelled pairs; policy-independent)}} \\\\"
        for n in ("b1_plain_dt", "b2_b1_repetition", "b3_v7b_gate", "b4_cov_gate", "b5_cov_gated_b1"):
            x = r["rules"][n]
            lines.append(f"{NAMES[n]} & {x['coverage']:.3f} & {x['n_ndo']} & {f3(x['risk'])} {ci(x['risk_ci95_cluster'])} & -- & -- & -- \\\\")
        lines.append(f"Random abstention (B6)$^\\dagger$ & 0.236 & 61 & {r['b6_random_abstention']['risk_expectation']:.3f} & -- & -- & -- \\\\")
        lines.append("\\hline\n" + head + " \\\\")
    for n in ("b7_cov_calibration", "abl_cov_mult", "abl_mult_only", "b9_cec_no_ers", "b8_full_cec"):
        x = r["models"][n]
        lines.append(f"{NAMES[n]} & {x['matched_cstar']:.3f}$^\\ast$ & {x['matched_n_ndo']:.0f} & {f3(x['matched_risk'])} {ci(x['matched_risk_ci95_cluster'])} & "
                     f"{x['brier']:.3f} & {x['logloss']:.3f} & {x['calib_slope']:.2f} \\\\")
rt = [p["runtime_s"] for p in S["linux_multiseed_saved"]["soft"]["per_seed"]]
den = S["denominators"]
tex = r"""\begin{table*}[!t]
\caption{Development-set comparison of SBG V8 decision rules, calibrated models and ablations (seed 0, out-of-fold).}
\label{tab:ablation}
\centering
\footnotesize
\begin{tabular}{|l|c|c|c|c|c|c|}
\hline
Method & Coverage & \#NDO & FA risk [95\% CI] & Brier & Log loss & Cal.\ slope \\
""" + "\n".join(lines) + r"""
\hline
\end{tabular}
\\[2pt]
\parbox{\textwidth}{\scriptsize DEVELOPMENT DATA, EXPLORATORY, NOT INDEPENDENT VALIDATION. """ + \
    f"Split: development only ({den['n_records']} pairs, {den['n_labelled']} with construction labels, {den['n_unresolved_y_none']} unlabelled and excluded, " + \
    f"{den['n_projects_labelled']} labelled projects, 114 overall; {den['dominant_project']} = {100*den['dominant_share']:.1f}\\% of labelled pairs). " + \
    r"Coverage and FA risk are over the 258 labelled pairs; 95\% CIs are percentile project-cluster bootstrap intervals (10{,}000 resamples). " + \
    r"$^\ast$Model rows are rank-matched to the V7-B gate coverage $c^*=61/258$ (transductive diagnostic, not a deployable threshold); with nested-CV thresholds at $\alpha\in\{0.10,0.15\}$ the models issue 0 NDO (multiplicity-only: 1). " + \
    r"Under strict blockers every model issues exactly V7-B's 61 NDO pairs, so risks are identical by construction; their CIs use only the ${\approx}50\%$ of resamples in which $c^*$ is attainable and are therefore not reliable. Brier, log loss and slope are on eligible pairs only (out-of-fold base-rate Brier " + \
    f"{R0['soft_v8.0']['models']['b8_full_cec']['brier_oof_base_rate']:.3f} soft, {R0['strict_v8.0s']['models']['b8_full_cec']['brier_oof_base_rate']:.3f} strict). " + \
    r"$^\dagger$Expected risk of random abstention among B1-issuable pairs. Per-method runtime was not recorded; the whole 13-system evaluation took " + \
    f"{min(rt):.0f}--{max(rt):.0f}\\,s per seed (Linux run). Linux-branch code, before the mac-branch ERS profile fix." + "}\n\\end{table*}\n"
open(os.path.join(TAB, "tab_ablation.tex"), "w").write(tex)
print("wrote figures and table")
