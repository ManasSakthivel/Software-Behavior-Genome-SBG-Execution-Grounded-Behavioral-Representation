"""All conceptual diagrams and the evidence-landscape / cross-platform / security figures of the SBG V8 manuscript (supersedes make_diagrams.py).
Statistical plots are in make_stat_figures.py. Both use scripts/figstyle.py. Nothing here executes SBG or any program under test.
Data figures read only existing files: audit/five_dataset_summary.json, audit/security_outcomes.json, datasets/v8/dev_records.jsonl (counts).
Conceptual content follows the code at research/v8-linux-validation (see audit/ARCHITECTURE_AND_DEFINITIONS.md for file:line anchors).
usage: <python with matplotlib> paper/IEEE_ACCESS_V8_FINAL/scripts/make_figures.py [name ...]"""
import json, os, sys
from collections import Counter
import numpy as np
from figstyle import (plt, canvas, box, title, arrow, tag, save, INK, BLUE, BLUE_L, BLUE_XL, VERM, VERM_L, GREEN, GREEN_L, ORANGE, ORANGE_L,
                      GREY, GREY_L, GREY_XL, FS, COL, DBL)
from matplotlib.patches import Rectangle, Patch

HERE = os.path.dirname(os.path.abspath(__file__)); PAPER = os.path.dirname(HERE); REPO = os.path.dirname(os.path.dirname(PAPER))


# ---------------------------------------------------------------- Fig. 1  why an empty difference set is not equivalence
def motivation():
    fig, ax = canvas(COL, 3.3)
    title(ax, 0.02, 0.985, "Five ways a differential comparison can end", fs=7.8)
    ax.text(0.02, 0.945, "bar: input domain;  bracket: inputs reaching the changed code;\nshaded: divergence-revealing inputs;  ticks: executed inputs", fontsize=6.3, va="top", color=GREY, linespacing=1.1)
    X0, X1 = 0.30, 0.74
    cases = [  # label, D span or None, D on observed channel?, tick positions (fraction), verdict, F text, colour
        ("(a) change preserves\n      behaviour", None, True, [0.08, 0.2, 0.33, 0.47, 0.6, 0.72, 0.88], "NDO", "F = 0", GREEN),
        ("(b) changed code\n      never reached", (0.62, 0.78), True, [0.06, 0.14, 0.22, 0.31, 0.4], "NDO", "F = 1", VERM),
        ("(c) reached, but in one\n      observable way", (0.66, 0.77), True, [0.1, 0.25, 0.56, 0.58, 0.6], "NDO", "F = 1", VERM),
        ("(d) divergence only on\n      a channel outside O", (0.55, 0.8), False, [0.12, 0.3, 0.6, 0.7, 0.9], "NDO", "F = 0 w.r.t. O", GREY),
        ("(e) a witness is found", (0.55, 0.8), True, [0.15, 0.4, 0.63, 0.88], "DIV", "witness", BLUE)]
    top, dy = 0.835, 0.143
    for k, (lab, D, observed, ticks, v, ftxt, col) in enumerate(cases):
        y = top - k * dy
        ax.text(0.02, y, lab, fontsize=6.8, va="center", linespacing=1.05)
        ax.plot([X0, X1], [y, y], color=INK, lw=1.0, solid_capstyle="butt")
        if k > 0:  # changed region bracket
            cx0, cx1 = X0 + 0.52 * (X1 - X0), X0 + 0.84 * (X1 - X0)
            ax.plot([cx0, cx0, cx1, cx1], [y + 0.022, y + 0.034, y + 0.034, y + 0.022], color=GREY, lw=0.6)
        if D:
            dx0, dx1 = X0 + D[0] * (X1 - X0), X0 + D[1] * (X1 - X0)
            if observed:
                ax.add_patch(Rectangle((dx0, y - 0.013), dx1 - dx0, 0.026, fc=VERM_L, ec=VERM, lw=0.5, zorder=1))
            else:
                ax.plot([X0, X1], [y - 0.034, y - 0.034], color=GREY, lw=0.6, ls=(0, (2, 1.5)))
                ax.add_patch(Rectangle((dx0, y - 0.045), dx1 - dx0, 0.022, fc="white", ec=GREY, lw=0.5, hatch="////", zorder=1))
        for t in ticks:
            tx = X0 + t * (X1 - X0)
            hit = D and observed and D[0] <= t <= D[1]
            ax.plot([tx, tx], [y - 0.02, y + 0.02], color=VERM if hit else BLUE, lw=1.3 if hit else 1.0, zorder=3)
        tag(ax, 0.845, y + 0.012, v, col if v == "DIV" else (GREEN if col == GREEN else (VERM if col == VERM else GREY)))
        ax.text(0.845, y - 0.03, ftxt, fontsize=6.3, ha="center", va="center", color=col if col != GREY else INK)
    yb = top - 5 * dy + 0.045
    ax.plot([0.02, 0.98], [yb + 0.035, yb + 0.035], color=GREY_L, lw=0.6)
    ax.text(0.02, yb, "Cases (a)-(d) all yield an empty difference set. Only (b) and (c) are false\nassurances; (d) is outside the declared boundary O. The paper estimates\n"
            r"$\mathcal{R}=P(F=1\mid \mathrm{NDO})$ from the evidence that distinguishes them.", fontsize=6.6, va="top", linespacing=1.2)
    save(fig, "fig_motivation")


