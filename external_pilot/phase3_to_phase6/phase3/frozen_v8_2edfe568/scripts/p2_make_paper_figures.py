#!/usr/bin/env python3
"""Phase 2 manuscript figures and tables, generated ONLY from results/v7b_phase2_summary/ (read-only).

Run:  .venv/bin/python scripts/p2_make_paper_figures.py
Writes: results/v7b_phase2_summary/figures/*.{pdf,png}  (NEW files only)
        paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/tables/P_*.tex and tables/SOURCES.json
Needs matplotlib; no Graphviz/LaTeX. Exploratory, non-pristine data: nothing here supports generalisation.
"""
import csv, json, pathlib, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = pathlib.Path(__file__).resolve().parent.parent
S = ROOT / "results/v7b_phase2_summary"
FIG = S / "figures"
TAB = ROOT / "paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/tables"
FIG.mkdir(exist_ok=True)
E1 = S / "p2_e1_20261118_074906"; E3 = S / "p2_e3_20261118_092700"; E4 = S / "p2_e4_20261118_154218"
E5 = S / "p2_e5_20261118_170505"; E6 = S / "p2_e6_20261118_171723"; E6B = S / "p2_e6b_20261118_174414"
E7 = S / "p2_e7_20261118_190612"; CON = S / "p2_consolidated_20261118_190644/consolidated.json"
rel = lambda p: str(p.relative_to(ROOT))

# colour-blind-safe, grayscale-distinguishable (different lightness)
C = {"div": "#0072B2", "ins": "#999999", "s2": "#009E73", "s1": "#B8E0CF", "b1": "#D55E00", "v7": "#0072B2", "b3": "#E69F00"}
plt.rcParams.update({"font.size": 7.5, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150,
                     "pdf.fonttype": 42, "axes.titlesize": 8})

def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight"); fig.savefig(FIG / f"{name}.png", bbox_inches="tight", dpi=200)
    plt.close(fig)

rows = lambda p: list(csv.DictReader(open(p)))
metrics = {(r["system"], r["outcome"]): r for r in rows(E3 / "statistics/system_metrics.csv")}
paired = {(r["test"], r["outcome"]): r for r in rows(E3 / "statistics/paired_comparisons.csv")}
riskc = rows(E3 / "statistics/risk_coverage.csv")
pairs = rows(E3 / "processed/dev_pairs_per_system.csv")
con = json.load(open(CON))
e1 = json.load(open(E1 / "e1_analysis.json"))
cc = collections.Counter((r["system"], r["truth"], r["verdict"]) for r in pairs)
byp = collections.defaultdict(dict)
for r in pairs: byp[r["pair_id"]][r["system"]] = r
f = lambda x: float(x)

# ---------------------------------------------------------------- diagrams (no external tool)
def box(ax, x, y, w, h, text, fc="#F2F2F2", ec="#333", ls="-", fs=7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=fc, ec=ec, lw=0.9, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)
def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=0.9, color="#333"))

