"""
sbg.distance
=============
Master behavioral distance computation module for the SBG project.

Provides ``behavioral_distance(genome_a, genome_b)`` — the weighted aggregate
distance across up to 8 genome dimensions — and ``DEFAULT_WEIGHTS``.

Formal grounding
----------------
* behavioral_distance  ↔  D(G₁, G₂)  (Definition 18, FORMAL_MODEL.md)
* DEFAULT_WEIGHTS      ↔  w*          (Definition 20, application-specific)
* Each d_k             ↔  dimension distance (Definition 17)
* Aggregation          ↔  𝒻 with p=1  (Definition 20, weighted average)

Design
------
Each genome module exposes a ``distance`` function that returns a float in
[0, 1].  This module imports all eight distance functions and computes the
weighted sum over whatever dimensions are present in both genome dicts.

Missing dimensions are tracked but do not affect the normalisation: weights
are re-normalised to the present dimensions so the result always lies in
[0, 1].

Usage
-----
    from sbg.distance import behavioral_distance, DEFAULT_WEIGHTS

    result = behavioral_distance(genome_a, genome_b)
    print(result["total_distance"])   # float in [0, 1]
    print(result["dimension_distances"])

Constraints
-----------
* No third-party imports.
* behavioral_distance(g, g) == 0.0 for any genome dict g.
* result["total_distance"] ∈ [0, 1] provided individual d_k ∈ [0, 1].
* sum(DEFAULT_WEIGHTS.values()) == 1.0
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sbg.extraction.static.extractor import distance as d_control
from sbg.extraction.static.data_genome import distance as d_data
from sbg.extraction.static.error_genome import distance as d_error
from sbg.extraction.dynamic.tracer import distance as d_exec
from sbg.extraction.dynamic.state_genome import distance as d_state
from sbg.extraction.dynamic.resource_genome import distance as d_resource
from sbg.extraction.dynamic.temporal_genome import distance as d_temporal
from sbg.extraction.dynamic.interaction_genome import distance as d_interaction


# ---------------------------------------------------------------------------
# DEFAULT_WEIGHTS
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS: Dict[str, float] = {
    "CONTROL":     0.20,
    "DATA":        0.15,
    "STATE":       0.15,
    "RESOURCE":    0.10,
    "TEMPORAL":    0.10,
    "ERROR":       0.10,
    "INTERACTION": 0.10,
    "EXECUTION":   0.10,
}
# sum = 0.20 + 0.15 + 0.15 + 0.10 + 0.10 + 0.10 + 0.10 + 0.10 = 1.00

# ---------------------------------------------------------------------------
# _DISTANCE_FNS — per-dimension distance functions
# ---------------------------------------------------------------------------

_DISTANCE_FNS: Dict[str, Any] = {
    "CONTROL":     d_control,
    "DATA":        d_data,
    "STATE":       d_state,
    "RESOURCE":    d_resource,
    "TEMPORAL":    d_temporal,
    "ERROR":       d_error,
    "INTERACTION": d_interaction,
    "EXECUTION":   d_exec,
}


# ---------------------------------------------------------------------------
# behavioral_distance
# ---------------------------------------------------------------------------

def behavioral_distance(
    genome_a: Dict[str, Any],
    genome_b: Dict[str, Any],
    weights: Dict[str, float] = DEFAULT_WEIGHTS,
    dimensions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Compute the weighted behavioral distance between two genome dicts.

    Parameters
    ----------
    genome_a, genome_b : dict
        Each maps dimension key → genome instance.
        Keys should be a subset of: CONTROL, DATA, STATE, RESOURCE,
        TEMPORAL, ERROR, INTERACTION, EXECUTION.

    weights : dict, optional
        Per-dimension weights.  Must be non-negative; need not sum to 1.0
        (they are re-normalised over the active dimensions).
        Defaults to DEFAULT_WEIGHTS.

    dimensions : list of str, optional
        Restrict computation to these dimension keys.  If None, all keys
        present in *weights* are considered.

    Returns
    -------
    dict with keys:
        ``total_distance``      float in [0, 1] — weighted aggregate.
        ``dimension_distances`` dict[str, float] — per-dimension d_k values.
        ``dimensions_used``     list[str] — dimensions included in the sum.
        ``weights_used``        dict[str, float] — effective (renormalised) weights.
        ``missing_dimensions``  list[str] — dimensions in *weights* but absent
                                from one or both genome dicts.

    Notes
    -----
    * Dimensions absent from either genome_a or genome_b are skipped and
      appear in ``missing_dimensions``.
    * Dimensions without a registered distance function are also skipped.
    * When no shared dimensions are found, ``total_distance`` is 0.0.
    * Result is symmetric: behavioral_distance(a, b) == behavioral_distance(b, a).
    * behavioral_distance(g, g) == 0.0 for any *g* (by property of d_k(x,x)=0).
    """
    candidate_dims: List[str] = list(dimensions) if dimensions is not None else list(weights)

    dimension_distances: Dict[str, float] = {}
    active_dims: List[str] = []
    missing_dims: List[str] = []

    for dim in candidate_dims:
        # Skip dimensions not in the weights map
        if dim not in weights:
            continue

        # Check presence in both genomes
        if dim not in genome_a or dim not in genome_b:
            missing_dims.append(dim)
            continue

        # Check we have a distance function for this dimension
        dist_fn = _DISTANCE_FNS.get(dim)
        if dist_fn is None:
            missing_dims.append(dim)
            continue

        d_val = dist_fn(genome_a[dim], genome_b[dim])
        # Clamp to [0, 1] as a defensive measure (each d_k should already be)
        dimension_distances[dim] = max(0.0, min(1.0, float(d_val)))
        active_dims.append(dim)

    # Re-normalise weights over active dimensions
    raw_weight_sum = sum(weights.get(dim, 0.0) for dim in active_dims)

    if raw_weight_sum <= 0.0 or not active_dims:
        # No active dimensions → distance is 0 (trivially equal)
        return {
            "total_distance": 0.0,
            "dimension_distances": dimension_distances,
            "dimensions_used": active_dims,
            "weights_used": {},
            "missing_dimensions": missing_dims,
        }

    effective_weights: Dict[str, float] = {
        dim: weights[dim] / raw_weight_sum for dim in active_dims
    }

    total = sum(
        effective_weights[dim] * dimension_distances[dim]
        for dim in active_dims
    )
    # Clamp final result to [0, 1] against floating-point noise
    total = max(0.0, min(1.0, total))

    return {
        "total_distance": total,
        "dimension_distances": dimension_distances,
        "dimensions_used": active_dims,
        "weights_used": effective_weights,
        "missing_dimensions": missing_dims,
    }
