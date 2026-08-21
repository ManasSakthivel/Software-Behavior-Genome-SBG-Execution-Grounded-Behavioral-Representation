"""
sbg/extraction/dynamic/test_state_genome.py
=============================================
Tests for StateGenome, StateGenomeExtractor, distance(), and canonicalize().

Run with:
    python3 -m pytest sbg/extraction/dynamic/test_state_genome.py -v
"""

from __future__ import annotations
import unittest
from typing import Dict, List

from sbg.extraction.dynamic.tracer import ExecutionTrace, TraceEvent, Tracer
from sbg.extraction.dynamic.state_genome import (
    StateGenome, StateGenomeExtractor, canonicalize, distance,
)

_extractor = StateGenomeExtractor()
_tracer = Tracer()


# ---------------------------------------------------------------------------
# Helpers — synthetic traces
# ---------------------------------------------------------------------------

def _ev(event_type="line", function_name="f", lineno=1, locals_=None, ts=0):
    return TraceEvent(
        event_type=event_type,
        function_name=function_name,
        lineno=lineno,
        local_vars_snapshot=locals_ or {},
        timestamp_ns=ts,
    )


def _trace(events, program_id="test"):
    coverage = {e.lineno for e in events}
    return ExecutionTrace(
        program_id=program_id,
        input_repr="<test>",
        events=events,
        return_value=None,
        exception=None,
        stdout="",
        execution_time_ms=0.0,
        coverage=coverage,
    )


def _genome(**kwargs):
    defaults = dict(
        variable_assignment_counts={},
        state_space_size=0,
        mutation_rate=0.0,
        heap_object_types={},
        stack_depth_profile={},
        state_transition_count=0,
        provenance={},
    )
    defaults.update(kwargs)
    return StateGenome(**defaults)


# ---------------------------------------------------------------------------
# Trace fixtures
# ---------------------------------------------------------------------------

def _traces_counter():
    events = [
        _ev("call",   "count", 1, {"x": "0"}, 1000),
        _ev("line",   "count", 2, {"x": "1"}, 2000),
        _ev("line",   "count", 3, {"x": "2"}, 3000),
        _ev("return", "count", 4, {"x": "2"}, 4000),
    ]
    return [_trace(events, "counter")]


def _traces_strings():
    events = [
        _ev("call",   "greet", 1, {"name": "'Alice'", "msg": "''"}, 1000),
        _ev("line",   "greet", 2, {"name": "'Alice'", "msg": "'Hello Alice'"}, 2000),
        _ev("return", "greet", 3, {"name": "'Alice'", "msg": "'Hello Alice'"}, 3000),
    ]
    return [_trace(events, "greeter")]


def _traces_lists():
    events = [
        _ev("call",   "build", 1, {"lst": "[]"},       1000),
        _ev("line",   "build", 2, {"lst": "[1]"},       2000),
        _ev("line",   "build", 3, {"lst": "[1, 2]"},    3000),
        _ev("return", "build", 4, {"lst": "[1, 2, 3]"}, 4000),
    ]
    return [_trace(events, "list_builder")]


def _traces_nested():
    events = [
        _ev("call",   "outer", 1, {"a": "1"}, 1000),
        _ev("call",   "inner", 5, {"b": "2"}, 2000),
        _ev("return", "inner", 7, {"b": "4"}, 3000),
        _ev("return", "outer", 3, {"a": "1"}, 4000),
    ]
    return [_trace(events, "nested")]


def _traces_counter_copy():
    events = [
        _ev("call",   "count", 1, {"x": "0"}, 1000),
        _ev("line",   "count", 2, {"x": "1"}, 2000),
        _ev("line",   "count", 3, {"x": "2"}, 3000),
        _ev("return", "count", 4, {"x": "2"}, 4000),
    ]
    return [_trace(events, "counter2")]


# ---------------------------------------------------------------------------
# Live-traced fixtures
# ---------------------------------------------------------------------------

def _live_add(n=5):
    def add_loop(limit):
        total = 0
        for i in range(limit):
            total += i
        return total
    return _tracer.trace(add_loop, [n])