def fig_architecture():
    fig, ax = plt.subplots(figsize=(3.5, 4.3)); ax.set_xlim(0, 10); ax.set_ylim(-1.5, 13); ax.axis("off")
    box(ax, 0.3, 11.3, 9.4, 1.3, "Inputs: base.py, variant.py, entry,\nuser-supplied JSON inputs, config (harness H)", "#FFFFFF")
    box(ax, 0.3, 9.3, 9.4, 1.4, "config.py: strict validation (S3 refused)\nrunner.py: repeats, replay, alternate control,\nchanged-region activation", "#E8F0F8")
    box(ax, 0.3, 7.1, 4.5, 1.7, "isolation.py\nchild per run, macOS\nsandbox-exec only", "#FDEBD3")
    box(ax, 5.2, 7.1, 4.5, 1.7, "harness.py (child)\nobservation, line/branch\ncapture, HMAC frame", "#FDEBD3")
    box(ax, 0.3, 5.1, 4.5, 1.5, "compare.py\nboundary comparator\n(canonical observations)", "#E8F0F8")
    box(ax, 5.2, 5.1, 4.5, 1.5, "decide.py (pure)\nverdict + sufficiency\nfirst match wins", "#E8F0F8")
    box(ax, 0.3, 3.0, 9.4, 1.6, "records.py: content-addressed records,\nhash-chained evidence.jsonl, verdict.json", "#E5F2EA")
    box(ax, 0.3, 1.0, 9.4, 1.5, "sbgv7 verify DIR: re-derives verdict from\nrecorded facts; executes nothing", "#E5F2EA")
    box(ax, 0.3, -1.4, 9.4, 1.6, "Not implemented: explorer, module E, S3,\nLinux isolation, supersession", "#FFFFFF", ls="--", ec="#888", fs=6.5)
    for (x, y1, y2) in [(5, 11.3, 10.7), (2.5, 9.3, 8.8), (7.5, 9.3, 8.8), (2.5, 7.1, 6.6), (7.5, 7.1, 6.6)]:
        arrow(ax, x, y1, x, y2)
    arrow(ax, 5, 5.1, 5, 4.6); arrow(ax, 5, 3.0, 5, 2.5)
    save(fig, "fig_p2_architecture")

def fig_verdict_flow():
    fig, ax = plt.subplots(figsize=(3.5, 3.9)); ax.set_xlim(0, 10); ax.set_ylim(0, 12); ax.axis("off")
    steps = [("1. identical sources?", "no verdict\n(ineligible:identical)", "#FFFFFF", 10.2),
             ("2. confirmed-difference\ninput?", "DIVERGENT_OBSERVABLE\n(replayable witness)", "#CFE3F3", 7.9),
             ("3. any blocking\ncondition?", "INSUFFICIENT(primary reason)\n18-code closed enum", "#E0E0E0", 5.6),
             ("4. S1 floors hold?\n(else INSUFFICIENT)", "NO_DIVERGENCE_OBSERVED(S1)\nor (S2) if S2 floors hold", "#D5EFE3", 3.3)]
    for q, a, fc, y in steps:
        box(ax, 0.2, y, 3.9, 1.5, q, "#FFFFFF", fs=6); box(ax, 5.0, y, 4.9, 1.5, a, fc, fs=5.2)
        arrow(ax, 4.1, y + 0.75, 5.0, y + 0.75); ax.text(4.55, y + 0.95, "yes", fontsize=5.5, ha="center")
    for y in (10.2, 7.9, 5.6): arrow(ax, 2.15, y, 2.15, y - 0.8); ax.text(2.35, y - 0.5, "no", fontsize=5.5)
    box(ax, 0.2, 1.0, 9.7, 1.4, "S3 is refused by configuration.\nNo equivalence verdict exists in the type.", "#FFFFFF", ls="--", ec="#888", fs=6.2)
    arrow(ax, 2.15, 3.3, 2.15, 2.4)
    save(fig, "fig_p2_verdict_flow")

# ---------------------------------------------------------------- data figures
def fig_verdict_dist():
    old, new = e1["verdict_distribution"]["old"], e1["verdict_distribution"]["new"]
    cats = [("DIVERGENT_OBSERVABLE", "DIVERGENT", C["div"]), ("NO_DIVERGENCE_OBSERVED/S2", "NDO S2", C["s2"]),
            ("NO_DIVERGENCE_OBSERVED/S1", "NDO S1", C["s1"]), ("INSUFFICIENT", "INSUFFICIENT", C["ins"])]
    fig, ax = plt.subplots(figsize=(3.5, 2.3)); left = [0, 0]
    for key, lab, col in cats:
        v = [old[key], new[key]]
        ax.barh(["old engine\n(post-fix rerun)", "current engine\n(E1 run 1)"], v, left=left, color=col, edgecolor="white", label=lab)
        for i, x in enumerate(v): ax.text(left[i] + x / 2, i, str(x), ha="center", va="center", fontsize=6.5, color="white" if lab != "NDO S1" else "black")
        left = [left[0] + v[0], left[1] + v[1]]
    ax.invert_yaxis(); ax.set_xlabel("pairs (312 driven pairs common to both runs)"); ax.legend(ncol=2, fontsize=6, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.32))
    save(fig, "fig_p2_verdict_dist")

