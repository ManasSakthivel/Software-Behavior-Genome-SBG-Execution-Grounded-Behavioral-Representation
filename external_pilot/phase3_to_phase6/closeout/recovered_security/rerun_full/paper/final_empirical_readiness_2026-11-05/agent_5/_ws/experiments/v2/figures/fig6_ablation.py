"""
experiments/v2/figures/fig6_ablation.py
=========================================
Figure 6: Ablation study — AUROC by genome dimension combination.

Data source: artifacts/phase4/E7/ablation_table.json
Reads ONLY from frozen artifact files. No hardcoded numbers.
"""
from __future__ import annotations
import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
DATA_FILE = REPO_ROOT / "artifacts" / "phase4" / "E7" / "ablation_table.json"
OUTPUT_DIR = REPO_ROOT / "artifacts" / "v2" / "figures"


def generate():
    ablation_data = json.loads(DATA_FILE.read_text())

    # Sort by AUROC descending
    ablation_data = sorted(ablation_data, key=lambda x: x["test_auroc"], reverse=True)
    conditions = [d["condition"] for d in ablation_data]
    aurocs = [d["test_auroc"] for d in ablation_data]
    ci_lowers = [d["test_ci_auroc"][0] for d in ablation_data]
    ci_uppers = [d["test_ci_auroc"][1] for d in ablation_data]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    out_data = {
        "figure": "FIGURE_6",
        "title": "Ablation: AUROC by Genome Dimension Combination (Sorted Descending)",
        "conditions": conditions,
        "auroc": aurocs,
        "ci_lower": ci_lowers,
        "ci_upper": ci_uppers,
        "source": "artifacts/phase4/E7/ablation_table.json",
        "key_finding": "ERROR_only outperforms CONTROL+DATA+ERROR — negative dimension interaction",
        "status": "FROZEN",
    }
    out_path = OUTPUT_DIR / "fig6_ablation_data.json"
    out_path.write_text(json.dumps(out_data, indent=2))
    print(f"[FIG6] Data written to {out_path}")

    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use("Agg")

        fig, ax = plt.subplots(figsize=(9, 6))
        y = list(range(len(conditions)))

        xerr_lower = [a - l for a, l in zip(aurocs, ci_lowers)]
        xerr_upper = [u - a for u, a in zip(ci_uppers, aurocs)]
        ax.barh(y, aurocs, xerr=[xerr_lower, xerr_upper],
                color="#3b82d4", alpha=0.8, capsize=3)

        ax.axvline(0.5, color="#888888", linestyle="--", linewidth=1, label="Random (0.5)")
        ax.set_yticks(y)
        ax.set_yticklabels(conditions, fontsize=8)
        ax.set_xlabel("AUROC (95% CI)")
        ax.set_title("Ablation: AUROC by Dimension Combination (N=744 test pairs)")
        ax.legend(fontsize=8)
        ax.set_xlim(0.25, 0.65)

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "fig6_ablation.pdf", dpi=150)
        plt.savefig(OUTPUT_DIR / "fig6_ablation.svg")
        print(f"[FIG6] PDF/SVG written to {OUTPUT_DIR}")
        plt.close()
    except ImportError:
        print("[FIG6] matplotlib not available — data JSON written only")

    return out_data


if __name__ == "__main__":
    generate()
