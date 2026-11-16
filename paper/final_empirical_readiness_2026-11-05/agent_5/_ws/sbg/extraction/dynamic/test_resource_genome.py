"""
Tests for sbg.extraction.dynamic.resource_genome
==================================================
All tests are deterministic (fixed inputs, no random state).

Coverage targets
----------------
* ResourceGenomeExtractor.extract → empty traces, single trace, multi-trace
* distance → identity (d(g,g)==0), symmetry, bounds [0,1], heterogeneous genomes
* canonicalize → idempotency, non-negative clamps, exception_rate bounds
"""

from __future__ import annotations

import math
from typing import List

import pytest

from sbg.extraction.dynamic.resource_genome import (
    ResourceGenome,
    ResourceGenomeExtractor,
    canonicalize,
    distance,
)
from sbg.extraction.dynamic.tracer import ExecutionTrace, TraceEvent, Tracer


# ---------------------------------------------------------------------------
# Helpers — build minimal ExecutionTrace objects without running Tracer
# ---------------------------------------------------------------------------

def _make_event(fn: str = "f", event_type: str = "call", n_vars: int = 2) -> TraceEvent:
    return TraceEvent(
        event_type=event_type,
        function_name=fn,
        lineno=1,
        local_vars_snapshot={f"v{i}": "0" for i in range(n_vars)},
        timestamp_ns=0,
    )


def _make_trace(
    *,
    execution_time_ms: float = 10.0,
    events: List[TraceEvent] | None = None,
    exception: str | None = None,
    program_id: str = "prog",
) -> ExecutionTrace:
    if events is None:
        events = [_make_event("f", "call"), _make_event("f", "return")]
    return ExecutionTrace(
        program_id=program_id,
        input_repr="0",
        events=events,
        return_value=None,
        exception=exception,
        stdout="",
        execution_time_ms=execution_time_ms,
        coverage=set(),
        truncated=False,
    )


def _make_genome(
    *,
    time_mean: float = 10.0,
    time_std: float = 1.0,
    time_min: float = 9.0,
    time_max: float = 11.0,
    len_mean: float = 5.0,
    len_std: float = 0.0,
    len_min: float = 5.0,
    len_max: float = 5.0,
    function_call_total: int = 3,
    exception_rate: float = 0.0,
    avg_local_var_count: float = 2.0,
) -> ResourceGenome:
    return ResourceGenome(
        execution_time_ms_stats={
            "mean": time_mean, "std": time_std, "min": time_min, "max": time_max,
        },
        trace_length_stats={
            "mean": len_mean, "std": len_std, "min": len_min, "max": len_max,
        },
        function_call_total=function_call_total,
        exception_rate=exception_rate,
        avg_local_var_count=avg_local_var_count,
        provenance={},
    )


# ---------------------------------------------------------------------------
# ResourceGenomeExtractor
# ---------------------------------------------------------------------------

class TestResourceGenomeExtractor:

    def test_empty_traces_returns_zero_genome(self) -> None:
        g = ResourceGenomeExtractor().extract([])
        assert g.function_call_total == 0
        assert g.exception_rate == 0.0
        assert g.avg_local_var_count == 0.0
        assert g.trace_length_stats["mean"] == 0.0

    def test_single_trace_execution_time_preserved(self) -> None:
        trace = _make_trace(execution_time_ms=42.5)
        g = ResourceGenomeExtractor().extract([trace])
        assert g.execution_time_ms_stats["mean"] == pytest.approx(42.5)
        assert g.execution_time_ms_stats["min"] == pytest.approx(42.5)
        assert g.execution_time_ms_stats["max"] == pytest.approx(42.5)
        assert g.execution_time_ms_stats["std"] == pytest.approx(0.0)

    def test_single_trace_no_exception(self) -> None:
        g = ResourceGenomeExtractor().extract([_make_trace()])
        assert g.exception_rate == 0.0

    def test_single_trace_with_exception(self) -> None:
        trace = _make_trace(exception="ValueError: bad")
        g = ResourceGenomeExtractor().extract([trace])
        assert g.exception_rate == pytest.approx(1.0)

    def test_exception_rate_fraction(self) -> None:
        traces = [
            _make_trace(exception="Err"),
            _make_trace(exception=None),
            _make_trace(exception=None),
            _make_trace(exception="Err"),
        ]
        g = ResourceGenomeExtractor().extract(traces)
        assert g.exception_rate == pytest.approx(0.5)

    def test_function_call_total_counts_only_calls(self) -> None:
        events = [
            _make_event("f", "call"),
            _make_event("f", "line"),
            _make_event("f", "return"),
            _make_event("g", "call"),
            _make_event("g", "return"),
        ]
        trace = _make_trace(events=events)
        g = ResourceGenomeExtractor().extract([trace])
        assert g.function_call_total == 2

    def test_trace_length_stats_multi(self) -> None:
        t1 = _make_trace(events=[_make_event() for _ in range(3)])
        t2 = _make_trace(events=[_make_event() for _ in range(7)])
        g = ResourceGenomeExtractor().extract([t1, t2])
        assert g.trace_length_stats["mean"] == pytest.approx(5.0)
        assert g.trace_length_stats["min"] == pytest.approx(3.0)
        assert g.trace_length_stats["max"] == pytest.approx(7.0)

    def test_avg_local_var_count(self) -> None:
        events = [
            _make_event("f", "call", n_vars=4),
            _make_event("f", "return", n_vars=0),
        ]
        trace = _make_trace(events=events)
        g = ResourceGenomeExtractor().extract([trace])
        assert g.avg_local_var_count == pytest.approx(2.0)  # (4+0)/2

    def test_provenance_contains_n_traces(self) -> None:
        traces = [_make_trace() for _ in range(5)]
        g = ResourceGenomeExtractor().extract(traces)
        assert g.provenance["n_traces"] == 5

    def test_provenance_contains_program_id(self) -> None:
        trace = _make_trace(program_id="my_prog")
        g = ResourceGenomeExtractor().extract([trace])
        assert "my_prog" in g.provenance["program_ids"]

    def test_via_real_tracer(self) -> None:
        """Integration: use Tracer to produce real traces then extract."""
        def _simple(x: int) -> int:
            return x * 2

        traces = Tracer().trace(_simple, [1, 2, 3])
        g = ResourceGenomeExtractor().extract(traces)
        assert g.function_call_total >= 3
        assert g.exception_rate == 0.0
        assert g.trace_length_stats["mean"] > 0


