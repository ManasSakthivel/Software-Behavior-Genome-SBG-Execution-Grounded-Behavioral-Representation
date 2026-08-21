"""
sbg.extraction.dynamic.resource_genome
========================================
Resource Genome extraction from execution traces.

Formal grounding
----------------
* ResourceGenome  ↔  g_R              (Definition 12, FORMAL_MODEL.md)
* extract         ↔  Φ_R              (Definition 7)
* distance        ↔  d_R              (Definition 17)
* canonicalize    ↔  𝒩_dist / 𝒞_ε   (Definition 22b)

Constraints
-----------
* No third-party imports.
* All analysis is derived from ExecutionTrace objects produced by Tracer.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from sbg.extraction.dynamic.tracer import ExecutionTrace


# ---------------------------------------------------------------------------
# ResourceGenome  (g_R — Definition 12)
# ---------------------------------------------------------------------------

@dataclass
class ResourceGenome:
    """
    Aggregated RESOURCE-dimension genome — g_R per Definition 12.

    Fields
    ------
    execution_time_ms_stats:
        Descriptive statistics {"mean", "std", "min", "max"} of per-trace
        wall-clock execution times in milliseconds.  Proxy for IC̄.
    trace_length_stats:
        Descriptive statistics {"mean", "std", "min", "max"} of per-trace
        event counts (|τ| — instruction-count proxy per Definition 12).
    function_call_total:
        Total number of "call" events across all traces.
    exception_rate:
        Fraction of traces that raised an exception.
    avg_local_var_count:
        Average number of distinct local variable names per trace event
        (memory-use proxy for MEM_peak per Definition 12).
    provenance:
        Metadata dictionary.
    """

    execution_time_ms_stats: Dict[str, float]
    trace_length_stats: Dict[str, float]
    function_call_total: int
    exception_rate: float
    avg_local_var_count: float
    provenance: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# _stats helper
# ---------------------------------------------------------------------------

def _stats(values: List[float]) -> Dict[str, float]:
    """Return mean, std, min, max for a non-empty list."""
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    return {
        "mean": mean,
        "std": math.sqrt(variance),
        "min": min(values),
        "max": max(values),
    }


# ---------------------------------------------------------------------------
# ResourceGenomeExtractor
# ---------------------------------------------------------------------------

class ResourceGenomeExtractor:
    """
    Implements Φ_R: List[ExecutionTrace] → ResourceGenome.

    Aggregation follows Definition 21 (frequency-weighted statistics).
    """

    def extract(self, traces: List[ExecutionTrace]) -> ResourceGenome:
        _empty: Dict[str, float] = {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
        if not traces:
            return ResourceGenome(
                execution_time_ms_stats=dict(_empty),
                trace_length_stats=dict(_empty),
                function_call_total=0,
                exception_rate=0.0,
                avg_local_var_count=0.0,
                provenance={"n_traces": 0},
            )

        n = len(traces)

        # Execution time stats
        time_stats = _stats([t.execution_time_ms for t in traces])

        # Trace length stats
        length_stats = _stats([float(len(t.events)) for t in traces])

        # Function call total
        call_total = sum(
            1 for t in traces for ev in t.events if ev.event_type == "call"
        )

        # Exception rate
        exception_rate = sum(1 for t in traces if t.exception is not None) / n

        # Average local var count per event
        all_var_counts: List[float] = [
            float(len(ev.local_vars_snapshot))
            for t in traces
            for ev in t.events
        ]
        avg_local_var_count = (
            sum(all_var_counts) / len(all_var_counts) if all_var_counts else 0.0
        )

        program_ids = list({t.program_id for t in traces})
        provenance: Dict[str, Any] = {
            "program_ids": program_ids,
            "n_traces": n,
            "extraction_timestamp": time.time(),
        }

        return ResourceGenome(
            execution_time_ms_stats=time_stats,
            trace_length_stats=length_stats,
            function_call_total=call_total,
            exception_rate=exception_rate,
            avg_local_var_count=avg_local_var_count,
            provenance=provenance,
        )


# ---------------------------------------------------------------------------
# distance  (Definition 17, row R)
# ---------------------------------------------------------------------------

def distance(g1: ResourceGenome, g2: ResourceGenome) -> float:
    """
    Pseudometric on ResourceGenome in [0, 1].

    d = 0.5 * normalised_L2(execution_time_ms_stats)
      + 0.5 * |exception_rate_1 - exception_rate_2|
    """
    keys = ("mean", "std", "min", "max")
    sq_sum = 0.0
    for k in keys:
        v1 = g1.execution_time_ms_stats.get(k, 0.0)
        v2 = g2.execution_time_ms_stats.get(k, 0.0)
        denom = max(abs(v1), abs(v2), 1e-12)
        sq_sum += ((v1 - v2) / denom) ** 2
    # sqrt(sq_sum) in [0, 2] for 4 components → scale to [0, 1]
    time_dist = min(math.sqrt(sq_sum) / 2.0, 1.0)
    exc_dist = abs(g1.exception_rate - g2.exception_rate)
    return 0.5 * time_dist + 0.5 * exc_dist


# ---------------------------------------------------------------------------
# canonicalize  (Definition 22b)
# ---------------------------------------------------------------------------

def canonicalize(g: ResourceGenome) -> ResourceGenome:
    """
    Return a canonical form of *g* (idempotent).

    * All stats values clamped to ≥ 0.
    * exception_rate clamped to [0, 1].
    * function_call_total clamped to ≥ 0.
    * avg_local_var_count clamped to ≥ 0.
    * provenance gains a ``canonicalized`` marker.
    """
    def _clean(d: Dict[str, float]) -> Dict[str, float]:
        return {k: max(0.0, float(v)) for k, v in d.items()}

    prov = dict(g.provenance)
    prov["canonicalized"] = True

    return ResourceGenome(
        execution_time_ms_stats=_clean(g.execution_time_ms_stats),
        trace_length_stats=_clean(g.trace_length_stats),
        function_call_total=max(0, int(g.function_call_total)),
        exception_rate=max(0.0, min(1.0, float(g.exception_rate))),
        avg_local_var_count=max(0.0, float(g.avg_local_var_count)),
        provenance=prov,
    )
