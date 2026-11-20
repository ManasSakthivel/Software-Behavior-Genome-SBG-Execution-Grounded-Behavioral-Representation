"""
baselines/v2/b08_hybrid_sbg_v2.py
====================================
Baseline B08-v2: Hybrid static+dynamic SBG V2.

Combines v1 static SBG similarity with v2 dynamic genome distance.
Pre-registered fusion weights: static=0.40, dynamic=0.60 (SAFEGUARD-1).

Tests: H8 (hybrid > dynamic-only), H9 (inversion reduced), H12 (regression detection).

Protocol
--------
1. Compute v1 static similarity via token-overlap proxy (or load if precomputed)
2. Compute v2 dynamic distance via DynamicGenome
3. Fuse: hybrid_sim = 1 - (0.40 * static_dist + 0.60 * dynamic_dist)
4. Score DEV → select threshold → evaluate TEST (never tune on test)
"""
from __future__ import annotations

import pathlib
import sys
from typing import Any, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sbg.v2.execution.genome import DynamicGenome
from sbg.v2.hybrid.fusion import hybrid_distance as _hybrid_dist, DEFAULT_FUSION_WEIGHTS, hybrid_similarity
from baselines.v2.b07_dynamic_v2 import (
    _extract_genome, V2_CANONICAL_INPUTS, _runner, _normalizer, _extractor
)
from baselines.common import (
    load_pairs, pairs_to_labels, find_optimal_threshold,
    compute_metrics, save_results, load_source,
)

ARTIFACT_DIR = str(REPO_ROOT / "artifacts" / "v2" / "B08")

# Pre-registered weights (SAFEGUARD-1 — specified before any experiments)
FUSION_WEIGHTS = DEFAULT_FUSION_WEIGHTS  # {"static": 0.40, "dynamic": 0.60}


def _get_static_similarity(pair: dict) -> Optional[float]:
    """
    Get v1 static SBG similarity for a pair.
    Uses token overlap as a proxy (available without running full v1 pipeline).
    Full v1 behavioral_distance would be more accurate but is expensive.
    """
    # Check for pre-computed field in pair dict
    if "sbg_static_similarity" in pair:
        return float(pair["sbg_static_similarity"])

    # Proxy: token-level Jaccard similarity (fast approximation)
    try:
        base_src = load_source(pair["base_path"])
        var_src = load_source(pair["variant_path"])
        base_tokens = set(base_src.split())
        var_tokens = set(var_src.split())
        union = len(base_tokens | var_tokens)
        if union == 0:
            return 0.5
        return len(base_tokens & var_tokens) / union
    except Exception:
        return None


def _score_hybrid_pair(
    base_path: str,
    variant_path: str,
    static_sim: Optional[float],
) -> float:
    """Score a pair using hybrid similarity."""
    g1 = _extract_genome(base_path)
    g2 = _extract_genome(variant_path)

    if g1 is None or g2 is None:
        # Fall back to static similarity only
        return static_sim if static_sim is not None else 0.5

    return hybrid_similarity(g1, g2, static_sim=static_sim, weights=FUSION_WEIGHTS)


def run(max_pairs: Optional[int] = None) -> tuple:
    """Run B08 hybrid baseline."""
    print("\n[B08_HYBRID_V2] Hybrid static+dynamic SBG v2 baseline")
    print(f"[B08_HYBRID_V2] Fusion weights: {FUSION_WEIGHTS} (pre-registered)")

    dev_pairs = load_pairs("dev")
    test_pairs = load_pairs("test")
    if max_pairs:
        dev_pairs = dev_pairs[:max_pairs]
        test_pairs = test_pairs[:max_pairs]

    # DEV pass
    print(f"\n[B08_HYBRID_V2] Scoring {len(dev_pairs)} DEV pairs...")
    dev_labels = pairs_to_labels(dev_pairs)
    dev_sims = []
    for i, p in enumerate(dev_pairs):
        base = str(REPO_ROOT / p["base_path"])
        var = str(REPO_ROOT / p["variant_path"])
        static_sim = _get_static_similarity(p)
        sim = _score_hybrid_pair(base, var, static_sim)
        dev_sims.append(sim)
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(dev_pairs)}")

    threshold = find_optimal_threshold(dev_sims, dev_labels)
    dev_metrics = compute_metrics(dev_sims, dev_labels, threshold)
    print(f"[B08_HYBRID_V2] DEV threshold={threshold:.4f} F1={dev_metrics['f1']:.4f} AUROC={dev_metrics['auroc']:.4f}")

    # TEST pass — frozen threshold
    print(f"\n[B08_HYBRID_V2] Scoring {len(test_pairs)} TEST pairs...")
    test_labels = pairs_to_labels(test_pairs)
    test_sims = []
    for i, p in enumerate(test_pairs):
        base = str(REPO_ROOT / p["base_path"])
        var = str(REPO_ROOT / p["variant_path"])
        static_sim = _get_static_similarity(p)
        sim = _score_hybrid_pair(base, var, static_sim)
        test_sims.append(sim)
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(test_pairs)}")

    test_metrics = compute_metrics(test_sims, test_labels, threshold)
    print(f"[B08_HYBRID_V2] TEST F1={test_metrics['f1']:.4f} AUROC={test_metrics['auroc']:.4f}")

    # Inversion analysis
    equiv_sims = [s for s, l in zip(test_sims, test_labels) if l == 0]
    changed_sims = [s for s, l in zip(test_sims, test_labels) if l == 1]
    equiv_mean = sum(equiv_sims) / len(equiv_sims) if equiv_sims else 0.0
    changed_mean = sum(changed_sims) / len(changed_sims) if changed_sims else 0.0
    inversion_delta = changed_mean - equiv_mean

    print(f"\n[B08_HYBRID_V2] === Inversion Analysis (H9) ===")
    print(f"  EQUIV mean similarity:   {equiv_mean:.4f}")
    print(f"  CHANGED mean similarity: {changed_mean:.4f}")
    print(f"  Inversion delta (hybrid): {inversion_delta:+.4f}  (v1 static was +0.0335)")
    print(f"  Inversion resolved:       {'YES' if inversion_delta < 0 else 'NO'}")

    pathlib.Path(ARTIFACT_DIR).mkdir(parents=True, exist_ok=True)

    dev_result = {
        "baseline": "B08_HYBRID_SBG_V2",
        "split": "dev",
        "fusion_weights": FUSION_WEIGHTS,
        "threshold": threshold,
        "metrics": dev_metrics,
    }
    test_result = {
        "baseline": "B08_HYBRID_SBG_V2",
        "split": "test",
        "threshold_from": "dev",
        "fusion_weights": FUSION_WEIGHTS,
        "threshold": threshold,
        "metrics": test_metrics,
        "inversion_analysis": {
            "equiv_mean_similarity": round(equiv_mean, 6),
            "changed_mean_similarity": round(changed_mean, 6),
            "inversion_delta_v2_hybrid": round(inversion_delta, 6),
            "inversion_delta_v1_reference": 0.0335,
            "inversion_resolved": bool(inversion_delta < 0),
        },
    }

    save_results("B08_HYBRID_SBG_V2", "dev", dev_result, ARTIFACT_DIR)
    save_results("B08_HYBRID_SBG_V2", "test", test_result, ARTIFACT_DIR)
    print(f"\n[B08_HYBRID_V2] Results saved to {ARTIFACT_DIR}")
    return dev_metrics, test_metrics, threshold


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pairs", type=int, default=None)
    args = parser.parse_args()
    run(max_pairs=args.max_pairs)