# ---------------------------------------------------------------- Fig. 2  architecture
def architecture():
    fig, ax = canvas(DBL, 3.7)
    Z = [(0.005, 0.205, "UNTRUSTED", "fresh sandboxed child per run", GREY_XL, GREY), (0.215, 0.235, "TRUSTED CONTROLLER", "parent process; holds anchor key K", BLUE_XL, BLUE),
         (0.46, 0.13, "EVIDENCE DIR", "sealed; one per pair", "white", INK), (0.60, 0.395, "VALIDATION, REPRESENTATION, DECISION", "separate interpreter; label-blind", BLUE_XL, BLUE)]
    for x, w, t, s, fc, ec in Z:
        box(ax, x, 0.115, w, 0.875, fc=fc, ec=ec, lw=0.9, r=0.015, ls="--" if t == "UNTRUSTED" else "-")
        title(ax, x + 0.007, 0.982, t, fs=7.3, color=ec if ec != INK else INK); ax.text(x + 0.007, 0.952, s, fontsize=6.4, va="top", color=GREY)
    # untrusted
    box(ax, 0.015, 0.14, 0.185, 0.77, fc="white", ec=GREY, lw=0.6, hatch="////", r=0.01)
    box(ax, 0.025, 0.715, 0.165, 0.175, "OS sandbox\nmacOS: sandbox-exec\nLinux: bwrap --unshare-net\n--ro-bind / /; rlimits;\nenv allow-list (no K)", fs=6.5)
    box(ax, 0.025, 0.52, 0.165, 0.15, "_tee_child.py stub\ntees stdout writes to\nfd 2 as nonce-framed\nrecords", fs=6.6)
    box(ax, 0.025, 0.345, 0.165, 0.13, "harness.py (V7-B)\ncanonicaliser; result\nframe on own fd", fs=6.6)
    box(ax, 0.025, 0.165, 0.165, 0.135, "Program under test\nP  or  P'", fc=GREY_L, bold=True, fs=7)
    arrow(ax, (0.1075, 0.52), (0.1075, 0.475)); arrow(ax, (0.1075, 0.345), (0.1075, 0.30))
    # controller
    box(ax, 0.225, 0.745, 0.215, 0.165, "Controller  collect.run_capture\nunmodified V7-B runner;\nfinalize() spy records per-input\nhits and branch directions", fs=6.6, ec=BLUE)
    box(ax, 0.225, 0.505, 0.215, 0.2, "Collector  procsep.Supervisor\nowns child pipes; parses tee;\njudge(): tee text vs harness\nstdout  →  match | mismatch |\nincomplete | no_frame", fs=6.6, ec=BLUE)
    box(ax, 0.225, 0.335, 0.215, 0.13, "Result-frame check\nHMAC-SHA256, fresh per-run\nkey over a closed pipe", fs=6.6, ec=BLUE)
    box(ax, 0.225, 0.155, 0.215, 0.14, "Shadow re-observer (optional)\nindependent minimal runner;\nreturn values only", fs=6.6, ls="--", ec=BLUE)
    for yy, t in ((0.83, "spawn"), (0.595, "fd 2"), (0.40, "frame")):
        if t == "spawn": arrow(ax, (0.225, yy), (0.19, yy), t, off=(0, 0.02), fs=6.3)
        else: arrow(ax, (0.19, yy), (0.225, yy), t, off=(0, 0.02), fs=6.3)
    arrow(ax, (0.225, 0.225), (0.19, 0.225), ls="--")
    # evidence
    box(ax, 0.468, 0.33, 0.114, 0.58, "", fc=GREY_XL, ec=INK, lw=0.6)
    files = [("evidence.jsonl", "SHA-256 chain"), ("verdict.json", "V7-B verdict"), ("v8_parts.json", "hits, branches"), ("v8_capture.json", "per-run records"),
             ("v8_anchor.json", "HMAC_K(digests)")]
    for i, (f, d) in enumerate(files):
        yy = 0.86 - i * 0.107
        ax.text(0.475, yy, f, fontsize=6.5, va="center", family="monospace"); ax.text(0.475, yy - 0.035, d, fontsize=6.2, va="center", color=GREY)
    arrow(ax, (0.44, 0.83), (0.468, 0.78), "write", off=(0.0, 0.03), fs=6.3); arrow(ax, (0.44, 0.6), (0.468, 0.6))
    box(ax, 0.468, 0.155, 0.114, 0.14, "Reviewer inputs\n(optional): sources,\npinned head; used by\ntrust.check, issues only", fs=6.4, ls="--")
    # validation and decision
    box(ax, 0.61, 0.69, 0.175, 0.22, "Validator\nvalidate_isolated:\nfresh interpreter, nonce +\nMAC-authenticated reply;\nvalidate_dir: schema,\nbinding, nonces, anchor", fs=6.4, ec=BLUE)
    box(ax, 0.80, 0.69, 0.185, 0.22, "Trust gate\ntrusted = False\n  → INSUFFICIENT for any\nverdict (incl. DIV);\nintegrity_ok feeds the\nrecord and the profile", fs=6.4, ec=VERM)
    box(ax, 0.61, 0.455, 0.175, 0.19, "Adapter → EvidenceRecord\nper-input outcome, hits,\nbranches, fingerprint,\nchannels, determinism,\nprovenance, flags", fs=6.4, ec=BLUE)
    box(ax, 0.80, 0.455, 0.185, 0.19, "Profile φ(E)\n15 change-conditioned\nfeatures; CEC risk g(φ)\n(+ ERS responses in B8)", fs=6.4, ec=BLUE)
    box(ax, 0.61, 0.155, 0.175, 0.255, "ERS audit (label-free)\nperturb a COPY: E → T_j(E)\nΔ$_j$ = R(T_j E) - R(E)\npass / fail / N/A per\nproperty; never edits the\nsealed evidence", fs=6.4, fc=GREEN_L, ec=GREEN)
    box(ax, 0.80, 0.155, 0.185, 0.255, "Verdict\n1  untrusted → INS\n2  witness → DIV\n3  eligible and\n    R ≤ τ  → NDO\n4  otherwise → INS", fs=6.6, ec=INK, lw=1.0)
    arrow(ax, (0.582, 0.8), (0.61, 0.8)); arrow(ax, (0.785, 0.8), (0.80, 0.8)); arrow(ax, (0.582, 0.55), (0.61, 0.55))
    arrow(ax, (0.785, 0.55), (0.80, 0.55)); arrow(ax, (0.8925, 0.69), (0.8925, 0.645)); arrow(ax, (0.8925, 0.455), (0.8925, 0.41))
    arrow(ax, (0.80, 0.50), (0.785, 0.36), ls="--", cs="arc3,rad=0.2")
    ax.text(0.005, 0.075, "Solid: on the verdict path.  Dashed: optional checks that report issues but do not change the verdict.  Hatched: OS sandbox boundary.", fontsize=6.6)
    ax.text(0.005, 0.035, "Key K never enters the child.  No code path invokes a container runtime; Linux confinement is bwrap/unshare network isolation and a read-only root.", fontsize=6.6)
    save(fig, "fig_architecture")


