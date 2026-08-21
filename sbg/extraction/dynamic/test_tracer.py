"""
tests for sbg.extraction.dynamic.tracer
========================================
All tests are deterministic (no random state, fixed seeds where relevant).

Pytest-cov / coverage note
---------------------------
pytest installs its own sys.settrace-based coverage tracer.  The Tracer class
saves and restores the existing tracer around every call, so coverage
collection continues normally across the entire test run.
"""

from __future__ import annotations

import sys
import time
from typing import List

import pytest

from sbg.extraction.dynamic.tracer import (
    ExecutionGenome,
    ExecutionGenomeExtractor,
    ExecutionTrace,
    Tracer,
    TraceEvent,
    canonicalize,
    distance,
)


# ---------------------------------------------------------------------------
# Tiny helper functions used as trace targets
# ---------------------------------------------------------------------------

def _add(x):
    """Simple deterministic function."""
    return x + 1


def _fibonacci(n):
    """Recursive function — exercises call/return events."""
    if n <= 1:
        return n
    return _fibonacci(n - 1) + _fibonacci(n - 2)


def _raises(x):
    """Always raises."""
    raise ValueError(f"bad value: {x}")


def _sleepy(x):
    """Sleeps longer than the 5-second timeout."""
    time.sleep(10)
    return x


def _print_something(x):
    """Writes to stdout."""
    print(f"value={x}")
    return x


def _many_lines(n):
    """
    Generates many events by looping — used to test max_events truncation.
    Iterates n times; each iteration fires multiple trace events.
    """
    total = 0
    for i in range(n):
        total += i
    return total


# ---------------------------------------------------------------------------
# 1. Basic tracing — Tracer on simple functions
# ---------------------------------------------------------------------------

class TestTracerBasic:
    def test_returns_one_trace_per_input(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [1, 2, 3])
        assert len(traces) == 3

    def test_trace_return_value_correct(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [10])
        assert traces[0].return_value == 11

    def test_trace_exception_captured(self):
        tracer = Tracer()
        traces = tracer.trace(_raises, ["oops"])
        t = traces[0]
        assert t.exception is not None
        assert "ValueError" in t.exception
        assert t.return_value is None

    def test_trace_no_exception_on_normal_execution(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [5])
        assert traces[0].exception is None

    def test_stdout_captured(self):
        tracer = Tracer()
        traces = tracer.trace(_print_something, [42])
        assert "42" in traces[0].stdout

    def test_execution_time_ms_positive(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [1])
        assert traces[0].execution_time_ms >= 0.0

    def test_program_id_set(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [1])
        assert traces[0].program_id == "_add"

    def test_input_repr_set(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [99])
        assert traces[0].input_repr == "99"

    def test_trace_events_not_empty(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [1])
        assert len(traces[0].events) > 0

    def test_trace_event_fields(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [1])
        ev = traces[0].events[0]
        assert isinstance(ev, TraceEvent)
        assert ev.event_type in ("call", "return", "line", "exception")
        assert isinstance(ev.function_name, str)
        assert isinstance(ev.lineno, int)
        assert isinstance(ev.local_vars_snapshot, dict)
        assert isinstance(ev.timestamp_ns, int)

    def test_local_vars_capped_at_100_chars(self):
        def _long_repr(x):
            return list(range(1000))  # repr will be >> 100 chars

        tracer = Tracer()
        traces = tracer.trace(_long_repr, [None])
        for ev in traces[0].events:
            for v in ev.local_vars_snapshot.values():
                assert len(v) <= 100, f"snapshot value exceeds 100 chars: {v!r}"

    def test_multiple_inputs_independent(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [0, 1, 2])
        return_values = [t.return_value for t in traces]
        assert return_values == [1, 2, 3]

    def test_recursive_function_traced(self):
        tracer = Tracer()
        traces = tracer.trace(_fibonacci, [6])
        assert traces[0].return_value == 8
        assert len(traces[0].events) > 0


# ---------------------------------------------------------------------------
# 2. Coverage vector
# ---------------------------------------------------------------------------

