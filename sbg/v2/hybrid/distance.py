"""
sbg.v2.hybrid.distance
=======================
Hybrid distance and alpha-sweep utilities for v2 genome evaluation.

hybrid_distance() — the primary v2 pair-level distance function.
sweep_alpha()     — scans fusion weights on dev split for ablation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sbg.v2.execution.genome import DynamicGenome, distance as d_dyn
from sbg.v2.hybrid.fusion import hybrid_distance as _hybrid_distance
from sbg.v2.hybrid.fusion import DEFAULT_FUSION_WEIGHTS


def hybrid_distance(
    dg1: DynamicGenome,
    dg2: DynamicGenome,
    static_dist: Optional[float] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compute hybrid behavioral distance with full provenance.

    Parameters
    ----------
    dg1, dg2 : DynamicGenome
    static_dist : float, optional
    weights : dict, optional

    Returns
    -------
    dict:
        hybrid_distance : float in [0, 1]
        dynamic_distance : float
        static_distance : Optional[float]
        weights_used : dict
    """
    if weights is None:
        weights = DEFAULT_FUSION_WEIGHTS

    total_w = sum(weights.values()) or 1.0
    w_s = weights.get("static", 0.40) / total_w
    w_d = weights.get("dynamic", 0.60) / total_w

    d_dynamic = d_dyn(dg1, dg2)
    d_hyb = _hybrid_distance(dg1, dg2, static_dist, weights)

    return {
        "hybrid_distance": d_hyb,
        "dynamic_distance": d_dynamic,
        "static_distance": static_dist,
        "weights_used": {"static": round(w_s, 4), "dynamic": round(w_d, 4)},
    }


def sweep_alpha(
    static_dists: List[float],
    dynamic_dists: List[float],
    labels: List[int],
    alphas: Optional[List[float]] = None,
) -> Dict[float, float]:
    """
    Sweep fusion weight alpha on a data split and return AUROC per alpha.

    Parameters
    ----------
    static_dists : list of float  — per-pair static distance
    dynamic_dists : list of float — per-pair dynamic distance
    labels : list of int          — 0=EQUIVALENT, 1=CHANGED
    alphas : list of float, optional
        Values to sweep. Default: [0.0, 0.1, ..., 1.0]

    Returns
    -------
    dict mapping alpha -> AUROC
    """
    from baselines.common import compute_auroc

    if alphas is None:
        alphas = [round(a * 0.1, 1) for a in range(11)]

    results: Dict[float, float] = {}
    for alpha in alphas:
        combined_sims = [
            1.0 - (alpha * d_s + (1.0 - alpha) * d_d)
            for d_s, d_d in zip(static_dists, dynamic_dists)
        ]
        results[alpha] = round(compute_auroc(combined_sims, labels), 6)
    return results