# ---------------------------------------------------------------- Fig. 3  evidence lifecycle
def lifecycle():
    fig, ax = canvas(DBL, 2.2)
    st = [("1 Execute", "V7-B engine runs\nP and P' per input\nin a fresh child", "sbgv7.isolation"),
          ("2 Capture", "parent-side hits\nand branches; tee;\nHMAC result frame", "collect, procsep"),
          ("3 Seal", "hash chain,\nsidecar, capture,\nanchor MAC", "evidence dir"),
          ("4 Validate", "validate_dir in a\nfresh interpreter;\nMAC-signed reply", "evidence_schema"),
          ("5 Represent", "EvidenceRecord:\ninputs, outcomes,\nfingerprints", "adapter"),
          ("6 Profile", "φ(E): 15\nfeatures relative\nto changed units", "profile"),
          ("7 Decide", "trust gate,\nwitness, eligibility,\nR ≤ τ", "calibrate.decide"),
          ("8 Audit", "ERS on a copy:\nP1-P9,\nresponses Δ$_j$", "ers, perturb")]
    n = len(st); w = 0.118; gap = (0.99 - 0.01 - n * w) / (n - 1)
    for i, (t, d, m) in enumerate(st):
        x = 0.01 + i * (w + gap)
        fc, ec = (GREEN_L, GREEN) if i == 7 else ((GREY_XL, GREY) if i == 0 else (BLUE_XL, BLUE))
        box(ax, x, 0.42, w, 0.47, fc=fc, ec=ec, lw=0.8)
        ax.text(x + w / 2, 0.85, t, fontsize=7.3, fontweight="bold", ha="center", va="top")
        ax.text(x + w / 2, 0.71, d, fontsize=6.3, ha="center", va="top", linespacing=1.12)
        ax.text(x + w / 2, 0.475, m, fontsize=6.0, ha="center", va="center", color=GREY, family="monospace")
        if i < n - 1: arrow(ax, (x + w, 0.655), (x + w + gap, 0.655), ls="--" if i == 6 else "-")
    box(ax, 0.01, 0.08, 0.98, 0.17, fc=VERM_L, ec=VERM, lw=0.7)
    ax.text(0.02, 0.165, "Fail-safe lane: a capture mismatch, broken chain, bad anchor, missing record or failed validation yields INSUFFICIENT; evidence that is not\n"
            "trusted can carry neither NDO nor DIV. Abstention on inadequate (ineligible or high-risk) evidence also yields INSUFFICIENT.", fontsize=6.6, va="center", linespacing=1.2)
    for i in (1, 3, 6):
        x = 0.01 + i * (w + gap) + w / 2
        arrow(ax, (x, 0.42), (x, 0.25), color=VERM)
    ax.text(0.01, 0.955, "Stages 1-7 produce one verdict per pair; stage 8 is a label-free audit that never modifies sealed evidence.", fontsize=6.6, va="center", color=GREY)
    save(fig, "fig_evidence_lifecycle")