class TestCoverageVector:
    def test_coverage_non_empty_after_execution(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [1])
        assert len(traces[0].coverage) > 0

    def test_coverage_contains_integers(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [1])
        for line in traces[0].coverage:
            assert isinstance(line, int)

    def test_coverage_grows_with_branches(self):
        def _branchy(x):
            if x > 0:
                return "pos"
            elif x < 0:
                return "neg"
            else:
                return "zero"

        tracer = Tracer()
        t_pos = tracer.trace(_branchy, [1])[0]
        t_neg = tracer.trace(_branchy, [-1])[0]
        # The two traces should cover different lines.
        assert t_pos.coverage != t_neg.coverage


# ---------------------------------------------------------------------------
# 3. Timeout
# ---------------------------------------------------------------------------

class TestTimeout:
    def test_timeout_fires_within_reasonable_time(self):
        """A function that sleeps 10 s must be killed well under 10 s."""
        tracer = Tracer()
        start = time.monotonic()
        traces = tracer.trace(_sleepy, [None])
        elapsed = time.monotonic() - start
        # Must terminate before the 10-second sleep completes.
        assert elapsed < 9.5, f"Timeout did not fire in time: {elapsed:.1f} s"

    def test_timeout_sets_exception(self):
        tracer = Tracer()
        traces = tracer.trace(_sleepy, [None])
        t = traces[0]
        assert t.exception is not None
        assert "Timeout" in t.exception or "timeout" in t.exception.lower()

    def test_timeout_return_value_is_none(self):
        tracer = Tracer()
        traces = tracer.trace(_sleepy, [None])
        assert traces[0].return_value is None


# ---------------------------------------------------------------------------
# 4. sys.settrace always restored
# ---------------------------------------------------------------------------

class TestSetttraceRestored:
    def test_settrace_restored_on_normal_execution(self):
        original = sys.gettrace()
        tracer = Tracer()
        tracer.trace(_add, [1])
        assert sys.gettrace() is original

    def test_settrace_restored_after_exception(self):
        original = sys.gettrace()
        tracer = Tracer()
        tracer.trace(_raises, ["x"])
        assert sys.gettrace() is original

    def test_settrace_restored_after_timeout(self):
        original = sys.gettrace()
        tracer = Tracer()
        tracer.trace(_sleepy, [None])
        assert sys.gettrace() is original

    def test_settrace_restored_after_max_events(self):
        original = sys.gettrace()
        tracer = Tracer()
        tracer.trace(_many_lines, [100_000], max_events=5)
        assert sys.gettrace() is original


# ---------------------------------------------------------------------------
# 5. max_events truncation
# ---------------------------------------------------------------------------

class TestMaxEventsTruncation:
    def test_events_capped_at_max_events(self):
        tracer = Tracer()
        traces = tracer.trace(_many_lines, [100_000], max_events=50)
        assert len(traces[0].events) <= 50

    def test_truncated_flag_set_when_capped(self):
        tracer = Tracer()
        traces = tracer.trace(_many_lines, [100_000], max_events=10)
        assert traces[0].truncated is True

    def test_truncated_flag_not_set_on_short_execution(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [1], max_events=10_000)
        assert traces[0].truncated is False

    def test_no_events_when_max_events_is_zero(self):
        tracer = Tracer()
        traces = tracer.trace(_add, [1], max_events=0)
        assert len(traces[0].events) == 0


# ---------------------------------------------------------------------------
# 6. ExecutionGenomeExtractor
# ---------------------------------------------------------------------------

