"""Vector diagrams for the SBG V8 IEEE Access paper (matplotlib only; grayscale-safe: gray fills + hatches + line styles, fonts >= 7 pt).
Outputs in ../figures/: fig_architecture.pdf (7 in), fig_pipeline.pdf (3.5 in), fig_perturbation_taxonomy.pdf (7 in), fig_security_outcomes.pdf (3.5 in).
Content follows audit/ARCHITECTURE_AND_DEFINITIONS.md and audit/security_outcomes.json (code @ 07ecd5b7)."""
import json, os
from collections import Counter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.dirname(HERE)
FIG = os.path.join(PAPER, "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "pdf.fonttype": 42, "ps.fonttype": 42, "hatch.linewidth": 0.5})
FS = 7.5  # body font size; nothing below 7 pt
PREVIEW = os.environ.get("SBG_FIG_PREVIEW")  # optional dir for 200-dpi PNG previews


def save(fig, name, **kw):
    fig.savefig(os.path.join(FIG, name + ".pdf"), **kw)
    if PREVIEW: fig.savefig(os.path.join(PREVIEW, name + ".png"), dpi=200, **kw)
    plt.close(fig)


def box(ax, x, y, w, h, text, fc="white", ec="black", lw=0.8, hatch=None, fs=FS, bold=False, ls="-", r=0.012, ha="center", va="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, hatch=hatch, ls=ls))
    if text:
        tx = x + w / 2 if ha == "center" else x + 0.008
        ax.text(tx, y + h / 2 if va == "center" else y + h - 0.012, text, ha=ha, va=va, fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.15)


def arrow(ax, p, q, text=None, ls="-", lw=0.8, off=(0, 0.012), fs=7, cs="arc3", both=False, ha="center"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="<|-|>" if both else "-|>", mutation_scale=7, lw=lw, ls=ls, color="black", connectionstyle=cs, shrinkA=1, shrinkB=1))
    if text:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, ha=ha, va="center", fontsize=fs, style="italic")