def fig_metrics_vs_b1():
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.5), gridspec_kw={"width_ratios": [1.5, 1]})
    sysl = [("B1", C["b1"]), ("B3", C["b3"]), ("V7-B", C["v7"])]
    outs = [("false_assurance", "false assurance\n(of 106 divergent)"), ("detection", "detection\n(of 106 divergent)"), ("abstention", "abstention\n(of 258)")]
    for j, (o, ol) in enumerate(outs):
        for i, (s, col) in enumerate(sysl):
            m = metrics[(s, o)]; x = j + (i - 1) * 0.25
            a.errorbar(x, f(m["est"]), yerr=[[f(m["est"]) - f(m["lo"])], [f(m["hi"]) - f(m["est"])]], fmt="o", color=col, ms=4, capsize=2, lw=1, label=s if j == 0 else None)
    a.set_xticks(range(3)); a.set_xticklabels([o[1] for o in outs]); a.set_ylabel("rate (95% project-cluster CI)"); a.set_ylim(-0.02, 1.0)
    a.legend(frameon=False, fontsize=6.5, ncol=3, loc="upper left"); a.set_title("(a) E3 rates vs. B1 baselines; exploratory", loc="left")
    # (b) attribution of B1's false assurances
    fa = [p for p in byp.values() if p["B1"]["truth"] == "DIV" and p["B1"]["verdict"] == "NO_DIVERGENCE_OBSERVED"]
    cnt = collections.Counter(p["V7-B"]["verdict"] for p in fa)
    labs = [("NO_DIVERGENCE_OBSERVED", "still NDO", C["b1"]), ("INSUFFICIENT", "INSUFFICIENT", C["ins"]), ("DIVERGENT_OBSERVABLE", "DIVERGENT", C["div"])]
    bottom = 0
    for k, l, col in labs:
        b.bar(0, cnt.get(k, 0), bottom=bottom, color=col, edgecolor="white", width=0.5)
        if cnt.get(k, 0): b.text(0, bottom + cnt[k] / 2, f"{l}: {cnt[k]}", ha="center", va="center", fontsize=6.5, color="white")
        bottom += cnt.get(k, 0)
    b.set_xticks([0]); b.set_xticklabels([f"{len(fa)} B1 false assurances,\nV7-B verdict"]); b.set_xlim(-0.6, 0.6); b.set_ylabel("pairs")
    b.set_title("(b) reduction is abstention", loc="left")
    save(fig, "fig_p2_metrics_vs_b1"); return cnt, len(fa)

def fig_risk_coverage():
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    v = [r for r in riskc if r["system"] == "V7-B"]
    ax.plot([f(r["coverage"]) for r in v], [f(r["risk"]) for r in v], "-o", color=C["v7"], ms=4, label="V7-B (none, S1, S2, S3)")
    for r in v: ax.annotate(r["min_sufficiency_for_NDO"], (f(r["coverage"]), f(r["risk"])), textcoords="offset points", xytext=(3, 4), fontsize=6)
    for s, col, m in [("B1", C["b1"], "s"), ("B3", C["b3"], "^")]:
        r = [x for x in riskc if x["system"] == s and x["min_sufficiency_for_NDO"] == "none"][0]
        ax.plot(f(r["coverage"]), f(r["risk"]), m, color=col, label=f"{s} (decides all)")
    ax.set_xlabel("coverage (decided / 258)"); ax.set_ylabel("error risk (decided)"); ax.set_xlim(0, 1.05); ax.set_ylim(-0.02, 0.35)
    ax.text(0.02, 0.31, "S3 row: only witnessed divergences\n(S3 refused; no NDO at S3)", fontsize=6, va="top")
    ax.legend(frameon=False, fontsize=6.5, loc="center right")
    save(fig, "fig_p2_risk_coverage")