def _live_fib(n=5):
    def fib(n):
        if n <= 1:
            return n
        return fib(n - 1) + fib(n - 2)
    return _tracer.trace(fib, [n])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStateGenomeExtractorBasic(unittest.TestCase):

    def test_returns_state_genome(self):
        self.assertIsInstance(_extractor.extract(_traces_counter()), StateGenome)

    def test_empty_traces_returns_genome(self):
        self.assertIsInstance(_extractor.extract([]), StateGenome)

    def test_no_events_trace_returns_genome(self):
        self.assertIsInstance(_extractor.extract([_trace([], "empty")]), StateGenome)

    def test_variable_counts_present(self):
        g = _extractor.extract(_traces_counter())
        self.assertIn("x", g.variable_assignment_counts)
        self.assertGreater(g.variable_assignment_counts["x"], 0)

    def test_string_type_in_heap_types(self):
        g = _extractor.extract(_traces_strings())
        self.assertIn("str", g.heap_object_types)

    def test_list_type_in_heap_types(self):
        g = _extractor.extract(_traces_lists())
        self.assertIn("list", g.heap_object_types)

    def test_state_space_size_positive(self):
        g = _extractor.extract(_traces_counter())
        self.assertGreater(g.state_space_size, 0)

    def test_mutation_rate_in_range(self):
        g = _extractor.extract(_traces_counter())
        self.assertGreaterEqual(g.mutation_rate, 0.0)
        self.assertLessEqual(g.mutation_rate, 1.0)

    def test_mutation_rate_nonzero_for_changing_state(self):
        g = _extractor.extract(_traces_counter())
        self.assertGreater(g.mutation_rate, 0.0)

    def test_state_transition_count_nonneg(self):
        g = _extractor.extract(_traces_counter())
        self.assertGreaterEqual(g.state_transition_count, 0)

    def test_stack_depth_keys_nonneg(self):
        g = _extractor.extract(_traces_counter())
        for depth in g.stack_depth_profile:
            self.assertGreaterEqual(depth, 0)

    def test_provenance_n_traces(self):
        g = _extractor.extract(_traces_counter())
        self.assertEqual(g.provenance["n_traces"], 1)

    def test_nested_calls_deeper_stack(self):
        g_flat = _extractor.extract(_traces_counter())
        g_nested = _extractor.extract(_traces_nested())
        max_flat = max(g_flat.stack_depth_profile.keys(), default=0)
        max_nested = max(g_nested.stack_depth_profile.keys(), default=0)
        self.assertGreaterEqual(max_nested, max_flat)


class TestStateGenomeExtractorLive(unittest.TestCase):

    def test_live_add_loop_extracts(self):
        self.assertIsInstance(_extractor.extract(_live_add()), StateGenome)

    def test_live_fib_extracts(self):
        self.assertIsInstance(_extractor.extract(_live_fib()), StateGenome)

    def test_live_fib_has_stack_profile(self):
        g = _extractor.extract(_live_fib())
        self.assertGreater(len(g.stack_depth_profile), 0)

    def test_live_fib_mutation_rate_in_range(self):
        g = _extractor.extract(_live_fib())
        self.assertGreaterEqual(g.mutation_rate, 0.0)
        self.assertLessEqual(g.mutation_rate, 1.0)