class TestExecutionGenomeExtractor:
    def _make_traces(self, n_inputs: int = 3) -> List[ExecutionTrace]:
        tracer = Tracer()
        return tracer.trace(_fibonacci, list(range(1, n_inputs + 1)))

    def test_extract_returns_execution_genome(self):
        extractor = ExecutionGenomeExtractor()
        traces = self._make_traces()
        g = extractor.extract(traces)
        assert isinstance(g, ExecutionGenome)

    def test_coverage_vector_non_empty(self):
        extractor = ExecutionGenomeExtractor()
        traces = self._make_traces()
        g = extractor.extract(traces)
        assert len(g.coverage_vector) > 0

    def test_coverage_vector_sorted(self):
        extractor = ExecutionGenomeExtractor()
        traces = self._make_traces()
        g = extractor.extract(traces)
        assert g.coverage_vector == sorted(g.coverage_vector)

    def test_function_call_counts_populated(self):
        extractor = ExecutionGenomeExtractor()
        traces = self._make_traces()
        g = extractor.extract(traces)
        assert len(g.function_call_counts) > 0

    def test_instruction_type_histogram_has_standard_keys(self):
        extractor = ExecutionGenomeExtractor()
        traces = self._make_traces()
        g = extractor.extract(traces)
        for key in ("call", "return", "line"):
            assert key in g.instruction_type_histogram

    def test_instruction_counts_non_negative(self):
        extractor = ExecutionGenomeExtractor()
        traces = self._make_traces()
        g = extractor.extract(traces)
        for v in g.instruction_type_histogram.values():
            assert v >= 0

    def test_hot_path_signature_is_string(self):
        extractor = ExecutionGenomeExtractor()
        traces = self._make_traces()
        g = extractor.extract(traces)
        assert isinstance(g.hot_path_signature, str)
        assert len(g.hot_path_signature) > 0

    def test_trace_length_stats_keys(self):
        extractor = ExecutionGenomeExtractor()
        traces = self._make_traces()
        g = extractor.extract(traces)
        for key in ("mean", "std", "min", "max"):
            assert key in g.trace_length_stats

    def test_trace_length_stats_min_le_max(self):
        extractor = ExecutionGenomeExtractor()
        traces = self._make_traces()
        g = extractor.extract(traces)
        assert g.trace_length_stats["min"] <= g.trace_length_stats["max"]

    def test_truncated_trace_fraction_in_range(self):
        extractor = ExecutionGenomeExtractor()
        traces = self._make_traces()
        g = extractor.extract(traces)
        assert 0.0 <= g.truncated_trace_fraction <= 1.0

    def test_truncated_fraction_non_zero_when_truncated(self):
        tracer = Tracer()
        traces = tracer.trace(_many_lines, [100_000], max_events=10)
        extractor = ExecutionGenomeExtractor()
        g = extractor.extract(traces)
        assert g.truncated_trace_fraction > 0.0

    def test_provenance_contains_n_traces(self):
        extractor = ExecutionGenomeExtractor()
        traces = self._make_traces(4)
        g = extractor.extract(traces)
        assert g.provenance["n_traces"] == 4

    def test_empty_traces_list(self):
        extractor = ExecutionGenomeExtractor()
        g = extractor.extract([])
        assert g.coverage_vector == []
        assert g.function_call_counts == {}
        assert g.truncated_trace_fraction == 0.0


# ---------------------------------------------------------------------------
# 7. distance
# ---------------------------------------------------------------------------

class TestDistance:
    def _genome_from_func(self, func, inputs):
        tracer = Tracer()
        traces = tracer.trace(func, inputs)
        return ExecutionGenomeExtractor().extract(traces)

    def test_distance_self_is_zero(self):
        g = self._genome_from_func(_fibonacci, [1, 2, 3, 4, 5])
        assert distance(g, g) == pytest.approx(0.0)

    def test_distance_in_range(self):
        g1 = self._genome_from_func(_fibonacci, [1, 2, 3])
        g2 = self._genome_from_func(_add, [1, 2, 3])
        d = distance(g1, g2)
        assert 0.0 <= d <= 1.0, f"distance out of [0,1]: {d}"

    def test_distance_symmetric(self):
        g1 = self._genome_from_func(_fibonacci, [1, 2, 3])
        g2 = self._genome_from_func(_add, [1, 2, 3])
        assert distance(g1, g2) == pytest.approx(distance(g2, g1))

    def test_distance_between_similar_functions_less_than_different(self):
        """fib(n) vs fib(n+1) should be closer than fib vs add."""
        g_fib_a = self._genome_from_func(_fibonacci, [1, 2, 3, 4])
        g_fib_b = self._genome_from_func(_fibonacci, [2, 3, 4, 5])
        g_add = self._genome_from_func(_add, [1, 2, 3, 4])
        d_fib_fib = distance(g_fib_a, g_fib_b)
        d_fib_add = distance(g_fib_a, g_add)
        assert d_fib_fib <= d_fib_add

    def test_distance_empty_genomes_is_zero(self):
        extractor = ExecutionGenomeExtractor()
        g1 = extractor.extract([])
        g2 = extractor.extract([])
        assert distance(g1, g2) == pytest.approx(0.0)

    def test_distance_one_empty_one_non_empty(self):
        extractor = ExecutionGenomeExtractor()
        g_empty = extractor.extract([])
        g_full = self._genome_from_func(_add, [1])
        d = distance(g_empty, g_full)
        assert 0.0 <= d <= 1.0