def fig_e5():
    labs, s1, s2 = ["0.6", "0.8 (default)", "0.9"], [], []
    for k in ("S2F06", "S2F08", "S2F09"):
        lv = con["E5"]["variants"][k]["levels"]; s1.append(lv.get("S1", 0)); s2.append(lv.get("S2", 0))
    fig, ax = plt.subplots(figsize=(3.5, 2.1))
    ax.bar(labs, s2, color=C["s2"], label="NDO S2"); ax.bar(labs, s1, bottom=s2, color=C["s1"], label="NDO S1")
    for i, (a, b_) in enumerate(zip(s2, s1)): ax.text(i, a / 2, str(a), ha="center", color="white", fontsize=7); ax.text(i, a + b_ / 2 + 0.01, str(b_) if b_ else "", ha="center", fontsize=7)
    ax.set_xlabel("S2 branch-coverage floor"); ax.set_ylabel("NO_DIVERGENCE_OBSERVED pairs (71)"); ax.legend(frameon=False, fontsize=6.5, loc="lower left")
    save(fig, "fig_p2_e5_floors"); return s1, s2

def fig_e6():
    fig, ax = plt.subplots(figsize=(3.5, 2.3))
    items = []
    for name, d in (("run 1", E6), ("run 2", E6B)):
        ro = json.load(open(d / "timing/timing_summary.json"))["relative_overhead"]
        for key, lab in (("V0_over_B1_wall_s", "V7-B / B1\nwall"), ("V0_over_B1_cpu_s", "V7-B / B1\nCPU"), ("V0_over_B1rep_wall_s", "V7-B / B1+rep\nwall")):
            items.append((lab, name, ro[key]["per_pair_ratio"]["median"], ro[key]["median_ratio_ci95"]))
    labs = ["V7-B / B1\nwall", "V7-B / B1\nCPU", "V7-B / B1+rep\nwall"]
    for k, name in enumerate(("run 1", "run 2")):
        for j, lab in enumerate(labs):
            it = [i for i in items if i[0] == lab and i[1] == name][0]; x = j + (k - 0.5) * 0.3
            ax.errorbar(x, it[2], yerr=[[it[2] - it[3][0]], [it[3][1] - it[2]]], fmt="o" if k == 0 else "s", color=C["v7"] if k == 0 else C["b1"], ms=4, capsize=2, label=name if j == 0 else None)
    ax.axhline(1, color="#888", lw=0.7, ls="--"); ax.set_xticks(range(3)); ax.set_xticklabels(labs); ax.set_ylabel("median per-pair ratio [95% CI]")
    ax.legend(frameon=False, fontsize=6.5); ax.set_title("40-pair subset, 5 reps, battery power, load flagged", fontsize=6.5, loc="left")
    save(fig, "fig_p2_e6_overhead")

# ---------------------------------------------------------------- tables
SRC = {}
def tex(name, caption, label, header, body, srcs, wide=False, align=None):
    ncol = len(header); align = align or "l" + "r" * (ncol - 1)
    env = "table*" if wide else "table"
    s = [f"\\begin{{{env}}}[t]\\centering\\scriptsize\\setlength{{\\tabcolsep}}{{3pt}}", f"\\caption{{{caption}}}\\label{{{label}}}",
         "\\resizebox{\\linewidth}{!}{%" if not wide else "", f"\\begin{{tabular}}{{{align}}}", "\\hline", " & ".join(header) + " \\\\", "\\hline"]
    s += [" & ".join(r) + " \\\\" for r in body] + ["\\hline", "\\end{tabular}" + ("}" if not wide else ""), f"\\end{{{env}}}"]
    (TAB / f"{name}.tex").write_text("\n".join(x for x in s if x != "") + "\n"); SRC[name] = [rel(p) for p in srcs]