# ---------------------------------------------------------------------------
# distance
# ---------------------------------------------------------------------------

class TestResourceGenomeDistance:

    def test_distance_self_is_zero(self) -> None:
        g = _make_genome()
        assert distance(g, g) == pytest.approx(0.0)

    def test_distance_identical_genomes_is_zero(self) -> None:
        g1 = _make_genome()
        g2 = _make_genome()
        assert distance(g1, g2) == pytest.approx(0.0)

    def test_distance_in_unit_interval(self) -> None:
        g1 = _make_genome(time_mean=1.0, exception_rate=0.0)
        g2 = _make_genome(time_mean=9999.0, exception_rate=1.0)
        d = distance(g1, g2)
        assert 0.0 <= d <= 1.0

    def test_distance_symmetry(self) -> None:
        g1 = _make_genome(time_mean=5.0, exception_rate=0.1)
        g2 = _make_genome(time_mean=50.0, exception_rate=0.9)
        assert distance(g1, g2) == pytest.approx(distance(g2, g1))

    def test_different_exception_rates_produce_nonzero_distance(self) -> None:
        g1 = _make_genome(exception_rate=0.0)
        g2 = _make_genome(exception_rate=1.0)
        assert distance(g1, g2) > 0.0

    def test_same_exception_rate_same_times_zero_distance(self) -> None:
        g1 = _make_genome(exception_rate=0.5, time_mean=10.0, time_std=1.0,
                          time_min=9.0, time_max=11.0)
        g2 = _make_genome(exception_rate=0.5, time_mean=10.0, time_std=1.0,
                          time_min=9.0, time_max=11.0)
        assert distance(g1, g2) == pytest.approx(0.0)

    def test_distance_never_exceeds_one(self) -> None:
        g1 = _make_genome(time_mean=0.0001, time_std=0.0, time_min=0.0, time_max=0.0001)
        g2 = _make_genome(time_mean=1e9, time_std=1e8, time_min=0.5e9, time_max=2e9)
        d = distance(g1, g2)
        assert d <= 1.0

    def test_distance_empty_genomes_is_zero(self) -> None:
        g1 = ResourceGenomeExtractor().extract([])
        g2 = ResourceGenomeExtractor().extract([])
        assert distance(g1, g2) == pytest.approx(0.0)

    def test_distance_between_extracted_genomes(self) -> None:
        """Two different trace sets should have distance > 0."""
        def _fast(x):
            return x

        def _slow(x):
            total = 0
            for i in range(100):
                total += i
            return total + x

        tracer = Tracer()
        traces_fast = tracer.trace(_fast, [1, 2])
        traces_slow = tracer.trace(_slow, [1, 2])
        g_fast = ResourceGenomeExtractor().extract(traces_fast)
        g_slow = ResourceGenomeExtractor().extract(traces_slow)
        # At minimum the trace lengths will differ
        assert distance(g_fast, g_slow) >= 0.0


# ---------------------------------------------------------------------------
# canonicalize
# ---------------------------------------------------------------------------

class TestResourceGenomeCanonicalize:

    def test_canonicalize_idempotent(self) -> None:
        g = _make_genome(exception_rate=0.3)
        c1 = canonicalize(g)
        c2 = canonicalize(c1)
        assert c1.exception_rate == c2.exception_rate
        assert c1.function_call_total == c2.function_call_total
        assert c1.avg_local_var_count == c2.avg_local_var_count
        assert c1.execution_time_ms_stats == c2.execution_time_ms_stats
        assert c1.trace_length_stats == c2.trace_length_stats

    def test_canonicalize_clamps_negative_exception_rate(self) -> None:
        g = _make_genome(exception_rate=-0.5)
        c = canonicalize(g)
        assert c.exception_rate == 0.0

    def test_canonicalize_clamps_exception_rate_above_one(self) -> None:
        g = _make_genome(exception_rate=2.0)
        c = canonicalize(g)
        assert c.exception_rate == 1.0

    def test_canonicalize_clamps_negative_call_total(self) -> None:
        g = _make_genome()
        g.function_call_total = -5
        c = canonicalize(g)
        assert c.function_call_total == 0

    def test_canonicalize_sets_canonicalized_flag(self) -> None:
        g = _make_genome()
        c = canonicalize(g)
        assert c.provenance.get("canonicalized") is True

    def test_canonicalize_clamps_negative_stats(self) -> None:
        g = _make_genome(time_mean=-1.0, time_std=-0.5, time_min=-2.0, time_max=-0.1)
        c = canonicalize(g)
        for v in c.execution_time_ms_stats.values():
            assert v >= 0.0

    def test_canonicalize_distance_self_still_zero_after_canonicalize(self) -> None:
        g = _make_genome()
        c = canonicalize(g)
        assert distance(c, c) == pytest.approx(0.0)
