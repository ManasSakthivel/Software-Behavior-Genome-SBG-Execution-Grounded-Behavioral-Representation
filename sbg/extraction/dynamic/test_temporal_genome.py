"""
Tests for sbg.extraction.dynamic.temporal_genome
==================================================
All tests are deterministic (fixed inputs, no random state).

Coverage targets
----------------
* TemporalGenomeExtractor.extract → empty, single trace, multi-trace
* distance → identity (d(g,g)==0), symmetry, bounds [0,1]
* canonicalize → idempotency, negative-value clamping
"""

from __future__ import annotations

import math
from typing import List

import pytest

from sbg.extraction.dynamic.temporal_genome import (
    TemporalGenome,
    TemporalGenomeExtractor,
    canonicalize,
    distance,
)
from sbg.extraction.dynamic.tracer import ExecutionTrace, TraceEvent, Tracer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(fn: str, event_type: str, n_vars: int = 1) -> TraceEvent:
    return TraceEvent(
        event_type=event_type,
        function_name=fn,
        lineno=1,
        local_vars_snapshot={f"v{i}": "0" for i in range(n_vars)},
        timestamp_ns=0,
    )


def _make_trace(
    events: List[TraceEvent],
    *,
    program_id: str = "prog",
    exception: str | None = None,
) -> ExecutionTrace:
    return ExecutionTrace(
        program_id=program_id,
        input_repr="0",
        events=events,
        return_value=None,
        exception=exception,
        stdout="",
        execution_time_ms=1.0,
        coverage=set(),
        truncated=False,
    )


def _make_genome(
    latency: dict | None = None,
    ngrams: dict | None = None,
    phase: dict | None = None,
    entropy: float = 1.0,
) -> TemporalGenome:
    return TemporalGenome(
        call_return_latency_profile=latency or {"f": 2.0},
        event_sequence_ngrams=ngrams or {"call/f→return/f": 1},
        phase_timing=phase or {"f": 0.5},
        temporal_entropy=entropy,
        provenance={},
    )


# ---------------------------------------------------------------------------
# TemporalGenomeExtractor
# ---------------------------------------------------------------------------

class TestTemporalGenomeExtractor:

    def test_empty_traces_returns_empty_genome(self) -> None:
        g = TemporalGenomeExtractor().extract([])
        assert g.call_return_latency_profile == {}
        assert g.event_sequence_ngrams == {}
        assert g.phase_timing == {}
        assert g.temporal_entropy == 0.0

    def test_single_trace_call_return_latency(self) -> None:
        events = [
            _make_event("f", "call"),
            _make_event("f", "line"),
            _make_event("f", "return"),
        ]
        trace = _make_trace(events)
        g = TemporalGenomeExtractor().extract([trace])
        # latency = index_of_return - index_of_call = 2 - 0 = 2
        assert g.call_return_latency_profile["f"] == pytest.approx(2.0)

    def test_single_trace_bigrams(self) -> None:
        events = [
            _make_event("f", "call"),
            _make_event("f", "return"),
        ]
        trace = _make_trace(events)
        g = TemporalGenomeExtractor().extract([trace])
        key = "call/f→return/f"
        assert key in g.event_sequence_ngrams
        assert g.event_sequence_ngrams[key] == 1

    def test_bigrams_accumulated_across_traces(self) -> None:
        events = [
            _make_event("f", "call"),
            _make_event("f", "return"),
        ]
        traces = [_make_trace(events), _make_trace(events)]
        g = TemporalGenomeExtractor().extract(traces)
        key = "call/f→return/f"
        assert g.event_sequence_ngrams[key] == 2

    def test_phase_timing_sums_to_one_for_single_function(self) -> None:
        events = [_make_event("f", "call"), _make_event("f", "return")]
        trace = _make_trace(events)
        g = TemporalGenomeExtractor().extract([trace])
        assert g.phase_timing["f"] == pytest.approx(1.0)

    def test_phase_timing_two_functions(self) -> None:
        events = [
            _make_event("f", "call"),
            _make_event("g", "call"),
            _make_event("g", "return"),
            _make_event("f", "return"),
        ]
        trace = _make_trace(events)
        g = TemporalGenomeExtractor().extract([trace])
        # f appears twice (call + return), g appears twice → 50/50
        assert g.phase_timing["f"] == pytest.approx(0.5)
        assert g.phase_timing["g"] == pytest.approx(0.5)

    def test_temporal_entropy_uniform_distribution(self) -> None:
        """Uniform event type distribution → maximum entropy = log(4)."""
        events = [
            _make_event("f", "call"),
            _make_event("f", "line"),
            _make_event("f", "exception"),
            _make_event("f", "return"),
        ]
        trace = _make_trace(events)
        g = TemporalGenomeExtractor().extract([trace])
        expected = math.log(4)  # max Shannon entropy for 4 equal-prob events
        assert g.temporal_entropy == pytest.approx(expected, rel=1e-5)

    def test_temporal_entropy_single_type_is_zero(self) -> None:
        events = [_make_event("f", "call"), _make_event("f", "call")]
        trace = _make_trace(events)
        g = TemporalGenomeExtractor().extract([trace])
        assert g.temporal_entropy == pytest.approx(0.0)

    def test_provenance_n_traces(self) -> None:
        traces = [_make_trace([_make_event("f", "call")]) for _ in range(4)]
        g = TemporalGenomeExtractor().extract(traces)
        assert g.provenance["n_traces"] == 4

    def test_multiple_calls_same_function_latency_averaged(self) -> None:
        events = [
            _make_event("f", "call"),    # idx 0
            _make_event("f", "return"),  # idx 1  → latency 1
            _make_event("f", "call"),    # idx 2
            _make_event("f", "line"),    # idx 3
            _make_event("f", "line"),    # idx 4
            _make_event("f", "return"),  # idx 5  → latency 3
        ]
        trace = _make_trace(events)
        g = TemporalGenomeExtractor().extract([trace])
        # mean latency = (1 + 3) / 2 = 2.0
        assert g.call_return_latency_profile["f"] == pytest.approx(2.0)

    def test_via_real_tracer(self) -> None:
        """Integration: use Tracer to produce real traces then extract."""
        def _countdown(n: int) -> int:
            if n <= 0:
                return 0
            return _countdown(n - 1)

        traces = Tracer().trace(_countdown, [3, 5])
        g = TemporalGenomeExtractor().extract(traces)
        assert g.temporal_entropy >= 0.0
        assert "_countdown" in g.call_return_latency_profile

    def test_empty_events_trace_contributes_no_phase_timing(self) -> None:
        empty_trace = _make_trace([])
        g = TemporalGenomeExtractor().extract([empty_trace])
        assert g.phase_timing == {}

    def test_ngram_key_format(self) -> None:
        events = [
            _make_event("alpha", "call"),
            _make_event("beta", "line"),
        ]
        trace = _make_trace(events)
        g = TemporalGenomeExtractor().extract([trace])
        assert "call/alpha→line/beta" in g.event_sequence_ngrams