pf = lambda x: "<1e-4" if x < 1e-4 else f"{x:.4f}"
def ci(m): return f"{f(m['est']):.3f} [{f(m['lo']):.3f}, {f(m['hi']):.3f}]"

def tables(attr):
    # datasets
    ds = collections.OrderedDict()
    for r in pairs:
        if r["system"] != "V7-B": continue
        ds.setdefault(r["dataset"], collections.Counter())[r["truth"]] += 1
    rule = {"quixbugs_buggy_fixed": "declared tests fail on buggy, pass on fixed", "quixbugs_sp_negatives": "generator: semantics-preserving variant",
            "synthetic_changed": "generator label: changed", "synthetic_equivalent": "generator label: equivalent (looser equality)", "bugsinpy_units": "real fixes; no defensible label"}
    body = [[n.replace("_", "\\_"), str(sum(c.values())), str(c["DIV"]), str(c["NO_OBS_DIFF"]), str(c["SUSPECT_LABEL"]), str(c["UNLABELLED"]), rule[n]] for n, c in ds.items()]
    tot = collections.Counter(); [tot.update(c) for c in ds.values()]
    body.append(["total", str(sum(tot.values())), str(tot["DIV"]), str(tot["NO_OBS_DIFF"]), str(tot["SUSPECT_LABEL"]), str(tot["UNLABELLED"]), ""])
    tex("P_datasets", "The 321 development pairs by arm and truth class (V7-B rows; all data non-pristine). Primary denominators: divergent (div.) and no-observed-difference (no-diff.) labels (258 pairs); suspect and unlabelled pairs are excluded. Source: \\path{results/v7b_phase2_summary/p2_e3_20261118_092700/processed/dev_pairs_per_system.csv}.",
        "tab:datasets", ["Arm", "Pairs", "Div.", "No-diff.", "Suspect", "Unlab.", "Truth rule"], body, [E3 / "processed/dev_pairs_per_system.csv"], align="lrrrrrl")
    # verdicts by arm
    va = collections.OrderedDict()
    for r in pairs:
        if r["system"] != "V7-B": continue
        k = r["verdict"] + (("/" + r["sufficiency"]) if r["verdict"] == "NO_DIVERGENCE_OBSERVED" else "")
        va.setdefault(r["dataset"], collections.Counter())[k] += 1
    cols = ["DIVERGENT_OBSERVABLE", "INSUFFICIENT", "NO_DIVERGENCE_OBSERVED/S1", "NO_DIVERGENCE_OBSERVED/S2", "NOT_DRIVEN"]
    body = [[n.replace("_", "\\_")] + [str(c[k]) for k in cols] for n, c in va.items()]
    t = collections.Counter(); [t.update(c) for c in va.values()]; body.append(["total"] + [str(t[k]) for k in cols])
    tex("P_byarm", "V7-B verdict per arm, E3 run (321 pairs). Source: \\path{results/v7b_phase2_summary/p2_e3_20261118_092700/processed/dev_pairs_per_system.csv}.",
        "tab:byarm", ["Arm", "DIV", "INSUF.", "NDO S1", "NDO S2", "Not driven"], body, [E3 / "processed/dev_pairs_per_system.csv"])
    # E3 metrics
    body = []
    for s in ("B1", "B1+rep", "B3", "B4", "V7-B"):
        fa, de, ab, al = (metrics[(s, o)] for o in ("false_assurance", "detection", "abstention", "false_alarm"))
        nf = cc[(s, "DIV", "NO_DIVERGENCE_OBSERVED")]; nd = cc[(s, "DIV", "DIVERGENT_OBSERVABLE")]; na = cc[(s, "DIV", "INSUFFICIENT")] + cc[(s, "NO_OBS_DIFF", "INSUFFICIENT")]
        nal = cc[(s, "NO_OBS_DIFF", "DIVERGENT_OBSERVABLE")]
        body.append([s, f"{nf}/106 = {ci(fa)}", f"{nd}/106 = {ci(de)}", f"{na}/258 = {ci(ab)}" if na else "0/258", f"{nal}/152 = {f(al['est']):.3f}"])
    tex("P_metrics", "E3 system metrics on the 258 labelled pairs (106 divergent, 152 no-difference); 95\\% project-cluster bootstrap CI ($B=10000$, seed 42). Exploratory; non-pristine data. Abstention for V7-B counts INSUFFICIENT on both truth classes (122 = 18 + 104). Source: \\path{results/v7b_phase2_summary/p2_e3_20261118_092700/statistics/system_metrics.csv}.",
        "tab:metrics", ["System", "False assurance", "Detection", "Abstention", "False alarm"], body, [E3 / "statistics/system_metrics.csv", E3 / "statistics/class_counts.csv"], align="lllll")
    # paired
    body = []
    for t_, o in (("V7-B", "false_assurance"), ("V7-B", "detection"), ("V7-B", "abstention"), ("V7-B", "false_alarm"), ("B3", "false_assurance"), ("B3", "detection"), ("B1+rep", "detection")):
        r = paired[(t_, o)]
        body.append([f"{t_} vs B1", o.replace("_", " "), f"{f(r['diff']):+.3f} [{f(r['diff_lo']):+.3f}, {f(r['diff_hi']):+.3f}]", f"{r['b_test_only']}/{r['c_ref_only']}", pf(f(r['p_signflip'])), pf(f(r['p_mcnemar_exact_pairlevel'])), pf(f(r['p_holm'])), "no" if r["meets_plus10pp"] == "False" else "yes"])
    tex("P_paired", "Paired comparisons against B1 (difference in rate, test minus reference, with 95\\% project-cluster CI; test-only/ref-only discordant pairs; project-level sign-flip, exact McNemar, Holm over 4 comparisons $\\times$ 2 primary outcomes). Descriptive: pairs cluster by project, data are non-pristine. The +10pp rule is not met in any row. Source: \\path{results/v7b_phase2_summary/p2_e3_20261118_092700/statistics/paired_comparisons.csv}.",
        "tab:paired", ["Comparison", "Outcome", "Diff. [CI]", "b/c", "Sign-flip p", "McNemar p", "Holm p", "+10pp"], body, [E3 / "statistics/paired_comparisons.csv"], wide=False, align="llrrrrrr")
    # risk coverage
    body = []
    for r in riskc:
        if r["system"] in ("V7-B", "B1") and (r["system"] == "V7-B" or r["min_sufficiency_for_NDO"] == "none"):
            body.append([r["system"], r["min_sufficiency_for_NDO"], f"{f(r['coverage']):.3f}", f"{f(r['risk']):.3f} [{f(r['risk_lo']):.3f}, {f(r['risk_hi']):.3f}]", f"{r['decided']}/{r['eligible']}"])
    tex("P_riskcov", "Risk--coverage (decided verdicts only; risk = errors/decided against generator or test-oracle labels). The V7-B S3 row contains only witnessed divergences because S3 is refused by configuration and no NO\\_DIVERGENCE\\_OBSERVED is issued at that level. Source: \\path{results/v7b_phase2_summary/p2_e3_20261118_092700/statistics/risk_coverage.csv}.",
        "tab:riskcov", ["System", "Min. level for NDO", "Coverage", "Risk [CI]", "Decided"], body, [E3 / "statistics/risk_coverage.csv"], align="llrrr")
    # gate counterfactual
    g = con["gate_counterfactual_E3"]; body = []
    for k, l in (("actual", "actual V7-B"), ("G_A_all_insufficient_to_NDO", "all INSUFFICIENT relabelled NDO"), ("G_B_gate_reasons_only_to_NDO", "only gate-attributable reasons relabelled")):
        body.append([l, str(g[k]["false_assurance"]) + "/" + str(g[k]["n_div"]), f"{g[k]['false_assurance_rate']:.3f}", str(g[k]["abstention"])])
    tex("P_gate", "Derived (not executed) gate counterfactual on the E3 verdicts. Source: \\path{results/v7b_phase2_summary/p2_consolidated_20261118_190644/consolidated.json}, key \\texttt{gate\\_counterfactual\\_E3}.",
        "tab:gate", ["Variant", "False assurance", "Rate", "Abstained"], body, [CON], align="lrrr")
    # reasons (E3 run, 312 driven pairs + not driven)
    rr = [json.loads(l) for l in open(E3 / "processed/k1_spike_per_pair.jsonl")]
    r1 = [r for r in rr if r["tag"] == "run1" and r["verdict"] == "INSUFFICIENT"]
    cnt = collections.Counter(r["primary"] for r in r1)
    desc = {"unmodelled_change": "changed lines without executable code (rule A-U1)", "unsupported_signature": "renamed entry or unsupported signature", "changed_region_not_activated": "no input reached the changed lines",
            "unobservable_outcome": "lossy or degenerate observation", "resource_limit": "limit hit on a side or both", "nondeterministic": "a version is not self-consistent", "import_error": "import or entry failure"}
    body = [[k.replace("_", "\\_"), str(v), desc[k]] for k, v in cnt.most_common()]
    body.append(["total", str(sum(cnt.values())), ""])
    tex("P_reasons", "Primary reason of the INSUFFICIENT verdicts in the E3 run (312 driven pairs; 9 pairs are not driven). Source: \\path{results/v7b_phase2_summary/p2_e3_20261118_092700/processed/k1_spike_per_pair.jsonl}.",
        "tab:reasons", ["Primary reason", "Pairs", "Meaning"], body, [E3 / "processed/k1_spike_per_pair.jsonl"], align="lrl")
    # ablations
    cfg = {"V0": "default", "V1": "$r_{det}=1$", "V2": "$r_{replay}=1$", "V3": "$k_{alt}=0$", "V4": "V1+V2+V3", "V5": "FOLD\\_FD1=False"}
    body = []
    for k in ("V0", "V1", "V2", "V3", "V4", "V5"):
        v = con["E4"]["variants"][k]; fl = con["E4"]["flips"].get(k, {})
        body.append([k, cfg[k], str(v["verdicts"]["DIVERGENT_OBSERVABLE"]), str(v["verdicts"]["INSUFFICIENT"]), str(v["verdicts"]["NO_DIVERGENCE_OBSERVED"]), str(fl.get("flips_verdict", "--")), f"{v['cpu_s_sum']:.1f}"])
    tex("P_e4", "E4 ablations on the 321 pairs (verdict counts; flips = pairs whose verdict value or level differs from V0). CPU is the summed per-pair CPU of the run (concurrency 4, load-sensitive). Only a reason code changes (one pair, V1 and V4). Source: \\path{results/v7b_phase2_summary/p2_consolidated_20261118_190644/consolidated.json}, key \\texttt{E4}.",
        "tab:e4", ["Variant", "Change", "DIV", "INSUF.", "NDO", "Flips vs V0", "CPU s (sum)"], body, [CON], align="llrrrrr")
    # E6
    body = []
    for name, d in (("run 1", E6), ("run 2", E6B)):
        t = json.load(open(d / "timing/timing_summary.json")); ro = t["relative_overhead"]
        loadsv = t["hardware"]["loadavg"][0]
        body.append([name, f"{t['systems']['V0']['wall_s']['per_pair_median']['median']:.3f}", f"{t['systems']['B1']['wall_s']['per_pair_median']['median']:.3f}",
                     f"{ro['V0_over_B1_wall_s']['per_pair_ratio']['median']:.3f} [{ro['V0_over_B1_wall_s']['median_ratio_ci95'][0]:.3f}, {ro['V0_over_B1_wall_s']['median_ratio_ci95'][1]:.3f}]",
                     f"{ro['V0_over_B1_cpu_s']['per_pair_ratio']['median']:.3f} [{ro['V0_over_B1_cpu_s']['median_ratio_ci95'][0]:.3f}, {ro['V0_over_B1_cpu_s']['median_ratio_ci95'][1]:.3f}]",
                     f"{ro['V0_over_B1rep_wall_s']['per_pair_ratio']['median']:.3f} [{ro['V0_over_B1rep_wall_s']['median_ratio_ci95'][0]:.3f}, {ro['V0_over_B1rep_wall_s']['median_ratio_ci95'][1]:.3f}]", f"{loadsv:.2f}"])
    tex("P_e6", "E6 runtime, 40-pair subset, 5 repetitions (V0 = default V7-B). Median per-pair wall time in seconds and median per-pair ratios with 95\\% CI. Both runs were flagged by the pre-registered load rule; machine on battery power. Last column: 1-minute load average at start. Source: \\path{results/v7b_phase2_summary/p2_e6_20261118_171723/timing/timing_summary.json} and \\path{p2_e6b_20261118_174414/timing/timing_summary.json}.",
        "tab:e6", ["Run", "V0 wall", "B1 wall", "V0/B1 wall", "V0/B1 CPU", "V0/B1+rep wall", "Load"], body, [E6 / "timing/timing_summary.json", E6B / "timing/timing_summary.json"], align="lrrrrrr")
    # E7 corruption matrix
    cr = json.load(open(E7 / "corruption_results.json")); by = collections.OrderedDict()
    for r in cr: by.setdefault(r["case"], []).append(r)
    body = []
    for case, rs in by.items():
        r0 = rs[0]; obs = sorted({x["observed"] for x in rs})
        det = "detected" if r0["expected"] != 0 else "NOT detected (documented limit)"
        body.append([case.replace("_", "\\_"), str(len(rs)), ",".join(map(str, obs)), "yes" if all(x["as_expected"] for x in rs) else "NO", det])
    tex("P_e7", "E7 corruption suite: 14 corruption cases applied to copies of three evidence directories each (one per verdict class), 42 runs. Exit codes of \\texttt{verify}: 0 verified, 1 mismatch, 2 unreadable or missing, 4 evidence omitted by size cap. ``As expected'' means as pre-registered; cases ending with exit 0 are documented limitations that the check does not detect. Source: \\path{results/v7b_phase2_summary/p2_e7_20261118_190612/corruption_results.json}.",
        "tab:e7", ["Case", "Runs", "Exit code", "As expected", "Outcome"], body, [E7 / "corruption_results.json"], align="lrrrl")
    json.dump(SRC, open(TAB / "SOURCES.json", "w"), indent=1)

if __name__ == "__main__":
    fig_architecture(); fig_verdict_flow(); fig_verdict_dist(); attr = fig_metrics_vs_b1(); fig_risk_coverage(); e5 = fig_e5(); fig_e6()
    tables(attr)
    assert attr[1] == 24 and attr[0]["INSUFFICIENT"] == 11 and attr[0]["NO_DIVERGENCE_OBSERVED"] == 13 and not attr[0].get("DIVERGENT_OBSERVABLE"), attr
    assert e5 == ([0, 16, 28], [71, 55, 43]), e5
    print("figures ->", rel(FIG), sorted(p.name for p in FIG.glob("fig_p2_*.pdf")))
    print("attribution of B1 false assurance:", dict(attr[0]), "E5 (S1,S2):", e5)