# ---------------------------------------------------------------------------
# 8. canonicalize
# ---------------------------------------------------------------------------

class TestCanonicalize:
    def _make_genome(self) -> ExecutionGenome:
        tracer = Tracer()
        traces = tracer.trace(_fibonacci, [1, 2, 3, 4])
        return ExecutionGenomeExtractor().extract(traces)

    def test_canonicalize_idempotent(self):
        g = self._make_genome()
        c1 = canonicalize(g)
        c2 = canonicalize(c1)
        assert c1.coverage_vector == c2.coverage_vector
        assert c1.function_call_counts == c2.function_call_counts
        assert c1.instruction_type_histogram == c2.instruction_type_histogram
        assert c1.hot_path_signature == c2.hot_path_signature
        assert c1.truncated_trace_fraction == c2.truncated_trace_fraction

    def test_canonicalize_sorts_coverage(self):
        g = self._make_genome()
        # Deliberately scramble coverage.
        scrambled = ExecutionGenome(
            coverage_vector=list(reversed(g.coverage_vector)),
            function_call_counts=g.function_call_counts,
            instruction_type_histogram=g.instruction_type_histogram,
            hot_path_signature=g.hot_path_signature,
            trace_length_stats=g.trace_length_stats,
            truncated_trace_fraction=g.truncated_trace_fraction,
            provenance=g.provenance,
        )
        c = canonicalize(scrambled)
        assert c.coverage_vector == sorted(c.coverage_vector)

    def test_canonicalize_removes_zero_call_counts(self):
        g = ExecutionGenome(
            coverage_vector=[1, 2, 3],
            function_call_counts={"foo": 5, "bar": 0, "baz": 3},
            instruction_type_histogram={"call": 8, "return": 8, "line": 10, "exception": 0},
            hot_path_signature="dummy",
            trace_length_stats={"mean": 1.0, "std": 0.0, "min": 1.0, "max": 1.0},
            truncated_trace_fraction=0.0,
            provenance={},
        )
        c = canonicalize(g)
        assert "bar" not in c.function_call_counts
        assert "foo" in c.function_call_counts

    def test_canonicalize_clamps_fraction(self):
        g = ExecutionGenome(
            coverage_vector=[],
            function_call_counts={},
            instruction_type_histogram={},
            hot_path_signature="",
            trace_length_stats={"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0},
            truncated_trace_fraction=2.5,   # out of range
            provenance={},
        )
        c = canonicalize(g)
        assert c.truncated_trace_fraction == pytest.approx(1.0)

    def test_canonicalize_marks_provenance(self):
        g = self._make_genome()
        c = canonicalize(g)
        assert c.provenance.get("canonicalized") is True

    def test_canonicalize_recomputes_hot_path_signature(self):
        """Removing zero counts must produce a consistent HPS."""
        g = ExecutionGenome(
            coverage_vector=[],
            function_call_counts={"foo": 3, "dead": 0},
            instruction_type_histogram={"call": 3, "return": 3, "line": 5, "exception": 0},
            hot_path_signature="stale_signature",
            trace_length_stats={"mean": 1.0, "std": 0.0, "min": 1.0, "max": 1.0},
            truncated_trace_fraction=0.0,
            provenance={},
        )
        c = canonicalize(g)
        # The recomputed signature must not be the stale one.
        from sbg.extraction.dynamic.tracer import _hot_path_signature
        expected = _hot_path_signature({"foo": 3})
        assert c.hot_path_signature == expected