# ---------------------------------------------------------------- Fig. 4  CEC methodology
def cec():
    fig, ax = canvas(DBL, 2.75)
    title(ax, 0.01, 0.985, "Fit (training projects only)", color=BLUE)
    box(ax, 0.01, 0.56, 0.17, 0.36, "Eligible labelled pairs\nno witness; blocker policy\nv8.0 (soft) or v8.0s / v8.1\n(strict); Y read only here", fs=6.6)
    box(ax, 0.20, 0.56, 0.17, 0.36, "Profile φ(E)\n15 features; counts\nlog(1+x); standardised;\nconstant features fixed\nat zero weight", fs=6.6, ec=BLUE)
    box(ax, 0.39, 0.56, 0.20, 0.36, "Sign-constrained L2 logistic\nweights ≤ 0 for evidence,\n≥ 0 for loss share\n(L-BFGS-B box bounds);\nλ in {0.3, 1, 3, 10} by inner\nproject-grouped 3-fold CV", fs=6.6, ec=BLUE)
    box(ax, 0.20, 0.13, 0.17, 0.32, "ERS responses Δ$_j$\n(B8 only; free sign)\ncomputed with the fold's\nCEC-without-ERS model", fs=6.6, fc=GREEN_L, ec=GREEN)
    arrow(ax, (0.18, 0.74), (0.20, 0.74)); arrow(ax, (0.37, 0.74), (0.39, 0.74)); arrow(ax, (0.37, 0.29), (0.45, 0.56), cs="arc3,rad=-0.2")
    title(ax, 0.61, 0.985, "Threshold (inner out-of-fold risks)", color=BLUE)
    ia = fig.add_axes([0.655, 0.33, 0.145, 0.5])
    c = np.linspace(0.02, 0.6, 60); r = 0.05 + 0.32 * c ** 1.3; ub = r + 0.16 / np.sqrt(c * 80)
    ia.plot(c, r, color=BLUE, lw=1.0, label="prefix risk"); ia.fill_between(c, r, ub, color=BLUE_L, lw=0, label="95% cluster UB")
    ia.plot(c, ub, color=BLUE, lw=0.6, ls="--"); ia.axhline(0.2, color=VERM, lw=0.7); ia.text(0.6, 0.205, r"$\alpha$", color=VERM, fontsize=7, va="bottom", ha="right")
    k = np.flatnonzero(ub <= 0.2); cs_ = c[k[-1]] if len(k) else None
    if cs_: ia.axvline(cs_, color=INK, lw=0.6, ls=":"); ia.text(cs_ + 0.01, 0.42, r"$\tau_\alpha$", fontsize=7)
    ia.set_xlim(0, 0.62); ia.set_ylim(0, 0.5); ia.set_xlabel("coverage", fontsize=6.5, labelpad=1); ia.set_ylabel("risk", fontsize=6.5, labelpad=1)
    ia.tick_params(labelsize=5.8, length=2); ia.text(0.31, 0.47, "schematic", fontsize=6, color=GREY, ha="center", style="italic")
    ax.text(0.615, 0.115, "rank eligible pairs by R; τ(α) = largest\nprefix whose one-sided 95% cluster-\nbootstrap upper bound ≤ α;\nnone qualifies → issue no NDO", fontsize=6.2, va="center", linespacing=1.1)
    arrow(ax, (0.59, 0.74), (0.635, 0.74))
    title(ax, 0.835, 0.985, "Decide (one record)", color=BLUE)
    steps = [("integrity_ok?", "no → INS", VERM), ("witness?", "yes → DIV", BLUE), ("eligible?", "no → INS", GREY), ("R(E) ≤ τ?", "yes → NDO\nno → INS", GREEN)]
    for i, (q, a, col) in enumerate(steps):
        y = 0.80 - i * 0.2
        box(ax, 0.835, y, 0.08, 0.13, q, fs=6.3, ec=INK)
        ax.text(0.922, y + 0.065, a, fontsize=6.4, va="center", color=col, fontweight="bold", linespacing=1.05)
        if i < 3: arrow(ax, (0.8725, y), (0.8725, y - 0.07))
    arrow(ax, (0.80, 0.5), (0.835, 0.5))
    save(fig, "fig_cec_method")