class TestStateGenomeDistance(unittest.TestCase):

    def test_distance_self_zero(self):
        g = _extractor.extract(_traces_counter())
        self.assertAlmostEqual(distance(g, g), 0.0, places=10)

    def test_distance_symmetric(self):
        g1 = _extractor.extract(_traces_counter())
        g2 = _extractor.extract(_traces_strings())
        self.assertAlmostEqual(distance(g1, g2), distance(g2, g1), places=10)

    def test_distance_in_range(self):
        g1 = _extractor.extract(_traces_counter())
        g2 = _extractor.extract(_traces_strings())
        d = distance(g1, g2)
        self.assertGreaterEqual(d, 0.0)
        self.assertLessEqual(d, 1.0)

    def test_distance_empty_self_zero(self):
        g = _extractor.extract([])
        self.assertAlmostEqual(distance(g, g), 0.0, places=10)

    def test_distance_default_genomes_zero(self):
        g1 = _genome()
        g2 = _genome()
        self.assertAlmostEqual(distance(g1, g2), 0.0, places=10)

    def test_distance_identical_traces_near_zero(self):
        g1 = _extractor.extract(_traces_counter())
        g2 = _extractor.extract(_traces_counter_copy())
        d = distance(g1, g2)
        self.assertLess(d, 0.2, "Expected d < 0.2, got {:.4f}".format(d))

    def test_distance_different_heap_types(self):
        g1 = _extractor.extract(_traces_counter())
        g2 = _extractor.extract(_traces_strings())
        self.assertGreater(distance(g1, g2), 0.0)

    def test_semantics_preserving_small_distance(self):
        def prog_a(x):
            result = 0
            for i in range(x):
                result += i
            return result

        def prog_b(n):
            total = 0
            for j in range(n):
                total += j
            return total

        ga = _extractor.extract(_tracer.trace(prog_a, [4]))
        gb = _extractor.extract(_tracer.trace(prog_b, [4]))
        d = distance(ga, gb)
        self.assertLess(d, 0.2, "Expected d < 0.2, got {:.4f}".format(d))

    def test_distance_extreme_manual(self):
        g_low = _genome(mutation_rate=0.0, stack_depth_profile={0: 100},
                        heap_object_types={"int": 10})
        g_high = _genome(mutation_rate=1.0, stack_depth_profile={10: 100},
                         heap_object_types={"str": 10, "list": 5})
        d = distance(g_low, g_high)
        self.assertGreaterEqual(d, 0.0)
        self.assertLessEqual(d, 1.0)

    def test_counter_vs_list_in_range(self):
        g1 = _extractor.extract(_traces_counter())
        g2 = _extractor.extract(_traces_lists())
        d = distance(g1, g2)
        self.assertGreaterEqual(d, 0.0)
        self.assertLessEqual(d, 1.0)


class TestStateGenomeCanonicalize(unittest.TestCase):

    def test_returns_state_genome(self):
        g = _extractor.extract(_traces_counter())
        self.assertIsInstance(canonicalize(g), StateGenome)

    def test_idempotent(self):
        g = _extractor.extract(_traces_nested())
        c1 = canonicalize(g)
        c2 = canonicalize(c1)
        self.assertEqual(c1.variable_assignment_counts, c2.variable_assignment_counts)
        self.assertEqual(c1.state_space_size, c2.state_space_size)
        self.assertAlmostEqual(c1.mutation_rate, c2.mutation_rate, places=10)
        self.assertEqual(c1.heap_object_types, c2.heap_object_types)
        self.assertEqual(c1.stack_depth_profile, c2.stack_depth_profile)
        self.assertEqual(c1.state_transition_count, c2.state_transition_count)

    def test_sorts_var_keys(self):
        g = _genome(variable_assignment_counts={"z": 3, "a": 1, "m": 2})
        c = canonicalize(g)
        self.assertEqual(list(c.variable_assignment_counts.keys()), ["a", "m", "z"])

    def test_sorts_heap_type_keys(self):
        g = _genome(heap_object_types={"str": 2, "int": 5, "list": 1})
        c = canonicalize(g)
        self.assertEqual(list(c.heap_object_types.keys()), ["int", "list", "str"])

    def test_sorts_stack_depth_keys(self):
        g = _genome(stack_depth_profile={3: 5, 1: 10, 2: 7})
        c = canonicalize(g)
        self.assertEqual(list(c.stack_depth_profile.keys()), [1, 2, 3])

    def test_rounds_mutation_rate(self):
        g = _genome(mutation_rate=0.123456789)
        c = canonicalize(g)
        self.assertAlmostEqual(c.mutation_rate, round(0.123456789, 4), places=10)

    def test_clamps_mutation_rate_high(self):
        c = canonicalize(_genome(mutation_rate=1.5))
        self.assertLessEqual(c.mutation_rate, 1.0)

    def test_clamps_mutation_rate_low(self):
        c = canonicalize(_genome(mutation_rate=-0.3))
        self.assertGreaterEqual(c.mutation_rate, 0.0)

    def test_marks_provenance(self):
        g = _extractor.extract(_traces_counter())
        c = canonicalize(g)
        self.assertTrue(c.provenance.get("canonicalized"))

    def test_distance_self_zero_after_canonicalize(self):
        g = _extractor.extract(_traces_counter())
        c = canonicalize(g)
        self.assertAlmostEqual(distance(c, c), 0.0, places=10)


if __name__ == "__main__":
    unittest.main()
