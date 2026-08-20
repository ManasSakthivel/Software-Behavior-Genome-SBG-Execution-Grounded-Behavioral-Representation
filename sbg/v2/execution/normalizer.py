"""
sbg.v2.execution.normalizer
============================
TraceNormalizer — converts raw ExecutionTrace objects into NormalizedBehavior:
a rename-invariant, line-number-invariant behavioral signature.

SAFEGUARD-2 enforcement
------------------------
This module is the feature oracle boundary. ALL features produced here are
classified Output-free per FEATURE_ORACLE.md. The normalizer never accesses
trace.return_value or trace.stdout content.

Rename-invariance
-----------------
Functions are anonymized by first-call order (index 0, 1, 2...). Call frequency
histogram is keyed by integer index, not function name. This ensures SP-2
(function rename) produces identical normalized signatures.

Line-number-invariance
----------------------
Absolute line numbers are NOT used in inter-program distance computation.
Coverage is captured as coverage_vector_size (count of unique lines reached)
and coverage_consistency (mean pairwise Jaccard of per-input coverage sets).
This is robust to SP-8 (extract function adds lines) and similar transforms.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from sbg.extraction.dynamic.tracer import ExecutionTrace


@dataclass
class NormalizedBehavior:
    """
    Normalized behavioral signature for a program across all inputs and runs.
    All features are Output-free (SAFEGUARD-2).

    Fields
    ------
    program_id : str
    anon_call_freq : Dict[int, float]
        Normalized call frequency per anonymous function index.
        Index 0 = first function called, 1 = second unique function called, etc.
    coverage_vector_size : int
        Count of unique lines reached (union across all inputs and runs).
    coverage_consistency : float
        Mean pairwise Jaccard similarity of per-input coverage sets.
        1.0 = same lines always reached. 0.0 = no consistent coverage.
    exception_type_set : List[str]
        Sorted list of unique exception class names observed. No messages.
    exception_rate : float
        Fraction of (input, run) traces that raised exceptions.
    call_depth_stats : Dict[str, float]
        {"mean": float, "max": float} of max call depth across traces.
    trace_length_stats : Dict[str, float]
        {"mean": float, "std": float} of event count per trace.
    hot_path_hash : str
        SHA-256 prefix of top-5 anonymous function indices by frequency.
        Rename-invariant: keyed by rank, not name.
    n_unique_functions : int
        Number of distinct functions called (structural complexity).
    provenance : Dict
    """
    program_id: str
    anon_call_freq: Dict[int, float]
    coverage_vector_size: int
    coverage_consistency: float
    exception_type_set: List[str]
    exception_rate: float
    call_depth_stats: Dict[str, float]
    trace_length_stats: Dict[str, float]
    hot_path_hash: str
    n_unique_functions: int
    provenance: Dict = field(default_factory=dict)


class TraceNormalizer:
    """
    Converts raw ExecutionTrace objects into NormalizedBehavior.

    All features are output-free. return_value and stdout are never accessed.
    """

    def normalize(
        self,
        program_id: str,
        all_runs: List[List[ExecutionTrace]],
    ) -> NormalizedBehavior:
        """
        Parameters
        ----------
        program_id : str
        all_runs : List[List[ExecutionTrace]]
            Outer list: runs. Inner list: traces per input.

        Returns
        -------
        NormalizedBehavior
        """
        if not all_runs or not any(all_runs):
            return self._empty(program_id)

        # Flatten all traces
        all_traces: List[ExecutionTrace] = [t for run in all_runs for t in run]

        # Build anonymization map: function_name -> index (first-call order)
        name_to_idx: Dict[str, int] = {}
        for trace in all_traces:
            for ev in trace.events:
                if ev.event_type == "call" and ev.function_name not in name_to_idx:
                    name_to_idx[ev.function_name] = len(name_to_idx)

        # Per-trace features
        per_trace_coverage: List[Set[int]] = []
        call_depths: List[int] = []
        event_counts: List[int] = []
        exception_types: Set[str] = set()
        n_exception_traces = 0
        anon_call_counts: Dict[int, int] = {}

        for trace in all_traces:
            per_trace_coverage.append(set(trace.coverage))
            event_counts.append(len(trace.events))

            # Exception type — class name only (no message — SAFEGUARD-2)
            if trace.exception is not None:
                n_exception_traces += 1
                exc_type = str(trace.exception).split(":")[0].strip()
                exception_types.add(exc_type)

            # Call depth and anonymous call frequency
            depth = 0
            max_depth = 0
            for ev in trace.events:
                if ev.event_type == "call":
                    depth += 1
                    max_depth = max(max_depth, depth)
                    idx = name_to_idx.get(ev.function_name, -1)
                    if idx >= 0:
                        anon_call_counts[idx] = anon_call_counts.get(idx, 0) + 1
                elif ev.event_type == "return":
                    depth = max(0, depth - 1)
            call_depths.append(max_depth)

        # Normalized anonymous call frequencies
        total_calls = sum(anon_call_counts.values()) or 1
        anon_call_freq = {k: v / total_calls for k, v in anon_call_counts.items()}

        # Coverage stats
        coverage_union: Set[int] = set()
        for cov in per_trace_coverage:
            coverage_union.update(cov)
        coverage_vector_size = len(coverage_union)

        # Coverage consistency: mean pairwise Jaccard (capped for efficiency)
        coverage_consistency = self._mean_pairwise_jaccard(per_trace_coverage)

        # Exception stats
        n_total = len(all_traces)
        exception_rate = n_exception_traces / n_total if n_total else 0.0

        # Call depth stats
        mean_depth = sum(call_depths) / len(call_depths) if call_depths else 0.0
        call_depth_stats = {
            "mean": round(mean_depth, 4),
            "max": float(max(call_depths, default=0)),
        }

        # Trace length stats
        mean_ev = sum(event_counts) / len(event_counts) if event_counts else 0.0
        n_ev = len(event_counts)
        var_ev = sum((x - mean_ev) ** 2 for x in event_counts) / n_ev if n_ev else 0.0
        trace_length_stats = {"mean": round(mean_ev, 4), "std": round(var_ev ** 0.5, 4)}

        # Hot path hash: top-5 anon function indices by frequency (rename-invariant)
        top5 = sorted(anon_call_freq.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        key = "|".join(str(idx) for idx, _ in top5)
        hot_path_hash = hashlib.sha256(key.encode()).hexdigest()[:16]

        return NormalizedBehavior(
            program_id=program_id,
            anon_call_freq=anon_call_freq,
            coverage_vector_size=coverage_vector_size,
            coverage_consistency=coverage_consistency,
            exception_type_set=sorted(exception_types),
            exception_rate=round(exception_rate, 6),
            call_depth_stats=call_depth_stats,
            trace_length_stats=trace_length_stats,
            hot_path_hash=hot_path_hash,
            n_unique_functions=len(name_to_idx),
            provenance={
                "program_id": program_id,
                "n_runs": len(all_runs),
                "n_traces_total": n_total,
                "n_functions_observed": len(name_to_idx),
                "feature_classification": "OUTPUT_FREE",
                "safeguard_2_compliant": True,
            },
        )

    @staticmethod
    def _mean_pairwise_jaccard(coverage_sets: List[Set[int]]) -> float:
        """Mean pairwise Jaccard across per-trace coverage sets (efficiency-capped)."""
        n = len(coverage_sets)
        if n < 2:
            return 1.0
        total = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, min(n, i + 6)):  # cap at 5 neighbors
                a, b = coverage_sets[i], coverage_sets[j]
                union = len(a | b)
                if union == 0:
                    total += 1.0
                else:
                    total += len(a & b) / union
                count += 1
        return round(total / count, 6) if count else 1.0

    @staticmethod
    def _empty(program_id: str) -> NormalizedBehavior:
        return NormalizedBehavior(
            program_id=program_id,
            anon_call_freq={},
            coverage_vector_size=0,
            coverage_consistency=1.0,
            exception_type_set=[],
            exception_rate=0.0,
            call_depth_stats={"mean": 0.0, "max": 0.0},
            trace_length_stats={"mean": 0.0, "std": 0.0},
            hot_path_hash=hashlib.sha256(b"").hexdigest()[:16],
            n_unique_functions=0,
            provenance={
                "program_id": program_id,
                "n_runs": 0,
                "n_traces_total": 0,
                "feature_classification": "OUTPUT_FREE",
                "safeguard_2_compliant": True,
            },
        )