# ---------------------------------------------------------------- Fig. 5  ERS framework: properties x perturbations
PROPS = [("1", "Irrelevant-evidence invariance", "inv"), ("2", "Duplicate-evidence invariance", "inv"), ("3", "Relevant-evidence sensitivity", "mono"),
         ("4", "Observation-loss sensitivity", "mono"), ("5", "Divergence responsiveness", "pos"), ("6", "Provenance sensitivity", "mono"),
         ("7", "Integrity rejection", "pos"), ("8", "Reproducibility sensitivity", "mono"), ("E", "Environment check (code only)", "mono")]
PCOLS = ["P1", "P1b", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]
PMAP = {"P1": "3", "P1b": "3", "P2": "1", "P3": "2", "P4": "4", "P5": "8", "P6": "5", "P7": "6", "P8": "7", "P9": "E"}
KIND = {"inv": ("Invariance (negative control)", BLUE, r"$|\Delta|\leq 0.02$ and verdict unchanged"),
        "mono": ("Monotone (robustness)", ORANGE, r"$\Delta\geq -10^{-6}$ or verdict INS"),
        "pos": ("Prescribed outcome (positive control)", VERM, "P6: DIV (INS or $\\Delta>0$ accepted); P8: INS")}


def ers_framework():
    fig, ax = canvas(DBL, 2.65)
    x0, cw, y0, rh = 0.25, 0.04, 0.86, 0.083
    for j, p in enumerate(PCOLS):
        ax.text(x0 + (j + 0.5) * cw, y0 + 0.045, p, fontsize=7, ha="center", fontweight="bold")
    for i, (n, name, k) in enumerate(PROPS):
        y = y0 - (i + 1) * rh
        ax.text(0.01, y + rh / 2, f"{n}", fontsize=7, va="center", fontweight="bold", color=KIND[k][1])
        ax.text(0.03, y + rh / 2, name, fontsize=6.9, va="center", style="italic" if n == "E" else "normal")
        for j, p in enumerate(PCOLS):
            on = PMAP[p] == n
            ax.add_patch(Rectangle((x0 + j * cw + 0.002, y + 0.006), cw - 0.004, rh - 0.012, fc=KIND[k][1] if on else GREY_XL, ec="white", lw=0.5))
            if on: ax.text(x0 + (j + 0.5) * cw, y + rh / 2, "x", color="white", fontsize=6.5, ha="center", va="center", fontweight="bold")
    xr = x0 + len(PCOLS) * cw + 0.02
    title(ax, xr, 0.945, "Pass criterion (sbgv8/ers.py)")
    for i, (k, (lab, col, crit)) in enumerate(KIND.items()):
        y = 0.80 - i * 0.215
        box(ax, xr, y - 0.07, 0.315, 0.165, fc="white", ec=col, lw=0.9)
        ax.add_patch(Rectangle((xr + 0.008, y + 0.045), 0.018, 0.035, fc=col, ec="none"))
        ax.text(xr + 0.033, y + 0.062, lab, fontsize=6.9, va="center", fontweight="bold")
        ax.text(xr + 0.012, y + 0.0, crit, fontsize=6.7, va="center")
    ax.text(xr, 0.12, r"$\Delta_j(\mathcal{E})=\hat{\mathcal{R}}(T_j(\mathcal{E}))-\hat{\mathcal{R}}(\mathcal{E})$", fontsize=7.2)
    ax.text(xr, 0.055, "N/A trials never count as passes; monotone\nproperties accept a move to abstention.", fontsize=6.6, va="center", linespacing=1.1)
    ax.text(0.01, 0.03, "Each perturbation tests exactly one property; P1b is a stronger variant of P1.", fontsize=6.6, color=GREY)
    save(fig, "fig_ers_framework")


