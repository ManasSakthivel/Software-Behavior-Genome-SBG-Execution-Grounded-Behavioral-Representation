"""
experiments/v2/figures/fig2_inversion.py
==========================================
Figure 2: Structural-Semantic Inversion — Before and After Execution Grounding.

Data source: artifacts/v2/FIGURE_DATA.json (FIGURE_2)
Reads ONLY from frozen artifact files. No hardcoded numbers.
"""
from __future__ import annotations
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
DATA_FILE = REPO_ROOT / "artifacts" / "v2" / "FIGURE_DATA.json"
OUTPUT_DIR = REPO_ROOT / "artifacts" / "v2" / "figures"


def generate():
    data = json.loads(DATA_FILE.read_text())
    fig_data = data["figures"]["FIGURE_2"]["data"]

    methods = fig_data["methods"]
    equiv_mean = fig_data["equiv_mean"]
    changed_mean = fig_data["changed_mean"]
    deltas = fig_data["inversion_delta"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Always write frozen data JSON
    out_data = {
        "figure": "FIGURE_2",
        "title": data["figures"]["FIGURE_2"]["title"],
        "methods": methods,
        "equiv_mean": equiv_mean,
        "changed_mean": changed_mean,
        "inversion_delta": deltas,
        "source": "artifacts/v2/FIGURE_DATA.json",
        "status": "FROZEN",
    }
    out_path = OUTPUT_DIR / "fig2_inversion_data.json"
    out_path.write_text(json.dumps(out_data, indent=2))
    print(f"[FIG2] Data written to {out_path}")

    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use("Agg")

        fig, ax = plt.subplots(figsize=(8, 5))
        x = range(len(methods))
        width = 0.35

        bars1 = ax.bar([xi - width/2 for xi in x], equiv_mean, width,
                       label="EQUIV (Semantics-Preserving)", color="#3b82d4", alpha=0.85)
        bars2 = ax.bar([xi + width/2 for xi in x], changed_mean, width,
                       label="CHANGED (Semantics-Changing)", color="#e05c5c", alpha=0.85)

        ax.set_xlabel("Method")
        ax.set_ylabel("Mean Similarity Score")
        ax.set_title("Structural-Semantic Inversion: Before and After Execution Grounding")
        ax.set_xticks(list(x))
        ax.set_xticklabels(methods, rotation=10)
        ax.legend()
        ax.set_ylim(0.7, 1.05)

        # Annotate inversion deltas
        for i, (xi, delta) in enumerate(zip(x, deltas)):
            color = "#22a022" if delta < 0 else "#cc0000"
            ax.annotate(f"Δ={delta:+.3f}",
                       xy=(xi, max(equiv_mean[i], changed_mean[i]) + 0.01),
                       ha="center", fontsize=8, color=color, fontweight="bold")

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "fig2_inversion.pdf", dpi=150)
        plt.savefig(OUTPUT_DIR / "fig2_inversion.svg")
        print(f"[FIG2] PDF/SVG written to {OUTPUT_DIR}")
        plt.close()
    except ImportError:
        print("[FIG2] matplotlib not available — data JSON written only")

    return out_data


if __name__ == "__main__":
    generate()
