"""
experiments/phase4/e6_baseline_comparison.py
=============================================
E6: SBG vs All Baselines — Comprehensive Comparison.

Loads all 8 Phase 3 baseline results and produces a ranked comparison table
with pairwise effect sizes and McNemar statistical tests for the primary
comparison (B08 vs B02).

For McNemar: re-scores test pairs with both methods to get per-pair predictions,
then computes the 2x2 contingency table.

Hypothesis addressed: H2 (SBG outperforms baselines)
"""
import json
import math
import pathlib
import random
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from experiments.phase4.utils import ensure_token_initialized

from baselines.common import (
    load_pairs, load_source, compute_auroc, compute_metrics,
    find_optimal_threshold, pairs_to_labels
)
from baselines.b08_full_sbg import score_fn as sbg_full_fn
from baselines.b02_ast import score_fn as ast_fn
from baselines.b07_static_sbg import score_fn as static_sbg_fn
from baselines.b01_token import score_fn as token_fn

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "phase4" / "E6"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
PHASE3_DIR = REPO_ROOT / "artifacts" / "phase3"

SEED = 42
ALPHA_CORRECTED = 0.0017  # Bonferroni over H1-H6


def load_phase3(baseline: str) -> dict:
    p = PHASE3_DIR / baseline / "results_test.json"
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {}