# ---------------------------------------------------------------------------
# distance
# ---------------------------------------------------------------------------

class TestTemporalGenomeDistance:

    def test_distance_self_is_zero(self) -> None:
        g = _make_genome()
        assert distance(g, g) == pytest.approx(0.0)

    def test_distance_identical_genomes_is_zero(self) -> None:
        g1 = _make_genome()
        g2 = _make_genome()
        assert distance(g1, g2) == pytest.approx(0.0)

    def test_distance_in_unit_interval(self) -> None:
        g1 = _make_genome(ngrams={"a→b": 1}, phase={"f": 1.0})
        g2 = _make_genome(ngrams={"c→d": 99}, phase={"g": 1.0})
        d = distance(g1, g2)
        assert 0.0 <= d <= 1.0

    def test_distance_symmetry(self) -> None:
        g1 = _make_genome(ngrams={"a→b": 1}, phase={"f": 0.3})
        g2 = _make_genome(ngrams={"c→d": 5}, phase={"g": 0.7})
        assert distance(g1, g2) == pytest.approx(distance(g2, g1))

    def test_disjoint_ngrams_gives_max_jaccard(self) -> None:
        g1 = _make_genome(ngrams={"a→b": 1}, phase={})
        g2 = _make_genome(ngrams={"c→d": 1}, phase={})
        # Jaccard = 1.0, phase dist = 0 → total = 0.5
        assert distance(g1, g2) == pytest.approx(0.5)

    def test_identical_ngrams_zero_jaccard_component(self) -> None:
        ng = {"a→b": 10}
        g1 = _make_genome(ngrams=ng, phase={"f": 0.5})
        g2 = _make_genome(ngrams=ng, phase={"f": 0.5})
        assert distance(g1, g2) == pytest.approx(0.0)

    def test_distance_empty_genomes_is_zero(self) -> None:
        g1 = TemporalGenomeExtractor().extract([])
        g2 = TemporalGenomeExtractor().extract([])
        assert distance(g1, g2) == pytest.approx(0.0)

    def test_distance_never_exceeds_one(self) -> None:
        g1 = _make_genome(ngrams={f"a{i}→b{i}": i for i in range(20)}, phase={"f": 1.0})
        g2 = _make_genome(ngrams={f"c{i}→d{i}": i for i in range(20)}, phase={"g": 1.0})
        assert distance(g1, g2) <= 1.0


# ---------------------------------------------------------------------------
# canonicalize
# ---------------------------------------------------------------------------

class TestTemporalGenomeCanonicalize:

    def test_canonicalize_idempotent(self) -> None:
        g = _make_genome()
        c1 = canonicalize(g)
        c2 = canonicalize(c1)
        assert c1.call_return_latency_profile == c2.call_return_latency_profile
        assert c1.event_sequence_ngrams == c2.event_sequence_ngrams
        assert c1.phase_timing == c2.phase_timing
        assert c1.temporal_entropy == c2.temporal_entropy

    def test_canonicalize_removes_non_positive_latency(self) -> None:
        g = _make_genome(latency={"f": 2.0, "g": -1.0, "h": 0.0})
        c = canonicalize(g)
        assert "g" not in c.call_return_latency_profile
        assert "h" not in c.call_return_latency_profile
        assert "f" in c.call_return_latency_profile

    def test_canonicalize_removes_zero_ngrams(self) -> None:
        g = _make_genome(ngrams={"a→b": 3, "c→d": 0})
        c = canonicalize(g)
        assert "c→d" not in c.event_sequence_ngrams
        assert "a→b" in c.event_sequence_ngrams

    def test_canonicalize_clamps_entropy_to_non_negative(self) -> None:
        g = _make_genome(entropy=-5.0)
        c = canonicalize(g)
        assert c.temporal_entropy >= 0.0

    def test_canonicalize_sets_canonicalized_flag(self) -> None:
        g = _make_genome()
        c = canonicalize(g)
        assert c.provenance.get("canonicalized") is True

    def test_canonicalize_clamps_phase_timing(self) -> None:
        g = _make_genome(phase={"f": 1.5, "g": -0.1, "h": 0.3})
        c = canonicalize(g)
        assert c.phase_timing.get("f") == pytest.approx(1.0)
        assert "g" not in c.phase_timing
        assert c.phase_timing.get("h") == pytest.approx(0.3)

    def test_canonicalize_distance_self_still_zero(self) -> None:
        g = _make_genome()
        c = canonicalize(g)
        assert distance(c, c) == pytest.approx(0.0)
