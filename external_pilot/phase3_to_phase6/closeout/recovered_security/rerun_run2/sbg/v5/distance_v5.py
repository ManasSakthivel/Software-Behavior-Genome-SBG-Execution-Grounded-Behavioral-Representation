"""
sbg.v5.distance_v5
==================
Combined V5 distance function.

Formula
-------
distance_v5(g1, g2) = 0.50 * distance_v3(g1.v3,  g2.v3)
                    + 0.25 * temporal_distance(g1.temporal, g2.temporal)
                    + 0.25 * state_distance(g1.state, g2.state)

Graceful degradation: if v5 features are unavailable for a pair, falls back
to the V3 distance only (weight 1.0).

Re-exported convenience wrapper; the concrete per-family distances live in:
  sbg.v3.genome               → distance_v3
  sbg.v5.temporal_genome_v5   → distance (as temporal_distance)
  sbg.v5.state_transition_genome → StateTransitionGenome().distance
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from sbg.v3.genome import DynamicGenomeV3, distance_v3
from sbg.v5.temporal_genome_v5 import TemporalGenomeV5
from sbg.v5.temporal_genome_v5 import distance as temporal_distance
from sbg.v5.state_transition_genome import StateTransitionGraph, StateTransitionGenome

_st_genome = StateTransitionGenome()

V3_WEIGHT       = 0.50
TEMPORAL_WEIGHT = 0.25
STATE_WEIGHT    = 0.25


@dataclass
class V5GenomeBundle:
    """Container holding all genome layers for a single program."""
    program_id: str
    v3: Optional[DynamicGenomeV3]
    temporal: Optional[TemporalGenomeV5]
    state: Optional[StateTransitionGraph]
    v5_available: bool = False


def distance_v5(b1: V5GenomeBundle, b2: V5GenomeBundle) -> float:
    """
    Combined V5 distance in [0, 1].

    Falls back to V3 distance only if V5 extraction failed for either bundle.
    """
    if b1.v3 is None or b2.v3 is None:
        return 0.5  # neutral on extraction failure

    d_v3 = distance_v3(b1.v3, b2.v3)

    if not (b1.v5_available and b2.v5_available):
        return d_v3

    d_temporal = 0.0
    if b1.temporal is not None and b2.temporal is not None:
        try:
            d_temporal = temporal_distance(b1.temporal, b2.temporal)
        except Exception:
            d_temporal = d_v3  # graceful fallback

    d_state = 0.0
    if b1.state is not None and b2.state is not None:
        try:
            d_state = _st_genome.distance(b1.state, b2.state)
        except Exception:
            d_state = d_v3  # graceful fallback

    combined = (
        V3_WEIGHT       * d_v3
        + TEMPORAL_WEIGHT * d_temporal
        + STATE_WEIGHT    * d_state
    )
    return max(0.0, min(1.0, combined))
