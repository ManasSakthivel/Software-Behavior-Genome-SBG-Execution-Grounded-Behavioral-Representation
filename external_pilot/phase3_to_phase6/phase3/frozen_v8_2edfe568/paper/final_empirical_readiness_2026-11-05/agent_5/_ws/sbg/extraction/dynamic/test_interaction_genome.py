"""
tests for sbg.extraction.dynamic.interaction_genome
=====================================================
15+ deterministic tests covering:
  * InteractionGenomeExtractor.extract (empty traces, single trace, multi-trace)
  * _classify_value (all value-shape categories)
  * _extract_call_sequence
  * _io_pattern_signature
  * distance (identity, symmetry, range, distinct genomes)
  * canonicalize (idempotency, cleaning, signature recomputation)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from sbg.extraction.dynamic.interaction_genome import (
    InteractionGenome,
    InteractionGenomeExtractor,
    _classify_value,
    _extract_call_sequence,
    _io_pattern_signature,
    _jsd,
    _jaccard_patterns,
    canonicalize,
    distance,
)
from sbg.extraction.dynamic.tracer import ExecutionTrace, TraceEvent


# ---------------------------------------------------------------------------
# Helpers — minimal ExecutionTrace factories
# ---------------------------------------------------------------------------

def _make_event(event_type: str, function_name: str) -> TraceEvent:
    return TraceEvent(
        event_type=event_type,
        function_name=function_name,
        lineno=1,
        local_vars_snapshot={},
        timestamp_ns=0,
    )


def _make_trace(
    return_value: Any = None,
    exception: Optional[str] = None,
    events: Optional[List[TraceEvent]] = None,
    program_id: str = "prog",
) -> ExecutionTrace:
    return ExecutionTrace(
        program_id=program_id,
        input_repr="<input>",
        events=events or [],
        return_value=return_value,
        exception=exception,
        stdout="",
        execution_time_ms=1.0,
        coverage=set(),
        truncated=False,
    )


# ---------------------------------------------------------------------------
# 1. _classify_value
# ---------------------------------------------------------------------------

class TestClassifyValue:
    def test_exception_takes_priority(self):
        assert _classify_value(42, "SomeError: oops") == "exception"

    def test_none_value(self):
        assert _classify_value(None, None) == "None"

    def test_true_value(self):
        assert _classify_value(True, None) == "True"

    def test_false_value(self):
        assert _classify_value(False, None) == "False"

    def test_zero_int(self):
        assert _classify_value(0, None) == "zero"

    def test_zero_float(self):
        assert _classify_value(0.0, None) == "zero"

    def test_positive_int(self):
        assert _classify_value(7, None) == "positive_int"

    def test_negative_int(self):
        assert _classify_value(-3, None) == "negative_int"

    def test_negative_float(self):
        assert _classify_value(-1.5, None) == "negative_int"

    def test_empty_str(self):
        assert _classify_value("", None) == "empty_str"

    def test_nonempty_str(self):
        assert _classify_value("hello", None) == "nonempty_str"

    def test_list_value(self):
        assert _classify_value([1, 2], None) == "list"

    def test_dict_value(self):
        assert _classify_value({"a": 1}, None) == "dict"

    def test_unknown_type_uses_type_name(self):
        class Foo:
            pass
        result = _classify_value(Foo(), None)
        assert result == "Foo"


# ---------------------------------------------------------------------------
# 2. _extract_call_sequence
# ---------------------------------------------------------------------------

class TestExtractCallSequence:
    def test_empty_events(self):
        assert _extract_call_sequence([]) == ""

    def test_single_call_event(self):
        events = [_make_event("call", "main")]
        assert _extract_call_sequence(events) == "main"

    def test_only_call_events_selected(self):
        events = [
            _make_event("call", "foo"),
            _make_event("line", "foo"),
            _make_event("call", "bar"),
            _make_event("return", "bar"),
        ]
        assert _extract_call_sequence(events) == "foo|bar"

    def test_sequence_order_preserved(self):
        events = [
            _make_event("call", "a"),
            _make_event("call", "b"),
            _make_event("call", "c"),
        ]
        assert _extract_call_sequence(events) == "a|b|c"


# ---------------------------------------------------------------------------
# 3. _io_pattern_signature
# ---------------------------------------------------------------------------

class TestIoPatternSignature:
    def test_empty_histogram(self):
        sig = _io_pattern_signature({})
        assert isinstance(sig, str)
        assert len(sig) == 16

    def test_deterministic(self):
        h = {"positive_int": 3, "None": 1}
        assert _io_pattern_signature(h) == _io_pattern_signature(h)

    def test_zero_counts_excluded(self):
        h1 = {"positive_int": 3}
        h2 = {"positive_int": 3, "None": 0}
        assert _io_pattern_signature(h1) == _io_pattern_signature(h2)

    def test_order_independent(self):
        h1 = {"a": 1, "b": 2}
        h2 = {"b": 2, "a": 1}
        assert _io_pattern_signature(h1) == _io_pattern_signature(h2)


# ---------------------------------------------------------------------------
# 4. InteractionGenomeExtractor.extract
# ---------------------------------------------------------------------------

class TestInteractionGenomeExtractorEmpty:
    def test_empty_traces_returns_genome(self):
        extractor = InteractionGenomeExtractor()
        g = extractor.extract([])
        assert isinstance(g, InteractionGenome)
        assert g.n_distinct_outputs == 0
        assert g.output_value_types == {}
        assert g.output_value_histogram == {}
        assert g.function_call_patterns == []

    def test_empty_traces_signature_is_string(self):
        g = InteractionGenomeExtractor().extract([])
        assert isinstance(g.io_pattern_signature, str)
        assert len(g.io_pattern_signature) == 16


class TestInteractionGenomeExtractorSingleTrace:
    def test_single_int_return(self):
        traces = [_make_trace(return_value=42)]
        g = InteractionGenomeExtractor().extract(traces)
        assert "int" in g.output_value_types
        assert g.output_value_types["int"] == 1
        assert "positive_int" in g.output_value_histogram
        assert g.n_distinct_outputs == 1

    def test_exception_trace_classified(self):
        traces = [_make_trace(return_value=None, exception="ValueError: bad")]
        g = InteractionGenomeExtractor().extract(traces)
        assert "exception" in g.output_value_histogram

    def test_call_sequence_extracted(self):
        events = [
            _make_event("call", "main"),
            _make_event("call", "helper"),
        ]
        traces = [_make_trace(events=events, return_value=1)]
        g = InteractionGenomeExtractor().extract(traces)
        assert len(g.function_call_patterns) == 1
        assert g.function_call_patterns[0] == "main|helper"

    def test_provenance_n_traces(self):
        traces = [_make_trace(return_value=None)]
        g = InteractionGenomeExtractor().extract(traces)
        assert g.provenance["n_traces"] == 1


class TestInteractionGenomeExtractorMultiTrace:
    def test_multi_trace_histogram_accumulates(self):
        traces = [
            _make_trace(return_value=1),
            _make_trace(return_value=2),
            _make_trace(return_value=None),
        ]
        g = InteractionGenomeExtractor().extract(traces)
        assert g.output_value_histogram.get("positive_int", 0) == 2
        assert g.output_value_histogram.get("None", 0) == 1

    def test_top10_patterns_capped(self):
        # 15 distinct sequences → should cap at 10
        traces = []
        for i in range(15):
            events = [_make_event("call", f"fn_{i}")]
            traces.append(_make_trace(events=events, return_value=i))
        g = InteractionGenomeExtractor().extract(traces)
        assert len(g.function_call_patterns) <= 10

    def test_n_distinct_outputs_counts_types(self):
        traces = [
            _make_trace(return_value=1),       # int
            _make_trace(return_value="hello"),  # str
            _make_trace(return_value=None),     # NoneType
        ]
        g = InteractionGenomeExtractor().extract(traces)
        assert g.n_distinct_outputs == 3


# ---------------------------------------------------------------------------
# 5. distance
# ---------------------------------------------------------------------------

class TestDistance:
    def _genome(
        self,
        histogram: Dict[str, int] = None,
        patterns: List[str] = None,
    ) -> InteractionGenome:
        hist = histogram or {}
        pats = patterns or []
        return InteractionGenome(
            output_value_types={},
            output_value_histogram=hist,
            function_call_patterns=pats,
            io_pattern_signature=_io_pattern_signature(hist),
            n_distinct_outputs=0,
        )

    def test_identity(self):
        g = self._genome({"positive_int": 5}, ["main|helper"])
        assert distance(g, g) == 0.0

    def test_empty_genomes_identity(self):
        g = self._genome()
        assert distance(g, g) == 0.0

    def test_symmetry(self):
        g1 = self._genome({"positive_int": 5}, ["a|b"])
        g2 = self._genome({"None": 3}, ["x|y"])
        assert abs(distance(g1, g2) - distance(g2, g1)) < 1e-10

    def test_range_zero_to_one(self):
        g1 = self._genome({"positive_int": 10}, ["a|b"])
        g2 = self._genome({"None": 10}, ["c|d"])
        d = distance(g1, g2)
        assert 0.0 <= d <= 1.0

    def test_different_histograms_nonzero(self):
        g1 = self._genome({"positive_int": 10})
        g2 = self._genome({"None": 10})
        assert distance(g1, g2) > 0.0

    def test_same_histogram_different_patterns(self):
        g1 = self._genome({"positive_int": 5}, ["a|b"])
        g2 = self._genome({"positive_int": 5}, ["c|d"])
        # JSD part = 0, Jaccard part = 1 → distance = 0.5
        assert abs(distance(g1, g2) - 0.5) < 1e-6

    def test_max_distance_fully_distinct(self):
        g1 = self._genome({"positive_int": 10}, ["a|b"])
        g2 = self._genome({"None": 10}, ["c|d"])
        d = distance(g1, g2)
        assert d > 0.0


# ---------------------------------------------------------------------------
# 6. canonicalize
# ---------------------------------------------------------------------------

class TestCanonicalize:
    def _raw_genome(self) -> InteractionGenome:
        return InteractionGenome(
            output_value_types={"int": 3, "NoneType": 0},  # zero entry to clean
            output_value_histogram={"positive_int": 2, "None": -1},  # negative to clean
            function_call_patterns=["a|b", "a|b", "c|d"],  # duplicate to dedup
            io_pattern_signature="badhash000000000",  # wrong; should be recomputed
            n_distinct_outputs=99,  # wrong; should be recomputed
            provenance={"n_traces": 1},
        )

    def test_zero_type_removed(self):
        g = self._raw_genome()
        c = canonicalize(g)
        assert "NoneType" not in c.output_value_types

    def test_negative_histogram_entry_removed(self):
        g = self._raw_genome()
        c = canonicalize(g)
        assert "None" not in c.output_value_histogram

    def test_duplicate_patterns_deduplicated(self):
        g = self._raw_genome()
        c = canonicalize(g)
        assert c.function_call_patterns.count("a|b") == 1

    def test_signature_recomputed(self):
        g = self._raw_genome()
        c = canonicalize(g)
        expected_sig = _io_pattern_signature(c.output_value_histogram)
        assert c.io_pattern_signature == expected_sig

    def test_n_distinct_recomputed(self):
        g = self._raw_genome()
        c = canonicalize(g)
        assert c.n_distinct_outputs == len(c.output_value_types)

    def test_provenance_gains_canonicalized_marker(self):
        g = self._raw_genome()
        c = canonicalize(g)
        assert c.provenance.get("canonicalized") is True

    def test_idempotent(self):
        g = self._raw_genome()
        c1 = canonicalize(g)
        c2 = canonicalize(c1)
        assert c1.output_value_types == c2.output_value_types
        assert c1.output_value_histogram == c2.output_value_histogram
        assert c1.function_call_patterns == c2.function_call_patterns
        assert c1.io_pattern_signature == c2.io_pattern_signature
        assert c1.n_distinct_outputs == c2.n_distinct_outputs

    def test_keys_sorted(self):
        g = InteractionGenome(
            output_value_types={"z_type": 1, "a_type": 2},
            output_value_histogram={"z_cat": 3, "a_cat": 1},
            function_call_patterns=[],
            io_pattern_signature="",
            n_distinct_outputs=2,
        )
        c = canonicalize(g)
        assert list(c.output_value_types.keys()) == sorted(c.output_value_types.keys())
        assert list(c.output_value_histogram.keys()) == sorted(c.output_value_histogram.keys())

    def test_patterns_capped_at_ten(self):
        patterns = [f"fn_{i}" for i in range(20)]
        g = InteractionGenome(
            output_value_types={},
            output_value_histogram={},
            function_call_patterns=patterns,
            io_pattern_signature="",
            n_distinct_outputs=0,
        )
        c = canonicalize(g)
        assert len(c.function_call_patterns) <= 10