def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h for two proportions."""
    def phi(p):
        p = max(1e-9, min(1 - 1e-9, p))
        return 2 * math.asin(p ** 0.5)
    return abs(phi(p1) - phi(p2))


def chi2_pvalue_approx(chi2: float, df: int = 1) -> float:
    """
    Approximate p-value for chi-squared test using incomplete gamma function.
    For df=1: P(X > chi2) ≈ erfc(sqrt(chi2/2))
    Uses Horner's method approximation for erfc.
    """
    if chi2 <= 0:
        return 1.0
    # For df=1: chi2 = z^2, so p = 2*(1-Phi(|z|))
    z = chi2 ** 0.5
    # Abramowitz & Stegun approximation for erfc
    t = 1.0 / (1.0 + 0.3275911 * z)
    poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))))
    erfc_approx = poly * math.exp(-z * z)
    return max(0.0, min(1.0, erfc_approx))


def mcnemar_test(preds_a: list, preds_b: list, labels: list) -> dict:
    """
    McNemar's test comparing classifier A vs B on same test set.
    b = A correct, B wrong
    c = A wrong, B correct
    Statistic: (|b - c| - 1)^2 / (b + c) with continuity correction
    """
    b = sum(1 for pa, pb, l in zip(preds_a, preds_b, labels)
            if pa == l and pb != l)
    c = sum(1 for pa, pb, l in zip(preds_a, preds_b, labels)
            if pa != l and pb == l)
    if b + c == 0:
        return {"b": 0, "c": 0, "statistic": 0.0, "p_value": 1.0,
                "significant": False, "note": "b+c=0 — classifiers agree on all disagreements"}
    stat = (abs(b - c) - 1) ** 2 / (b + c)
    p = chi2_pvalue_approx(stat, df=1)
    return {
        "b": b, "c": c,
        "statistic": round(stat, 4),
        "p_value": round(p, 6),
        "significant_at_corrected_alpha": p < ALPHA_CORRECTED,
        "alpha_corrected": ALPHA_CORRECTED,
    }


def run_e6():
    print("=" * 60)
    print("E6: Comprehensive Baseline Comparison")
    print("=" * 60)

    ensure_token_initialized()
    # Load all Phase 3 results
    baselines = ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08"]
    phase3_results = {}
    for b in baselines:
        r = load_phase3(b)
        if r:
            phase3_results[b] = r

    # Build comparison table
    table = []
    for b in baselines:
        r = phase3_results.get(b, {})
        m = r.get("metrics", {})
        table.append({
            "baseline": b,
            "name": r.get("baseline", b),
            "f1": m.get("f1"),
            "auroc": m.get("auroc"),
            "auprc": m.get("auprc"),
            "ci_f1": [m.get("ci_f1_lower"), m.get("ci_f1_upper")],
            "ci_auroc": [m.get("ci_auroc_lower"), m.get("ci_auroc_upper")],
            "threshold": r.get("threshold"),
        })

    # Sort by AUROC descending
    table_sorted = sorted(
        [t for t in table if t["auroc"] is not None],
        key=lambda x: -x["auroc"]
    )

    print("\n  Baseline ranking by AUROC:")
    for rank, entry in enumerate(table_sorted, 1):
        print(f"    {rank}. {entry['baseline']} ({entry['name']}): "
              f"F1={entry['f1']:.4f}  AUROC={entry['auroc']:.4f}  AUPRC={entry['auprc']:.4f}")

    # Primary comparison: B08 (Full SBG) vs B02 (Best baseline = AST)
    # Re-score test pairs to get per-pair predictions for McNemar
    print("\n  Re-scoring test pairs for McNemar test (B08 vs B02)...")
    test_pairs = load_pairs("test")
    dev_pairs = load_pairs("dev")
    test_labels = pairs_to_labels(test_pairs)
    dev_labels = pairs_to_labels(dev_pairs)

    # Get dev thresholds from Phase 3 artifacts
    b02_dev = PHASE3_DIR / "B02" / "results_dev.json"
    b08_dev = PHASE3_DIR / "B08" / "results_dev.json"

    b02_threshold = 0.5
    b08_threshold = 0.5
    if b02_dev.exists():
        with open(b02_dev) as f:
            b02_threshold = json.load(f).get("threshold", 0.5)
    if b08_dev.exists():
        with open(b08_dev) as f:
            b08_threshold = json.load(f).get("threshold", 0.5)

    print(f"  B02 threshold (from dev): {b02_threshold:.4f}")
    print(f"  B08 threshold (from dev): {b08_threshold:.4f}")

    b02_sims, b08_sims = [], []
    for i, p in enumerate(test_pairs):
        if (i + 1) % 100 == 0:
            print(f"    {i+1}/{len(test_pairs)}...")
        src_base = load_source(p["base_path"])
        src_var = load_source(p["variant_path"])
        try:
            b02_sims.append(float(ast_fn(src_base, src_var)))
        except Exception:
            b02_sims.append(0.5)
        try:
            b08_sims.append(float(sbg_full_fn(src_base, src_var)))
        except Exception:
            b08_sims.append(0.5)

    # Per-pair predictions: predict CHANGED (1) if sim < threshold
    b02_preds = [1 if s < b02_threshold else 0 for s in b02_sims]
    b08_preds = [1 if s < b08_threshold else 0 for s in b08_sims]

    mcnemar = mcnemar_test(b02_preds, b08_preds, test_labels)
    print(f"  McNemar B02 vs B08: b={mcnemar['b']}, c={mcnemar['c']}, "
          f"chi2={mcnemar['statistic']:.4f}, p={mcnemar['p_value']:.6f}")

    # Effect sizes: pairwise Cohen's h for F1
    b02_f1 = phase3_results.get("B02", {}).get("metrics", {}).get("f1", 0.0) or 0.0
    b08_f1 = phase3_results.get("B08", {}).get("metrics", {}).get("f1", 0.0) or 0.0
    b02_auroc = phase3_results.get("B02", {}).get("metrics", {}).get("auroc", 0.5) or 0.5
    b08_auroc = phase3_results.get("B08", {}).get("metrics", {}).get("auroc", 0.5) or 0.5

    pairwise_effects = {}
    for b in baselines:
        if b == "B08":
            continue
        r = phase3_results.get(b, {})
        m = r.get("metrics", {})
        other_f1 = m.get("f1") or 0.0
        other_auroc = m.get("auroc") or 0.5
        pairwise_effects[f"B08_vs_{b}"] = {
            "delta_f1": round(b08_f1 - other_f1, 4),
            "delta_auroc": round(b08_auroc - other_auroc, 4),
            "cohens_h_f1": round(cohens_h(b08_f1, other_f1), 4),
            "sbg_wins_f1": b08_f1 > other_f1,
            "sbg_wins_auroc": b08_auroc > other_auroc,
        }

    # H2 verdict
    sbg_best_auroc = b08_auroc
    best_baseline_auroc = max(
        (phase3_results.get(b, {}).get("metrics", {}).get("auroc") or 0.0)
        for b in ["B01", "B02", "B03", "B04", "B05", "B06", "B07"]
    )
    h2_supported = sbg_best_auroc > best_baseline_auroc
    h2_verdict = {
        "status": "SUPPORTED" if h2_supported else "NOT_SUPPORTED",
        "sbg_auroc": round(sbg_best_auroc, 4),
        "best_baseline_auroc": round(best_baseline_auroc, 4),
        "delta_auroc": round(sbg_best_auroc - best_baseline_auroc, 4),
        "mcnemar_significant": mcnemar.get("significant_at_corrected_alpha", False),
        "interpretation": (
            f"Full SBG AUROC={sbg_best_auroc:.4f} vs best baseline AUROC={best_baseline_auroc:.4f}. "
            f"H2 is {'SUPPORTED' if h2_supported else 'NOT SUPPORTED'}. "
            f"McNemar test: p={mcnemar['p_value']:.6f} "
            f"({'significant' if mcnemar.get('significant_at_corrected_alpha') else 'not significant'} "
            f"at α={ALPHA_CORRECTED})."
        ),
    }

    result = {
        "experiment": "E6",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_addressed": ["H2"],
        "n_test_pairs": len(test_pairs),
        "baseline_table_sorted_by_auroc": table_sorted,
        "pairwise_effects_B08_vs_others": pairwise_effects,
        "mcnemar_B08_vs_B02": mcnemar,
        "b02_threshold_used": b02_threshold,
        "b08_threshold_used": b08_threshold,
        "h2_verdict": h2_verdict,
        "finding": h2_verdict["interpretation"],
        "seed": SEED,
    }

    out_path = ARTIFACT_DIR / "results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n=== E6 Summary ===")
    print(f"  H2: {h2_verdict['status']}")
    print(f"  {h2_verdict['interpretation']}")
    print(f"\nResults saved to: {out_path}")
    return result


if __name__ == "__main__":
    run_e6()
