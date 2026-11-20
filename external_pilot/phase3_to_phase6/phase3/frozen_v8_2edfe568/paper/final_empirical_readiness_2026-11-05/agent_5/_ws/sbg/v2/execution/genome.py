"""
sbg.v2.execution.genome
========================
DynamicGenome and DynamicGenomeExtractor for SBG v2.

The DynamicGenome is built from NormalizedBehavior and provides a distance
function for use in hybrid genome fusion.

Formal grounding
----------------
DynamicGenome ↔ g_D (v2 behavioral genome, execution-derived dimensions)
distance       ↔ d_D(g1, g2)  in [0, 1]

SAFEGUARD-2: All fields are Output-free. Feature classification documented
in docs/v2/FEATURE_ORACLE.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sbg.v2.execution.normalizer import NormalizedBehavior


@dataclass
class DynamicGenome:
    """
    V2 dynamic behavioral genome.

    All features are Output-free (SAFEGUARD-2).
    All features are rename-invariant (anonymous function indices).
    All features are line-number-invariant (coverage ratios, not line sets).

    Fields
    ------
    program_id : str
    coverage_size : int
        Total unique lines covered across all inputs and runs.
    coverage_consistency : float
        Mean pairwise Jaccard of per-input coverage sets. Range [0,1].
        1.0 = same lines always taken. 0.0 = completely different paths per input.
    anon_call_freq : Dict[int, float]
        Normalized call frequency per anonymous function index (first-call order).
        Keyed by integer, NOT by function name — rename-invariant.
    hot_path_hash : str
        16-hex SHA-256 of top-5 anonymous function indices by frequency.
    exception_type_set : List[str]
        Sorted unique exception class names. No messages (SAFEGUARD-2).
    exception_rate : float
        Fraction of traces with any exception. Range [0,1].
    call_depth_mean : float
        Mean max call depth across traces.
    call_depth_max : float
        Maximum call depth observed.
    trace_length_mean : float
        Mean event count per trace.
    trace_length_std : float
        Std of event count per trace.
    n_unique_functions : int
        Count of unique functions called (structural complexity).
    provenance : Dict
        Metadata: program_id, extraction info, SAFEGUARD-2 compliance.
    """
    program_id: str
    coverage_size: int
    coverage_consistency: float
    anon_call_freq: Dict[int, float]
    hot_path_hash: str
    exception_type_set: List[str]
    exception_rate: float
    call_depth_mean: float
    call_depth_max: float
    trace_length_mean: float
    trace_length_std: float
    n_unique_functions: int
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for storage/comparison. Return value NOT included (SAFEGUARD-2)."""
        return {
            "program_id": self.program_id,
            "coverage_size": self.coverage_size,
            "coverage_consistency": self.coverage_consistency,
            "anon_call_freq": {str(k): v for k, v in self.anon_call_freq.items()},
            "hot_path_hash": self.hot_path_hash,
            "exception_type_set": self.exception_type_set,
            "exception_rate": self.exception_rate,
            "call_depth_mean": self.call_depth_mean,
            "call_depth_max": self.call_depth_max,
            "trace_length_mean": self.trace_length_mean,
            "trace_length_std": self.trace_length_std,
            "n_unique_functions": self.n_unique_functions,
            "feature_classification": "OUTPUT_FREE",
            "safeguard_2_compliant": True,
        }


class DynamicGenomeExtractor:
    """
    Φ_D: NormalizedBehavior → DynamicGenome.
    """

    def extract(self, nb: NormalizedBehavior) -> DynamicGenome:
        """
        Extract DynamicGenome from NormalizedBehavior.

        Parameters
        ----------
        nb : NormalizedBehavior

        Returns
        -------
        DynamicGenome
        """
        return DynamicGenome(
            program_id=nb.program_id,
            coverage_size=nb.coverage_vector_size,
            coverage_consistency=nb.coverage_consistency,
            anon_call_freq=dict(nb.anon_call_freq),
            hot_path_hash=nb.hot_path_hash,
            exception_type_set=list(nb.exception_type_set),
            exception_rate=nb.exception_rate,
            call_depth_mean=nb.call_depth_stats.get("mean", 0.0),
            call_depth_max=nb.call_depth_stats.get("max", 0.0),
            trace_length_mean=nb.trace_length_stats.get("mean", 0.0),
            trace_length_std=nb.trace_length_stats.get("std", 0.0),
            n_unique_functions=nb.n_unique_functions,
            provenance=dict(nb.provenance),
        )


# ---------------------------------------------------------------------------
# distance function
# ---------------------------------------------------------------------------

def distance(g1: DynamicGenome, g2: DynamicGenome) -> float:
    """
    Pseudometric on DynamicGenome in [0, 1].

    Formula (5-component weighted average):

    d = 0.30 * d_coverage
      + 0.30 * d_call_freq
      + 0.15 * d_exception
      + 0.15 * d_depth
      + 0.10 * d_consistency

    Components
    ----------
    d_coverage   : |coverage_size_1 - coverage_size_2| / max(1, max(sizes))
    d_call_freq  : L1(anon_call_freq_1, anon_call_freq_2) / 2  (L1 in [0,2] → scale to [0,1])
    d_exception  : 0.5 * Jaccard_dist(exc_types) + 0.5 * |exc_rate_1 - exc_rate_2|
    d_depth      : |depth_mean_1 - depth_mean_2| / max(1, max(depths))
    d_consistency: |consistency_1 - consistency_2|

    Properties
    ----------
    * d(g, g) = 0.0  for any g
    * d(g1, g2) = d(g2, g1)  (symmetric)
    * result in [0, 1]
    """
    W1, W2, W3, W4, W5 = 0.30, 0.30, 0.15, 0.15, 0.10

    # d_coverage
    max_cov = max(g1.coverage_size, g2.coverage_size, 1)
    d_coverage = abs(g1.coverage_size - g2.coverage_size) / max_cov

    # d_call_freq: L1 on normalized histograms
    all_funcs = set(g1.anon_call_freq) | set(g2.anon_call_freq)
    if not all_funcs:
        d_call_freq = 0.0
    else:
        l1 = sum(
            abs(g1.anon_call_freq.get(f, 0.0) - g2.anon_call_freq.get(f, 0.0))
            for f in all_funcs
        )
        d_call_freq = min(1.0, l1 / 2.0)

    # d_exception: Jaccard on type sets + rate difference
    s1, s2 = set(g1.exception_type_set), set(g2.exception_type_set)
    union_exc = len(s1 | s2)
    if union_exc == 0:
        jaccard_exc = 0.0
    else:
        jaccard_exc = 1.0 - len(s1 & s2) / union_exc
    rate_diff = abs(g1.exception_rate - g2.exception_rate)
    d_exception = 0.5 * jaccard_exc + 0.5 * rate_diff

    # d_depth
    max_depth = max(g1.call_depth_mean, g2.call_depth_mean, 1.0)
    d_depth = abs(g1.call_depth_mean - g2.call_depth_mean) / max_depth

    # d_consistency
    d_consistency = abs(g1.coverage_consistency - g2.coverage_consistency)

    total = (W1 * d_coverage + W2 * d_call_freq + W3 * d_exception +
             W4 * d_depth + W5 * d_consistency)
    return max(0.0, min(1.0, total))