# ---------------------------------------------------------------- Fig. 6  perturbation taxonomy: edit target x mode
# ---------------------------------------------------------------- Fig. 7  evidence landscape (data)
def landscape():
    recs = [json.loads(l) for l in open(os.path.join(REPO, "datasets/v8/dev_records.jsonl"))]
    ARM = {"synthetic": "Synthetic", "quixbugs": "QuixBugs", "quixbugs_neg": "QuixBugs neg.", "bugsinpy_units": "BugsInPy units"}
    def arm(pid): return ARM[pid.split(":", 1)[0]]
    cnt = Counter((arm(r["pair_id"]), r.get("y")) for r in recs)
    arms = ["Synthetic", "QuixBugs", "QuixBugs neg.", "BugsInPy units"]
    assert [sum(v for (k, _), v in cnt.items() if k == a) for a in arms] == [150, 31, 85, 46], cnt  # Table: corpus
    F = json.load(open(os.path.join(PAPER, "audit/five_dataset_summary.json")))["per_dataset"]
    fig = plt.figure(figsize=(DBL, 2.45))
    a1 = fig.add_axes([0.11, 0.2, 0.245, 0.64]); a2 = fig.add_axes([0.40, 0.06, 0.275, 0.82]); a3 = fig.add_axes([0.785, 0.2, 0.2, 0.64])
    left = np.zeros(len(arms))
    for yv, lab, col, h in ((1, "Y = 1 (behaviour changes)", VERM, None), (0, "Y = 0 (preserved)", BLUE, None), (None, "unlabelled", "white", "////")):
        v = np.array([cnt[(a, yv)] for a in arms]); a1.barh(range(len(arms)), v, left=left, color=col, ec=INK, lw=0.4, hatch=h, height=0.62, label=lab)
        for i, (l, x) in enumerate(zip(left, v)):
            if x >= 6: a1.text(l + x / 2, i, str(x), ha="center", va="center", fontsize=6.5, color="white" if col != "white" else INK)
        left += v
    tot = sum(cnt.values())
    a1.set_yticks(range(len(arms))); a1.set_yticklabels(arms); a1.invert_yaxis(); a1.set_xlabel("executed pairs")
    a1.set_title(f"(a) Development corpus: {tot} executed pairs", fontsize=7.3, loc="left")
    a1.legend(frameon=False, fontsize=6.0, loc="lower right", handlelength=1.2); a1.set_xlim(0, 165)
    # (b) evidence categories
    a2.axis("off"); a2.set_xlim(0, 1); a2.set_ylim(0, 1)
    a2.text(0, 1.0, "(b) Evaluation evidence by category (A-E executed)", fontsize=7.3, va="bottom")
    cats = [("A", "Real program pairs", "312 executed (synthetic, QuixBugs, BugsInPy)", GREEN_L, GREEN, None),
            ("B", "Real-execution perturbation", "30 pairs, 720 trials (exploratory)", GREEN_L, GREEN, None),
            ("C", "Cross-platform analysis", "macOS = Linux on identical records", ORANGE_L, ORANGE, None),
            ("D", "Security and integrity", "25 macOS (final), 125 Linux (pre-fix)", ORANGE_L, ORANGE, None),
            ("E", "Unit and regression tests", "257 tests, macOS", GREEN_L, GREEN, None),
            ("F", "Template-derived artifact", "excluded: not executed, outcomes = labels", GREY_L, GREY, "////"),
            ("G", "Independent adjudication", "implemented, not executed", "white", VERM, None)]
    for i, (k, t, s, fc, ec, h) in enumerate(cats):
        y = 0.86 - i * 0.135
        a2.add_patch(Rectangle((0, y), 1, 0.118, fc=fc, ec=ec, lw=0.8, hatch=h))
        a2.text(0.035, y + 0.059, k, fontsize=8, fontweight="bold", va="center", color=ec)
        a2.text(0.11, y + 0.084, t, fontsize=6.2, fontweight="bold", va="center", bbox=dict(fc=fc if not h else "white", ec="none", pad=0.1))
        a2.text(0.11, y + 0.032, s, fontsize=5.7, va="center", bbox=dict(fc=fc if not h else "white", ec="none", pad=0.1))
    # (c) five-dataset template artifact
    ds = list(F)
    java = np.array([F[d]["languages"].get("Java", 0) if isinstance(F[d]["languages"], dict) else 0 for d in ds]); py = np.array([F[d]["n_pairs"] for d in ds]) - java
    a3.barh(range(len(ds)), java, color="white", ec=GREY, hatch="////", lw=0.5, height=0.6, label="Java text")
    a3.barh(range(len(ds)), py, left=java, color="white", ec=GREY, hatch="....", lw=0.5, height=0.6, label="Python text")
    a3.set_yticks(range(len(ds))); a3.set_yticklabels(ds, fontsize=6.6); a3.invert_yaxis(); a3.set_xlim(0, 75); a3.set_xlabel("records (12 templates; outcomes = labels)", fontsize=6.5)
    a3.set_title("(c) Five-dataset artifact (excluded)", fontsize=7.0, loc="left", color=GREY)
    a3.legend(frameon=False, fontsize=6.0, loc="lower right", bbox_to_anchor=(1.02, 0.0), ncol=1, handlelength=1.0)
    save(fig, "fig_evidence_landscape")




