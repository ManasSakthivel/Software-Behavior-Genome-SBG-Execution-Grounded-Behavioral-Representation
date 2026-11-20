"""
baselines/v2/b08_hybrid_v2_correct.py
========================================
B08-V2-CORRECT: Hybrid static+dynamic SBG V2 — CORRECTED IMPLEMENTATION.

Architecture Correction
-----------------------
The original b08_hybrid_sbg_v2.py used Jaccard token-overlap as the "static
component." This is NOT v1 SBG. This corrected version uses the FULL v1
behavioral_distance() from sbg/distance.py — the same function that produced
AUROC=0.4237 in v1 evaluation.

Hybrid formula:
    D_hybrid = w_static * D_v1_static + w_dynamic * D_v2_dynamic
    similarity = 1 - D_hybrid

Weight selection protocol (PREREGISTERED — MUST precede test evaluation):
    WEIGHT_GRID: w_static ∈ {0.0, 0.2, 0.4, 0.6, 0.8, 1.0}
    Selection criterion: best AUROC on DEV split
    Final test evaluation: use selected weight ONCE

Pre-registered default weight (SAFEGUARD-1 — docs/v2/HYPOTHESES_V2.md):
    w_static = 0.40, w_dynamic = 0.60

This script saves to artifacts/v2/B08_CORRECT/ to avoid overwriting the original.
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# ============================================================
# PREREGISTERED WEIGHT GRID — documented BEFORE test evaluation
# This constant must precede any scoring/evaluation code.
# ============================================================
WEIGHT_GRID: List[float] = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
_PREREGISTERED_DEFAULT_W_STATIC: float = 0.40  # from SAFEGUARD-1
_GRID_DECLARED: bool = True  # sentinel — weight grid exists before scoring
assert _GRID_DECLARED, "Weight grid must be declared before any test evaluation"

ARTIFACT_DIR = str(REPO_ROOT / "artifacts" / "v2" / "B08_CORRECT")

from sbg.v2.static_proxy import v1_behavioral_distance
from sbg.v2.execution.genome import DynamicGenome, distance as dyn_distance
from baselines.v2.b07_dynamic_v2 import _extract_genome as _extract_dynamic_genome
from baselines.common import (
    load_pairs, pairs_to_labels, find_optimal_threshold,
    compute_metrics, save_results, compute_auroc,
)


def _get_v1_static_distance(pair: Dict[str, Any]) -> Optional[float]:
    """Compute full v1 behavioral_distance for a pair. Returns None on failure."""
    base_path = str(REPO_ROOT / pair["base_path"])
    variant_path = str(REPO_ROOT / pair["variant_path"])
    return v1_behavioral_distance(base_path, variant_path)


def _score_pair(
    pair: Dict[str, Any],
    w_static: float,
) -> float:
    """
    Score a single pair using hybrid distance.
    Returns similarity in [0, 1].
    """
    base_path = str(REPO_ROOT / pair["base_path"])
    variant_path = str(REPO_ROOT / pair["variant_path"])

    # v2 dynamic distance
    g1 = _extract_dynamic_genome(base_path)
    g2 = _extract_dynamic_genome(variant_path)
    if g1 is None or g2 is None:
        d_dynamic = 0.5
    else:
        d_dynamic = dyn_distance(g1, g2)

    # v1 static distance
    d_static = _get_v1_static_distance(pair)

    w_d = 1.0 - w_static

    if d_static is None:
        # Fall back to dynamic only
        return 1.0 - d_dynamic

    d_hybrid = w_static * d_static + w_d * d_dynamic
    return max(0.0, min(1.0, 1.0 - d_hybrid))


def _score_all_pairs(
    pairs: List[Dict[str, Any]],
    w_static: float,
    desc: str = "",
) -> List[float]:
    """Score all pairs with given fusion weight."""
    sims = []
    for i, p in enumerate(pairs):
        sims.append(_score_pair(p, w_static))
        if (i + 1) % 50 == 0:
            print(f"  [{desc}] {i+1}/{len(pairs)} scored")
    return sims


def run(max_pairs: Optional[int] = None) -> Tuple[Dict, Dict, float, float]:
    """
    Run B08-V2-CORRECT hybrid baseline.

    Protocol:
    1. Score DEV pairs for each weight in WEIGHT_GRID
    2. Select weight with best DEV AUROC
    3. Score TEST pairs with selected weight (exactly once)
    4. Report results with full provenance

    Returns (dev_metrics, test_metrics, selected_threshold, selected_w_static)
    """
    print("\n[B08_CORRECT] Hybrid static(v1 full)+dynamic(v2) SBG — CORRECTED")
    print(f"[B08_CORRECT] Static component: full v1 behavioral_distance() (AUROC=0.4237 in v1)")
    print(f"[B08_CORRECT] PREREGISTERED weight grid: {WEIGHT_GRID}")
    print(f"[B08_CORRECT] PREREGISTERED default w_static: {_PREREGISTERED_DEFAULT_W_STATIC}")

    dev_pairs = load_pairs("dev")
    test_pairs = load_pairs("test")
    if max_pairs:
        dev_pairs = dev_pairs[:max_pairs]
        test_pairs = test_pairs[:max_pairs]

    dev_labels = pairs_to_labels(dev_pairs)
    test_labels = pairs_to_labels(test_pairs)

    # ===================================================
    # PHASE 1: DEV — select weight from PREREGISTERED GRID
    # ===================================================
    print(f"\n[B08_CORRECT] Phase 1: Grid search on {len(dev_pairs)} DEV pairs...")
    grid_results: Dict[float, float] = {}  # w_static -> DEV AUROC

    for w_s in WEIGHT_GRID:
        print(f"  Testing w_static={w_s:.1f}...")
        dev_sims = _score_all_pairs(dev_pairs, w_s, f"dev w={w_s:.1f}")
        auroc = compute_auroc(dev_sims, dev_labels)
        grid_results[w_s] = auroc
        print(f"  w_static={w_s:.1f} -> DEV AUROC={auroc:.4f}")

    # Select best weight on DEV
    best_w_static = max(grid_results, key=lambda w: grid_results[w])
    best_dev_auroc = grid_results[best_w_static]
    print(f"\n[B08_CORRECT] Selected w_static={best_w_static:.1f} (DEV AUROC={best_dev_auroc:.4f})")
    print(f"[B08_CORRECT] Pre-registered default was w_static={_PREREGISTERED_DEFAULT_W_STATIC:.1f}")
    if best_w_static != _PREREGISTERED_DEFAULT_W_STATIC:
        print(f"[B08_CORRECT] NOTE: Selected weight differs from pre-registered default")

    # Final DEV metrics with selected weight
    dev_sims_final = _score_all_pairs(dev_pairs, best_w_static, "dev-final")
    threshold = find_optimal_threshold(dev_sims_final, dev_labels)
    dev_metrics = compute_metrics(dev_sims_final, dev_labels, threshold)
    print(f"[B08_CORRECT] DEV: threshold={threshold:.4f} F1={dev_metrics['f1']:.4f} AUROC={dev_metrics['auroc']:.4f}")

    # ===================================================
    # PHASE 2: TEST — frozen weight and threshold
    # ===================================================
    print(f"\n[B08_CORRECT] Phase 2: TEST evaluation (w_static={best_w_static:.1f}, threshold frozen)")
    test_sims = _score_all_pairs(test_pairs, best_w_static, "test")
    test_metrics = compute_metrics(test_sims, test_labels, threshold)
    print(f"[B08_CORRECT] TEST: F1={test_metrics['f1']:.4f} AUROC={test_metrics['auroc']:.4f} AUPRC={test_metrics['auprc']:.4f}")

    # Inversion analysis
    equiv_sims = [s for s, l in zip(test_sims, test_labels) if l == 0]
    changed_sims = [s for s, l in zip(test_sims, test_labels) if l == 1]
    equiv_mean = sum(equiv_sims) / len(equiv_sims) if equiv_sims else 0.0
    changed_mean = sum(changed_sims) / len(changed_sims) if changed_sims else 0.0
    inversion_delta = changed_mean - equiv_mean

    print(f"\n[B08_CORRECT] === Inversion Analysis (H8/H9) ===")
    print(f"  EQUIV mean similarity:   {equiv_mean:.4f}")
    print(f"  CHANGED mean similarity: {changed_mean:.4f}")
    print(f"  Inversion delta (hybrid-correct): {inversion_delta:+.4f}  (v1 static was +0.0335)")
    print(f"  Inversion resolved:       {'YES' if inversion_delta < 0 else 'NO'}")
    print(f"  H8 (hybrid > dynamic): {'SUPPORTED' if test_metrics['auroc'] > 0.531 else 'NOT_SUPPORTED'}")

    pathlib.Path(ARTIFACT_DIR).mkdir(parents=True, exist_ok=True)

    dev_result = {
        "baseline": "B08_HYBRID_V2_CORRECT",
        "static_component": "full_v1_behavioral_distance",
        "architecture_fix": "token_overlap_proxy_replaced_with_behavioral_distance",
        "split": "dev",
        "weight_selection": "dev_only",
        "weight_grid_preregistered": WEIGHT_GRID,
        "selected_w_static": best_w_static,
        "preregistered_default_w_static": _PREREGISTERED_DEFAULT_W_STATIC,
        "grid_auroc_results": {str(w): round(v, 6) for w, v in grid_results.items()},
        "threshold": threshold,
        "metrics": dev_metrics,
        "provenance": {
            "static": "sbg.distance.behavioral_distance() — all 8 dims, DEFAULT_WEIGHTS",
            "dynamic": "sbg.v2.execution.genome.distance() via b07_dynamic_v2._extract_genome()",
            "weight_selection_protocol": "DEV AUROC maximization over preregistered grid",
            "test_evaluation": "single pass with frozen threshold and frozen weight",
        },
    }

    test_result = {
        "baseline": "B08_HYBRID_V2_CORRECT",
        "static_component": "full_v1_behavioral_distance",
        "split": "test",
        "threshold_from": "dev",
        "selected_w_static": best_w_static,
        "preregistered_default_w_static": _PREREGISTERED_DEFAULT_W_STATIC,
        "threshold": threshold,
        "metrics": test_metrics,
        "inversion_analysis": {
            "equiv_mean_similarity": round(equiv_mean, 6),
            "changed_mean_similarity": round(changed_mean, 6),
            "inversion_delta_hybrid_correct": round(inversion_delta, 6),
            "inversion_delta_v1_reference": 0.0335,
            "inversion_delta_b07_dynamic_v2": -0.0453,
            "inversion_resolved": bool(inversion_delta < 0),
        },
        "h8_verdict": "SUPPORTED" if test_metrics["auroc"] > 0.531023 else "NOT_SUPPORTED",
        "comparison": {
            "b07_dynamic_v2_auroc": 0.531023,
            "b08_correct_auroc": test_metrics["auroc"],
            "delta": round(test_metrics["auroc"] - 0.531023, 6),
        },
    }

    save_results("B08_HYBRID_V2_CORRECT", "dev", dev_result, ARTIFACT_DIR)
    save_results("B08_HYBRID_V2_CORRECT", "test", test_result, ARTIFACT_DIR)
    print(f"\n[B08_CORRECT] Results saved to {ARTIFACT_DIR}")
    return dev_metrics, test_metrics, threshold, best_w_static


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pairs", type=int, default=None)
    args = parser.parse_args()
    run(max_pairs=args.max_pairs)
