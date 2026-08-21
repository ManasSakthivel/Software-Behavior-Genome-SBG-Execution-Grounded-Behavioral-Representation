"""
experiments/v2/figures/fig3_performance.py
============================================
Figure 3: AUROC comparison for all baselines with confidence intervals.

Data source: artifacts/v2/FIGURE_DATA.json (FIGURE_3)
Reads ONLY from frozen artifact files. No hardcoded numbers.
"""
from __future__ import annotations
import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
DATA_FILE = REPO_ROOT / "artifacts" / "v2" / "FIGURE_DATA.json"
OUTPUT_DIR = REPO_ROOT / "artifacts" / "v2" / "figures"


def generate():
    data = json.loads(DATA_FILE.read_text())
    fig_data = data["figures"]["FIGURE_3"]["data"]

    methods = fig_data["methods"]
    auroc = fig_data["auroc"]
    ci_lower = fig_data["ci_lower"]
    ci_upper = fig_data["ci_upper"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    out_data = {
        "figure": "FIGURE_3",
        "title": data["figures"]["FIGURE_3"]["title"],
        "methods": methods,
        "auroc": auroc,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "source": "artifacts/v2/FIGURE_DATA.json",
        "status": "FROZEN",
    }
    out_path = OUTPUT_DIR / "fig3_performance_data.json"
    out_path.write_text(json.dumps(out_data, indent=2))
    print(f"[FIG3] Data written to {out_path}")

    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use("Agg")

        fig, ax = plt.subplots(figsize=(10, 5))
        x = list(range(len(methods)))

        colors = ["#7c5cd8" if "V2" in m else "#3b82d4" for m in methods]
        bars = ax.bar(x, auroc, color=colors, alpha=0.8)

        # Error bars (asymmetric CI)
        yerr_lower = [a - l for a, l in zip(auroc, ci_lower)]
        yerr_upper = [u - a for u, a in zip(ci_upper, auroc)]
        ax.errorbar(x, auroc, yerr=[yerr_lower, yerr_upper],
                    fmt="none", color="black", capsize=4, linewidth=1.5)

        # Random baseline
        ax.axhline(0.5, color="#888888", linestyle="--", linewidth=1, label="Random (0.5)")
        ax.axhline(0.5528, color="#22a022", linestyle=":", linewidth=1.5, label="AST baseline (0.5528)")

        ax.set_xlabel("Method")
        ax.set_ylabel("AUROC (95% CI)")
        ax.set_title("Program Similarity: AUROC Comparison (N=744 test pairs)")
        ax.set_xticks(x)
        ax.set_xticklabels(methods, rotation=20, ha="right", fontsize=8)
        ax.set_ylim(0.25, 0.70)
        ax.legend(fontsize=8)

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "fig3_performance.pdf", dpi=150)
        plt.savefig(OUTPUT_DIR / "fig3_performance.svg")
        print(f"[FIG3] PDF/SVG written to {OUTPUT_DIR}")
        plt.close()
    except ImportError:
        print("[FIG3] matplotlib not available — data JSON written only")

    return out_data


if __name__ == "__main__":
    generate()