# ---------------------------------------------------------------- Fig. 11  threat model
def threat_model():
    fig, ax = canvas(DBL, 3.05)
    box(ax, 0.005, 0.14, 0.33, 0.83, fc=GREY_XL, ec=GREY, ls="--", r=0.015); title(ax, 0.013, 0.962, "Inside the OS sandbox (untrusted)", color=GREY)
    box(ax, 0.345, 0.14, 0.30, 0.83, fc=BLUE_XL, ec=BLUE, r=0.015); title(ax, 0.353, 0.962, "Trusted controller and validator", color=BLUE)
    box(ax, 0.655, 0.14, 0.34, 0.83, fc="white", ec=INK, r=0.015); title(ax, 0.663, 0.962, "Evidence at rest and review")
    tag(ax, 0.06, 0.87, "A1", VERM); ax.text(0.09, 0.87, "adversarial program under test", fontsize=6.8, va="center")
    tag(ax, 0.71, 0.87, "A2", VERM); ax.text(0.74, 0.87, "keyless post-hoc writer", fontsize=6.8, va="center")
    tag(ax, 0.71, 0.80, "A3", VERM); ax.text(0.74, 0.80, "evidence substituter", fontsize=6.8, va="center")
    rows = [  # (attack surface text, mitigation text, outcome, colour, y, x-zone)
        ("A1  forge result on stdout", "HMAC result frame, per-run key", "prevented", GREEN, 0.71),
        ("A1  hide / alter stdout (A08)", "tee to fd 2 + parent judge()", "forced INS", GREEN, 0.61),
        ("A1  patch canonicaliser / forge\n      via harness (A01, A02)", "shadow re-observation (optional)", "detected only", ORANGE, 0.49),
        ("A1  sense analysis (SENSE04b:\n      code-object file path)", "argv / __file__ masking (partial)", "SUCCEEDS", VERM, 0.37),
        ("A1  forge tee record, guessed\n      nonce (A17)", "nonce-framed records", "DIV → INS", ORANGE, 0.25)]
    for txt, mit, out, col, y in rows:
        box(ax, 0.015, y - 0.045, 0.31, 0.09, txt, fs=6.4, ha="left", ec=VERM, fc="white")
        box(ax, 0.355, y - 0.035, 0.19, 0.07, mit, fs=6.2, ec=BLUE)
        arrow(ax, (0.325, y), (0.355, y), color=VERM)
        tag(ax, 0.597, y, out, col, color="white" if col != ORANGE else INK, fs=5.8)
    rows2 = [("A2  edit field, re-chain log\n      (P04)", "anchor HMAC_K over\nall digests; validate_dir", "forced INS", GREEN, 0.71),
             ("A2  strip / alter anchor", "require anchor; key K", "forced INS", GREEN, 0.575),
             ("A3  substitute genuine evidence\n      of another program (P06)", "source binding (optional,\nreviewer-supplied)", "detected only", ORANGE, 0.44),
             ("key holder re-anchors (P08)", "out of scope", "SUCCEEDS", VERM, 0.305)]
    for txt, mit, out, col, y in rows2:
        box(ax, 0.665, y - 0.04, 0.165, 0.08, txt, fs=6.1, ha="left", ec=VERM if "scope" not in mit else GREY, fc="white", ls="-" if "scope" not in mit else "--")
        box(ax, 0.84, y - 0.04, 0.15, 0.08, mit, fs=6.1, ec=BLUE if "scope" not in mit else GREY, ls="-" if "scope" not in mit else "--")
        tag(ax, 0.915, y - 0.062, out, col, color="white" if col != ORANGE else INK, fs=5.8)
    box(ax, 0.665, 0.15, 0.325, 0.065, "Out of scope: holders of K, host / kernel / sandbox compromise,\nnative-code attacks on the harness, side channels, sandbox escape", fs=5.8, ls="--", ec=GREY)
    ax.text(0.005, 0.085, "Outcomes from the macOS re-run at the final commit (25 attacks and probes) and the original suite. Green: the false verdict is prevented (forced INS or no effect).", fontsize=6.5)
    ax.text(0.005, 0.045, "Orange: detected but the effective verdict is unchanged, or a true divergence is denied. Vermillion: succeeds with no check firing.", fontsize=6.5)
    save(fig, "fig_threat_model")


