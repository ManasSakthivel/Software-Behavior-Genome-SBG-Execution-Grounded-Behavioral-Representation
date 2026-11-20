"""Shared visual language for every figure in the SBG V8 manuscript (imported by make_figures.py and make_stat_figures.py).
One serif family (matches IEEE body text), one restrained Okabe-Ito-derived palette with fixed semantic roles, 7-8 pt text, vector PDF output.
Roles: SBG/trusted = blue; risk, attack, residual = vermillion; verified/pass = green; baseline = orange; untrusted/neutral = grey."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"], "mathtext.fontset": "stix",
    "font.size": 8, "axes.labelsize": 8, "legend.fontsize": 6.8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "axes.linewidth": 0.6, "lines.linewidth": 1.0, "hatch.linewidth": 0.45, "pdf.fonttype": 42, "ps.fonttype": 42,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.pad_inches": 0.02})

INK = "#1F1F1F"
BLUE, BLUE_L, BLUE_XL = "#0072B2", "#D6E6F3", "#EEF4FA"      # SBG / trusted
VERM, VERM_L = "#D55E00", "#F9E0CF"                          # risk / attack / residual
GREEN, GREEN_L = "#009E73", "#D3EEE5"                        # verified / pass
ORANGE, ORANGE_L = "#E69F00", "#FBEBC7"                      # baselines
GREY, GREY_L, GREY_XL = "#7F7F7F", "#E4E4E4", "#F4F4F4"      # untrusted / neutral
SKY, PURPLE = "#56B4E9", "#CC79A7"
FS = 7.5
COL, DBL = 3.5, 7.16   # IEEE column / double-column width (in)

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(HERE), "figures")
os.makedirs(FIG, exist_ok=True)
PREVIEW = os.environ.get("SBG_FIG_PREVIEW")   # optional dir for PNG previews


def save(fig, name, **kw):
    fig.savefig(os.path.join(FIG, name + ".pdf"), **kw)
    if PREVIEW: fig.savefig(os.path.join(PREVIEW, name + ".png"), dpi=170, **kw)
    plt.close(fig)
    p = os.path.join(FIG, name + ".pdf"); assert os.path.getsize(p) > 1000, p


def canvas(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text="", fc="white", ec=INK, lw=0.7, hatch=None, fs=FS, bold=False, ls="-", r=0.01, ha="center", va="center", color=INK, z=1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, hatch=hatch, ls=ls, zorder=z))
    if text:
        tx = x + w / 2 if ha == "center" else x + 0.008
        ty = y + h / 2 if va == "center" else y + h - 0.01
        ax.text(tx, ty, text, ha=ha, va=va, fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.15, color=color, zorder=z + 1)


def title(ax, x, y, text, fs=FS + 0.3, color=INK, ha="left"):
    ax.text(x, y, text, fontsize=fs, fontweight="bold", va="top", ha=ha, color=color)


def arrow(ax, p, q, text=None, ls="-", lw=0.8, color=INK, off=(0, 0.014), fs=7, cs="arc3", both=False, ha="center", z=3):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="<|-|>" if both else "-|>", mutation_scale=7, lw=lw, ls=ls, color=color, connectionstyle=cs,
                                 shrinkA=1, shrinkB=1, zorder=z))
    if text:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, ha=ha, va="center", fontsize=fs, style="italic", color=color,
                bbox=dict(fc="white", ec="none", pad=0.3), zorder=z + 1)


def tag(ax, x, y, text, fc, color="white", fs=6.8):
    ax.text(x, y, text, fontsize=fs, color=color, ha="center", va="center", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25,rounding_size=0.15", fc=fc, ec="none"), zorder=6)
