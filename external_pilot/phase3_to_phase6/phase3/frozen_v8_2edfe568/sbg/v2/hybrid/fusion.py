"""
sbg.v2.hybrid.fusion
=====================
HybridGenome: fuses v1 static SBG genome with v2 dynamic genome into a
single unified behavioral representation.

Design
------
The fusion operates on pair-level distances, not on raw genome objects:
  D_hybrid(P1, P2) = w_static * D_static(P1, P2) + w_dynamic * D_dynamic(P1, P2)

where:
  D_static  = behavioral_distance from v1 sbg.distance (8 static dimensions)
  D_dynamic = distance() from sbg.v2.execution.genome

Pre-registered weights (SAFEGUARD-1, docs/v2/HYPOTHESES_V2.md):
  w_static  = 0.40
  w_dynamic = 0.60

Weight search on DEV split is allowed for ablation experiments,
but final test evaluation always uses pre-registered weights.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from sbg.v2.execution.genome import DynamicGenome

# Pre-registered default weights
DEFAULT_FUSION_WEIGHTS: Dict[str, float] = {"static": 0.40, "dynamic": 0.60}


@dataclass
class HybridGenome:
    """
    Container for combined static + dynamic information about a single program.

    Fields
    ------
    program_id : str
    dynamic_genome : DynamicGenome
        V2 dynamic genome (output-free).
    static_distance_precomputed : Optional[float]
        Pre-computed v1 static SBG distance for the pair this program belongs to.
        Set at evaluation time (not extraction time).
    fusion_weights : Dict[str, float]
        {"static": w_s, "dynamic": w_d}, auto-normalized to sum 1.0.
    provenance : Dict
    """
    program_id: str
    dynamic_genome: DynamicGenome
    static_distance_precomputed: Optional[float] = None
    fusion_weights: Dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_FUSION_WEIGHTS)
    )
    provenance: Dict[str, Any] = field(default_factory=dict)


def hybrid_distance(
    dg1: DynamicGenome,
    dg2: DynamicGenome,
    static_dist: Optional[float] = None,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Compute hybrid behavioral distance in [0, 1].

    Parameters
    ----------
    dg1, dg2 : DynamicGenome
        V2 dynamic genomes for the two programs being compared.
    static_dist : float, optional
        Pre-computed v1 static SBG distance (pair-level) in [0, 1].
        If None, only dynamic distance is used.
    weights : dict, optional
        {"static": w_s, "dynamic": w_d}.
        If static_dist is None, static weight is redistributed to dynamic.

    Returns
    -------
    float in [0, 1]

    Properties
    ----------
    * hybrid_distance(g, g, 0.0) = 0.0  (identity)
    * Symmetric: hybrid_distance(g1, g2) = hybrid_distance(g2, g1)
    """
    from sbg.v2.execution.genome import distance as d_dyn

    if weights is None:
        weights = DEFAULT_FUSION_WEIGHTS

    # Re-normalize
    total_w = sum(weights.values())
    if total_w <= 0:
        total_w = 1.0
    w_s = weights.get("static", 0.40) / total_w
    w_d = weights.get("dynamic", 0.60) / total_w

    d_dynamic = d_dyn(dg1, dg2)

    if static_dist is None:
        # Fall back to dynamic only
        return max(0.0, min(1.0, d_dynamic))

    result = w_s * float(static_dist) + w_d * d_dynamic
    return max(0.0, min(1.0, result))


def hybrid_similarity(
    dg1: DynamicGenome,
    dg2: DynamicGenome,
    static_sim: Optional[float] = None,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Convenience: returns 1 - hybrid_distance.
    static_sim should be a SIMILARITY score in [0, 1] (1 - static_distance).
    """
    static_dist = (1.0 - static_sim) if static_sim is not None else None
    return 1.0 - hybrid_distance(dg1, dg2, static_dist, weights)