# ---------------------------------------------------------------- Fig. 12  claim-to-evidence traceability
def traceability():
    fig, ax = canvas(DBL, 2.35)
    heads = ["Manuscript claim", "Register entry", "Derived artifact", "Generating script", "Raw machine-readable source", "Version anchor"]
    xs = [0.005, 0.175, 0.335, 0.505, 0.67, 0.865]; ws = [0.16, 0.15, 0.16, 0.155, 0.185, 0.13]
    for x, w, h in zip(xs, ws, heads): ax.text(x + w / 2, 0.955, h, fontsize=7.0, fontweight="bold", ha="center", va="top")
    lanes = [["Plain DT risk 0.169\n[0.086, 0.354] (RQ3)", "NUMERICAL_CLAIM_\nAUDIT.md, RQ table", "audit/stats_summary.json\nrules.b1_plain_dt", "stats_recompute.py\n(recomputed once)", "datasets/v8/\ndev_records.jsonl", "linux branch,\nmd5 07e57a80"],
             ["Probe failed P2 on 109\nof 227 records (RQ2)", "CLAIM_EVIDENCE_\nREGISTER #10", "Table: ERS matrix\n(tab_ers.tex)", "sbgv8.ers.run_matrix\n(repository run)", "results/v8/linux/\nperturb/posthoc_matrix", "pre-fix: linux;\npost-fix: b9b8a86c"],
             ["SENSE04b succeeds;\nfix is partial (RQ1)", "CLAIM_EVIDENCE_\nREGISTER #26-27", "audit/security_\noutcomes.json", "audit_security_\nrerun.py (earlier run)", "audit/security_\nrerun_darwin.json", "HEAD 07ecd5b7,\nmacOS arm64"]]
    fills = [BLUE_XL, BLUE_XL, "white", GREEN_L, GREY_XL, "white"]
    for i, lane in enumerate(lanes):
        y = 0.68 - i * 0.255
        for j, (x, w, t) in enumerate(zip(xs, ws, lane)):
            box(ax, x, y, w, 0.2, t, fs=6.3, fc=fills[j], ec=BLUE if j < 2 else (GREEN if j == 3 else INK), lw=0.6)
            if j < 5: arrow(ax, (x + w, y + 0.1), (xs[j + 1], y + 0.1))
    ax.text(0.005, 0.07, "Every number in the paper follows one such chain. Numbers whose chain ends in report text without a raw source (e.g. Podman isolation, a 250-pair 'independent'", fontsize=6.5)
    ax.text(0.005, 0.03, "validation, slopes near 1) are excluded and listed in NUMERICAL_CLAIM_AUDIT.md. No script in this chain was re-run for the revision.", fontsize=6.5)
    save(fig, "fig_traceability")


# ---------------------------------------------------------------- security outcomes (data: audit/security_outcomes.json)
OUT = [("blocked", BLUE, None, "blocked (INS)"), ("detected", SKY_ := "#56B4E9", None, "detected"), ("mitigated", GREEN, None, "no effect (true verdict)"),
       ("insufficient_unexplained", "white", "////", "INS, cause unrecorded"), ("succeeded", VERM, None, "succeeded"), ("unresolved", GREY_L, "....", "report text only")]
SHORT = {"in-process harness/runtime tampering": "in-process tamper", "result-channel / fd attack": "result channel/fd", "evaluation-awareness sensing": "eval. sensing",
         "cross-pair evidence substitution": "substitution", "post-hoc evidence tampering": "post-hoc tamper", "sandbox / isolation escape": "sandbox escape",
         "resource exhaustion": "resource exhaust."}


ALL = {f.__name__: f for f in (motivation, architecture, lifecycle, cec, ers_framework, landscape, threat_model, traceability)}
if __name__ == "__main__":
    for n in (sys.argv[1:] or ALL):
        ALL[n](); print("wrote", n)
