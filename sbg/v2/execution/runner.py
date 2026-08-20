"""
sbg.v2.execution.runner
========================
SandboxRunner — wraps v1 Tracer with noise-floor measurement (SAFEGUARD-6),
reproducibility seeding, and per-program run isolation.

Formal grounding
----------------
SandboxResult ↔ extended τ(P, I_v2) — execution trace bundle for input set I_v2.

Design principles
-----------------
* Composes v1 Tracer (sbg.extraction.dynamic.tracer.Tracer). Does NOT replace it.
* Runs each program N times (default 5) to measure intra-version variance (SAFEGUARD-6).
* Features with intra-version std > 10% of mean are flagged as non-deterministic.
* Concurrency programs (conc_producer_consumer, conc_read_write_lock) are excluded.
* No third-party imports.

SAFEGUARD-2
-----------
SandboxRunner only collects raw ExecutionTrace objects from v1 Tracer.
Feature extraction (TraceNormalizer, DynamicGenomeExtractor) enforces output-free
classification. SandboxRunner itself does not extract features.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from sbg.extraction.dynamic.tracer import Tracer, ExecutionTrace

# Programs excluded from dynamic execution (non-deterministic threading)
_UNSAFE_PROGRAMS = {"conc_producer_consumer", "conc_read_write_lock"}


@dataclass
class SandboxResult:
    """
    Result of running a program N times under the SandboxRunner.

    Fields
    ------
    program_id : str
    traces : List[List[ExecutionTrace]]
        Outer list: one entry per run. Inner list: one trace per input.
    n_runs : int
    seed : int
        RNG seed used (for reproducibility logging).
    wall_time_ms : float
        Total wall-clock time for all runs.
    noise_floor_stats : Dict[str, float]
        Per-feature std across runs (SAFEGUARD-6).
        Keys: "{feature}_std" and "{feature}_mean" for each tracked feature.
    non_deterministic_flags : List[str]
        Features where std/mean > NOISE_THRESHOLD.
    timeout_fraction : float
        Fraction of individual traces that timed out.
    error : Optional[str]
        If program could not be run (unsafe, import error), reason here.
    """
    program_id: str
    traces: List[List[ExecutionTrace]]
    n_runs: int
    seed: int
    wall_time_ms: float
    noise_floor_stats: Dict[str, float] = field(default_factory=dict)
    non_deterministic_flags: List[str] = field(default_factory=list)
    timeout_fraction: float = 0.0
    error: Optional[str] = None


class SandboxRunner:
    """
    Runs a callable N times under the v1 Tracer for noise-floor measurement.

    Parameters
    ----------
    noise_threshold : float
        std/mean ratio above which a feature is flagged non-deterministic. Default 0.10.

    Usage
    -----
        runner = SandboxRunner()
        result = runner.run("sort_quicksort", my_func, inputs, n_runs=5)
    """

    NOISE_THRESHOLD = 0.10

    def __init__(self) -> None:
        self._tracer = Tracer()

    def run(
        self,
        program_id: str,
        func: Callable,
        inputs: List[Any],
        n_runs: int = 5,
        seed: int = 42,
        max_events: int = 10_000,
    ) -> SandboxResult:
        """
        Execute func(inp) for each inp in inputs, n_runs times.

        Parameters
        ----------
        program_id : str
        func : Callable
        inputs : List[Any]
            One trace produced per element per run.
        n_runs : int >= 1
            Number of independent runs for noise floor estimation.
        seed : int
            For reproducibility logging (inputs are not shuffled).
        max_events : int
            Passed to v1 Tracer.

        Returns
        -------
        SandboxResult
        """
        # Safety check
        if program_id in _UNSAFE_PROGRAMS:
            return SandboxResult(
                program_id=program_id,
                traces=[],
                n_runs=0,
                seed=seed,
                wall_time_ms=0.0,
                error=f"UNSAFE_CONCURRENT_PROGRAM: {program_id}",
            )

        all_runs: List[List[ExecutionTrace]] = []
        start_wall = time.monotonic()

        for _ in range(max(1, n_runs)):
            run_traces = self._tracer.trace(func, inputs, max_events=max_events)
            all_runs.append(run_traces)

        wall_ms = (time.monotonic() - start_wall) * 1000.0

        noise_stats = self._compute_noise_floor(all_runs)
        flags = self._flag_noisy_features(noise_stats)
        timeout_frac = self._timeout_fraction(all_runs)

        return SandboxResult(
            program_id=program_id,
            traces=all_runs,
            n_runs=len(all_runs),
            seed=seed,
            wall_time_ms=wall_ms,
            noise_floor_stats=noise_stats,
            non_deterministic_flags=flags,
            timeout_fraction=timeout_frac,
            error=None,
        )

    # ------------------------------------------------------------------
    # Noise floor computation (SAFEGUARD-6)
    # ------------------------------------------------------------------

    def _compute_noise_floor(
        self, all_runs: List[List[ExecutionTrace]]
    ) -> Dict[str, float]:
        """
        Compute per-feature std and mean across runs.

        Features tracked (all output-free per SAFEGUARD-2):
          - coverage_size: total unique lines covered (union across inputs)
          - call_count_total: total call events across all traces in run
          - event_count_mean: mean events per trace
          - exception_fraction: fraction of traces with exceptions
          - n_functions_called: unique function names across all traces
        """
        if not all_runs:
            return {}

        feature_vectors: Dict[str, List[float]] = {
            "coverage_size": [],
            "call_count_total": [],
            "event_count_mean": [],
            "exception_fraction": [],
            "n_functions_called": [],
        }

        for run_traces in all_runs:
            if not run_traces:
                continue
            coverage_union: set = set()
            call_total = 0
            event_lengths = []
            n_exceptions = 0
            all_funcs: set = set()

            for trace in run_traces:
                coverage_union.update(trace.coverage)
                event_lengths.append(len(trace.events))
                for ev in trace.events:
                    if ev.event_type == "call":
                        call_total += 1
                        all_funcs.add(ev.function_name)
                if trace.exception is not None:
                    n_exceptions += 1

            feature_vectors["coverage_size"].append(float(len(coverage_union)))
            feature_vectors["call_count_total"].append(float(call_total))
            n_tr = len(run_traces)
            mean_ev = sum(event_lengths) / n_tr if n_tr else 0.0
            feature_vectors["event_count_mean"].append(mean_ev)
            feature_vectors["exception_fraction"].append(n_exceptions / n_tr if n_tr else 0.0)
            feature_vectors["n_functions_called"].append(float(len(all_funcs)))

        result: Dict[str, float] = {}
        for feat, vals in feature_vectors.items():
            if not vals:
                result[f"{feat}_std"] = 0.0
                result[f"{feat}_mean"] = 0.0
                continue
            mean = sum(vals) / len(vals)
            variance = sum((v - mean) ** 2 for v in vals) / len(vals) if len(vals) > 1 else 0.0
            std = variance ** 0.5
            result[f"{feat}_std"] = round(std, 6)
            result[f"{feat}_mean"] = round(mean, 6)

        return result

    def _flag_noisy_features(self, noise_stats: Dict[str, float]) -> List[str]:
        """Flag features where std/mean > NOISE_THRESHOLD (SAFEGUARD-6)."""
        flags = []
        for feat in ["coverage_size", "call_count_total", "event_count_mean",
                     "exception_fraction", "n_functions_called"]:
            std = noise_stats.get(f"{feat}_std", 0.0)
            mean = noise_stats.get(f"{feat}_mean", 0.0)
            if mean > 0 and std / mean > self.NOISE_THRESHOLD:
                flags.append(feat)
        return flags

    def _timeout_fraction(self, all_runs: List[List[ExecutionTrace]]) -> float:
        total = sum(len(r) for r in all_runs)
        if total == 0:
            return 0.0
        timed_out = sum(
            1 for r in all_runs for t in r
            if t.exception is not None and "TimeoutError" in str(t.exception)
        )
        return timed_out / total