def canvas(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


# ------------------------------------------------------------------ 1. architecture (7 in)
def architecture():
    fig, ax = canvas(7.0, 4.0)
    # zones (x: untrusted 0.005-0.285 | trusted 0.30-0.60 | evidence/decision 0.615-0.995)
    box(ax, 0.005, 0.10, 0.28, 0.885, "", fc="0.93", lw=0.9, ls="--", r=0.02)
    ax.text(0.012, 0.975, "UNTRUSTED", fontsize=8, fontweight="bold", va="top")
    ax.text(0.012, 0.947, "fresh sandboxed child per run", fontsize=7, va="top")
    box(ax, 0.30, 0.10, 0.30, 0.885, "", fc="white", lw=1.3, r=0.02)
    ax.text(0.307, 0.975, "TRUSTED CONTROLLER", fontsize=8, fontweight="bold", va="top")
    ax.text(0.307, 0.947, "parent process; holds key K", fontsize=7, va="top")
    box(ax, 0.615, 0.10, 0.38, 0.885, "", fc="white", lw=0.9, r=0.02)
    ax.text(0.622, 0.975, "EVIDENCE, VALIDATION, DECISION", fontsize=8, fontweight="bold", va="top")

    # untrusted: sandbox boundary (hatched frame) with inner boxes
    box(ax, 0.017, 0.13, 0.256, 0.785, "", fc="white", lw=0.8, hatch="////")
    box(ax, 0.03, 0.70, 0.23, 0.195, "Sandbox boundary\nmacOS: sandbox-exec\nLinux: bwrap --unshare-net\n  --ro-bind / /\nrlimits CPU, NOFILE, FSIZE;\nprocess-group kill; env\nallow-list (no key)",
        fc="white", fs=7, lw=0.6, ha="left")
    box(ax, 0.03, 0.495, 0.23, 0.16, "_tee_child.py (stub)\ntees each sys.stdout\nwrite to fd 2 as a\nnonce-framed record", fc="white", ha="left")
    box(ax, 0.03, 0.31, 0.23, 0.145, "harness.py (V7-B)\ncanonicaliser, Cap;\nargv, __file__ masked", fc="white", ha="left")
    box(ax, 0.03, 0.155, 0.23, 0.115, "Program under test\nbase B  /  variant V", fc="0.80", bold=True)
    arrow(ax, (0.145, 0.495), (0.145, 0.455)); arrow(ax, (0.145, 0.31), (0.145, 0.27))

    # trusted controller
    box(ax, 0.312, 0.745, 0.276, 0.16, "Controller\ncollect.run_capture\nunmodified V7-B runner;\nfinalize() spy: hits/branches", fc="white")
    box(ax, 0.312, 0.475, 0.276, 0.225, "Collector\nprocsep.Supervisor\nowns child fd 1/2 pipes;\nparses tee records;\ntee text == harness stdout?\nmatch | mismatch | incomplete", fc="white")
    box(ax, 0.312, 0.305, 0.276, 0.13, "Result-frame check\nSBGV7F1 + HMAC(per-run key)\non a dedicated fd", fc="white")
    box(ax, 0.312, 0.135, 0.276, 0.13, "Shadow re-observer\n(optional) own runner,\nreturn values only", fc="white", ls="--")

    # untrusted <-> trusted arrows
    arrow(ax, (0.26, 0.575), (0.312, 0.575))
    ax.text(0.286, 0.60, "fd 2", fontsize=7, ha="center", style="italic", bbox=dict(fc="white", ec="none", pad=0.4))
    arrow(ax, (0.26, 0.37), (0.312, 0.37))
    ax.text(0.286, 0.395, "frame", fontsize=7, ha="center", style="italic", bbox=dict(fc="white", ec="none", pad=0.4))
    arrow(ax, (0.312, 0.79), (0.26, 0.79))
    ax.text(0.286, 0.815, "spawn", fontsize=7, ha="center", style="italic", bbox=dict(fc="white", ec="none", pad=0.4))
    arrow(ax, (0.312, 0.20), (0.26, 0.20), ls="--")

    # evidence / validation / decision
    box(ax, 0.627, 0.585, 0.15, 0.32, "Evidence dir\n\nevidence.jsonl\n(SHA-256 chain)\nverdict.json\nv8_parts.json\nv8_capture.json\nv8_anchor.json\n(HMAC, key K)", fc="0.86", fs=7)
    box(ax, 0.79, 0.585, 0.193, 0.32, "Validator\nvalidate_dir\n\nschema; binding to\nlog head; seq/nonce;\nper-run status,\ntimings, stdout\ndigest; anchor MAC", fc="white", fs=7)
    box(ax, 0.627, 0.335, 0.356, 0.21, "Decision\nrecord -> profile phi (15 features)\n-> sign-constrained logistic risk\nuntrusted -> INSUFFICIENT; witness -> DIV\nNDO iff eligible and risk <= tau", fc="white", fs=7)
    box(ax, 0.627, 0.13, 0.356, 0.165, "Reviewer checks (optional)\nexpected sources, pinned head, shadow\nraise issues; verdict NOT changed", fc="white", ls="--", fs=7)
    arrow(ax, (0.588, 0.825), (0.627, 0.80))
    arrow(ax, (0.588, 0.59), (0.627, 0.68))
    ax.text(0.607, 0.715, "write", fontsize=7, ha="center", style="italic", rotation=90)
    arrow(ax, (0.777, 0.745), (0.79, 0.745))
    arrow(ax, (0.886, 0.585), (0.886, 0.545))
    ax.text(0.893, 0.565, "trusted?", fontsize=7, ha="left", va="center", style="italic")
    arrow(ax, (0.588, 0.20), (0.627, 0.20), ls="--")
    # legend
    ax.text(0.008, 0.06, "Solid: always on the verdict path.  Dashed: optional, detection only.  Hatched: OS sandbox boundary.", fontsize=7, va="center")
    ax.text(0.008, 0.025, "Key K never enters the child.  No code path invokes Podman; Linux confinement is bwrap/unshare.", fontsize=7, va="center")
    save(fig, "fig_architecture")


# ------------------------------------------------------------------ 2. evidence-to-verdict pipeline (3.5 in)
def pipeline():
    fig, ax = canvas(3.5, 5.0)
    steps = [("Pair ingestion", "(B, V, entry, inputs, cfg)"),
             ("Sandboxed execution", "V7-B engine; fresh child per run"),
             ("Trusted capture", "tee records + HMAC result frame"),
             ("Sealing", "chain, sidecar, capture,\nanchor MAC"),
             ("Integrity validation", "validate_dir: trusted?"),
             ("Evidence record", "adapter; integrity_ok"),
             ("Profile phi(E), 15 features", "activation, branch coverage,\nmultiplicity, repetition, obs.\nproxy, diversity, reproducibility,\nloss, channels, provenance,\nintegrity, environment"),
             ("Calibrated risk", "sign-constrained L2 logistic;\ntau: cluster-bootstrap\nupper bound <= alpha")]
    x, w = 0.03, 0.63
    hs = [0.062, 0.062, 0.062, 0.08, 0.062, 0.062, 0.15, 0.10]
    y = 0.985; c = []
    for (t, sub), h in zip(steps, hs):
        y0 = y - h
        box(ax, x, y0, w, h, "", fc="white")
        ax.text(x + 0.015, y - 0.009, t, fontsize=7.5, fontweight="bold", va="top")
        ax.text(x + 0.015, y - 0.033, sub, fontsize=7, va="top", linespacing=1.1)
        c.append((y0, y)); y = y0 - 0.02
    for (a0, _), (_, b1) in zip(c, c[1:]):
        arrow(ax, (x + w / 2, a0), (x + w / 2, b1))
    hv = 0.165; yv = y - hv
    box(ax, x, yv, w, hv, "", fc="0.90")
    ax.text(x + 0.015, yv + hv - 0.009, "Verdict gates, in order", fontsize=7.5, fontweight="bold", va="top")
    ax.text(x + 0.015, yv + hv - 0.033, "1 untrusted / integrity fail -> INS\n2 witness -> DIVERGENT\n3 eligible, risk <= tau -> NDO\n4 otherwise -> INSUFFICIENT\neligible policy: v8.0 soft | v8.0s strict | v8.1",
            fontsize=7, va="top", linespacing=1.15)
    arrow(ax, (x + w / 2, c[-1][0]), (x + w / 2, yv + hv))
    sx, sw = 0.70, 0.285
    # reviewer checks beside sealing/integrity rows
    rt, rb = c[3][1], c[4][0]
    box(ax, sx, rb, sw, rt - rb, "Reviewer\nchecks\n(optional):\nshadow, sources,\npinned head;\nissues only", fc="white", ls="--", fs=7)
    ym = (c[4][0] + c[4][1]) / 2
    arrow(ax, (x + w, ym), (sx, ym), ls="--")
    # ERS loop beside profile / risk rows
    et, eb = c[6][1], c[7][0]
    box(ax, sx, eb, sw, et - eb, "ERS audit\n(P1-P9)\n\npost-hoc edit\nE -> T_j(E)\n\nDelta_j =\nrisk(T_j E)\n - risk(E)\n\npass / fail\n / N/A", fc="0.94", fs=7)
    yp = (c[6][0] + c[6][1]) / 2; yr = (c[7][0] + c[7][1]) / 2
    arrow(ax, (sx, yp), (x + w, yp))
    ax.text((sx + x + w) / 2, yp + 0.012, "T_j E", fontsize=7, ha="center", style="italic")
    arrow(ax, (x + w, yr), (sx, yr))
    ax.text((sx + x + w) / 2, yr + 0.012, "risk", fontsize=7, ha="center", style="italic")
    save(fig, "fig_pipeline")


# ------------------------------------------------------------------ 3. perturbation taxonomy (7 in)
PERT = [("P1", "delete sole reachers of a changed unit/channel"), ("P1b", "delete covers of least-multiplicity unit"), ("P2", "add synthetic inputs on unchanged lines"),
        ("P3", "add copies flagged duplicate_of"), ("P4", "mask one observation channel"), ("P5", "flip 50% SAME non-det.; halve repeats"),
        ("P6", "add synthetic CONFIRMED_DIFF witness"), ("P7", "provenance := label_derived / untrusted"), ("P8", "integrity_ok := False"), ("P9", "env_consistent := False")]
PROPS = [("Prop. 1", "Irrelevant-evidence invariance"), ("Prop. 2", "Duplicate-evidence invariance"), ("Prop. 3", "Relevant-evidence sensitivity"),
         ("Prop. 4", "Observation-loss sensitivity"), ("Prop. 5", "Divergence responsiveness"), ("Prop. 6", "Provenance sensitivity"),
         ("Prop. 7", "Integrity rejection"), ("Prop. 8", "Reproducibility sensitivity"), ("(code only)", "Environment sensitivity")]
P2PROP = {"P1": 2, "P1b": 2, "P2": 0, "P3": 1, "P4": 3, "P5": 7, "P6": 4, "P7": 5, "P8": 6, "P9": 8}
CTRL = [("Negative control", "invariance:\n|Delta| <= 0.02, verdict\nunchanged (P2, P3)", "-", "0.75", None),
        ("Positive control", "exact outcome: DIV (P6);\nintegrity_ok=0 and INS (P8)", "--", "white", "////"),
        ("Robustness (monotone)", "Delta >= -1e-6 or INS;\nabstention counts as pass\n(P1, P1b, P4, P5, P7, P9)", ":", "white", "....")]
P2CTRL = {"P2": 0, "P3": 0, "P6": 1, "P8": 1, "P1": 2, "P1b": 2, "P4": 2, "P5": 2, "P7": 2, "P9": 2}


def taxonomy():
    fig, ax = canvas(7.0, 3.3)
    X1, W1, X2, W2, X3, W3 = 0.01, 0.37, 0.435, 0.265, 0.755, 0.24
    ax.text(X1, 0.975, "Perturbation (post-hoc edit of a record copy)", fontsize=7.5, fontweight="bold", va="top")
    ax.text(X2, 0.975, "ERS property (Linux numbering)", fontsize=7.5, fontweight="bold", va="top")
    ax.text(X3, 0.975, "Control type (ers._eval)", fontsize=7.5, fontweight="bold", va="top")
    top, bot = 0.91, 0.02
    dy = (top - bot) / len(PERT); py = {}
    for k, (pid, d) in enumerate(PERT):
        y = top - (k + 1) * dy + 0.008; h = dy - 0.016; c = CTRL[P2CTRL[pid]]
        box(ax, X1, y, W1, h, "", fc=c[3], hatch=c[4], lw=0.7)
        ax.text(X1 + 0.008, y + h / 2, pid, fontsize=7.5, fontweight="bold", va="center", bbox=dict(fc="white", ec="none", pad=0.4))
        ax.text(X1 + 0.05, y + h / 2, d, fontsize=7, va="center", bbox=dict(fc="white", ec="none", pad=0.4))
        py[pid] = y + h / 2
    dy2 = (top - bot) / len(PROPS); qy = []
    for k, (pn, d) in enumerate(PROPS):
        y = top - (k + 1) * dy2 + 0.01; h = dy2 - 0.02
        box(ax, X2, y, W2, h, f"{pn}: {d}", fc="white", lw=0.7, fs=7, ls="--" if k == 8 else "-")
        qy.append(y + h / 2)
    for pid, j in P2PROP.items():
        ax.plot([X1 + W1, X2], [py[pid], qy[j]], color="black", lw=0.8, ls=CTRL[P2CTRL[pid]][2])
    dy3 = (top - bot) / 3
    for k, (t, d, ls, fc, hch) in enumerate(CTRL):
        y = top - (k + 1) * dy3 + 0.03; h = dy3 - 0.06
        box(ax, X3, y, W3, h, "", fc=fc, hatch=hch, lw=0.7)
        ax.text(X3 + 0.01, y + h - 0.015, t, fontsize=7.5, fontweight="bold", va="top", bbox=dict(fc="white", ec="none", pad=0.4))
        ax.plot([X3 + 0.165, X3 + 0.225], [y + h - 0.03] * 2, color="black", lw=1.0, ls=ls)
        ax.text(X3 + 0.01, y + 0.015, d, fontsize=7, va="bottom", linespacing=1.15, bbox=dict(fc="white", ec="none", pad=0.4))
    save(fig, "fig_perturbation_taxonomy")


# ------------------------------------------------------------------ 4. security outcomes (3.5 in)
OUT = [("blocked", "0.15", None), ("detected", "0.45", None), ("mitigated", "0.75", None), ("insufficient_unexplained", "white", "////"), ("succeeded", "white", "xxxx"), ("unresolved", "0.92", "....")]
LBL = {"blocked": "blocked (INS)", "detected": "detected", "mitigated": "no effect (true verdict)", "insufficient_unexplained": "INS, cause unrecorded",
       "succeeded": "succeeded", "unresolved": "report-text only"}
SHORT = {"in-process harness/runtime tampering": "in-process tamper", "result-channel / fd attack": "result channel/fd", "evaluation-awareness sensing": "eval. sensing",
         "cross-pair evidence substitution": "substitution", "post-hoc evidence tampering": "post-hoc tamper", "sandbox / isolation escape": "sandbox escape",
         "resource exhaustion": "resource exhaust."}


def security():
    rows = json.load(open(os.path.join(PAPER, "audit", "security_outcomes.json")))
    panels = [("(a) macOS, HEAD 07ecd5b7, executed in this audit", lambda r: r["suite"] == "audit_rerun_head_darwin"),
              ("(b) Linux suite as recorded (pre-fix) + report-only claims", lambda r: r["suite"] in ("linux_container_74", "linux_tamper_51", "linux_podman_isolation", "linux_report_claims"))]
    fig, axes = plt.subplots(2, 1, figsize=(3.5, 4.6), gridspec_kw=dict(height_ratios=[5, 7], hspace=0.55))
    for ax, (title, sel) in zip(axes, panels):
        sub = [r for r in rows if sel(r) and r["class"] in SHORT]
        cls = [c for c in SHORT if any(r["class"] == c for r in sub)]
        cnt = {c: Counter(r["outcome"] for r in sub if r["class"] == c) for c in cls}
        left = [0] * len(cls)
        for o, fc, h in OUT:
            v = [cnt[c].get(o, 0) for c in cls]
            if not any(v): continue
            ax.barh(range(len(cls)), v, left=left, color=fc, edgecolor="black", hatch=h, lw=0.5, label=LBL[o], height=0.68)
            for i, (l, x) in enumerate(zip(left, v)):
                if x: ax.text(l + x / 2, i, str(x), ha="center", va="center", fontsize=7, color="white" if fc in ("0.15", "0.45") else "black",
                              bbox=None if fc in ("0.15", "0.45") else dict(fc="white", ec="none", pad=0.15))
            left = [a + b for a, b in zip(left, v)]
        ax.set_yticks(range(len(cls))); ax.set_yticklabels([f"{SHORT[c]} ({sum(cnt[c].values())})" for c in cls], fontsize=7)
        ax.invert_yaxis(); ax.set_xlabel("attacks / probes", fontsize=7); ax.tick_params(labelsize=7)
        ax.set_title(title, fontsize=7.5, loc="left")
        for s in ("top", "right"): ax.spines[s].set_visible(False)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(fc=fc, ec="black", hatch=h, lw=0.5, label=LBL[o]) for o, fc, h in OUT], loc="lower center", ncol=2, fontsize=7, frameon=False,
               bbox_to_anchor=(0.5, -0.11), handlelength=1.6, columnspacing=1.0)
    save(fig, "fig_security_outcomes", bbox_inches="tight")


if __name__ == "__main__":
    architecture(); pipeline(); taxonomy(); security()
    for f in ("fig_architecture", "fig_pipeline", "fig_perturbation_taxonomy", "fig_security_outcomes"):
        p = os.path.join(FIG, f + ".pdf"); assert os.path.getsize(p) > 1000, p; print(p)
