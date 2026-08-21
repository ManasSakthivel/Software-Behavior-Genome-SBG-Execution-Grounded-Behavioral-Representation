"""
tests for sbg.distance and sbg.canonicalization
=================================================
20+ deterministic tests covering:

  * behavioral_distance with all 8 dimensions present
  * behavioral_distance with a subset of dimensions
  * distance(g, g) == 0 for every dimension
  * DEFAULT_WEIGHTS sum to 1.0
  * total_distance is always in [0, 1]
  * canonicalize_all is idempotent
  * missing dimensions are tracked correctly
  * custom weight vectors are renormalised
  * dimensions= filter parameter
  * behavioral_distance is symmetric
"""

from __future__ import annotations

import pytest

from sbg.distance import behavioral_distance, DEFAULT_WEIGHTS, _DISTANCE_FNS
from sbg.canonicalization import canonicalize, canonicalize_all, GENOME_REGISTRY

# ---- genome imports ----
from sbg.extraction.static.extractor import ControlGenome
from sbg.extraction.static.data_genome import DataGenome
from sbg.extraction.static.error_genome import ErrorGenome
from sbg.extraction.dynamic.tracer import ExecutionGenome
from sbg.extraction.dynamic.state_genome import StateGenome
from sbg.extraction.dynamic.resource_genome import ResourceGenome
from sbg.extraction.dynamic.temporal_genome import TemporalGenome
from sbg.extraction.dynamic.interaction_genome import InteractionGenome


# ---------------------------------------------------------------------------
# Helpers — build minimal "zero" genome instances for each dimension
# ---------------------------------------------------------------------------

def _zero_control() -> ControlGenome:
    return ControlGenome(
        branch_probability_profile={},
        call_graph_edges=[],
        loop_nesting_profile=[],
        cyclomatic_complexity=1,
        control_flow_entropy=0.0,
        provenance={},
    )


def _zero_data() -> DataGenome:
    from dataclasses import fields as _fields
    # Build with all-zero/empty values using field defaults where possible
    kw = {}
    for f in _fields(DataGenome):
        if f.name == "provenance":
            kw[f.name] = {}
        elif f.type in ("Dict[str, int]", "Dict[str, float]"):
            kw[f.name] = {}
        elif f.type == "float":
            kw[f.name] = 0.0
        else:
            kw[f.name] = {}
    try:
        return DataGenome(**kw)
    except TypeError:
        return DataGenome(
            value_type_histogram={}, constant_value_profile={},
            container_usage={}, arithmetic_op_histogram={},
            comparison_op_histogram={}, data_flow_complexity=0.0,
            provenance={},
        )


def _zero_error() -> ErrorGenome:
    return ErrorGenome(
        exception_types_raised=[], exception_types_caught=[],
        bare_except_count=0, try_block_count=0, finally_block_count=0,
        assertion_count=0, error_propagation_pattern="none",
        error_coverage_score=0.0, provenance={},
    )


def _zero_execution() -> ExecutionGenome:
    return ExecutionGenome(
        coverage_vector=[],
        function_call_counts={},
        instruction_type_histogram={},
        hot_path_signature="",
        trace_length_stats={"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0},
        truncated_trace_fraction=0.0,
        provenance={},
    )


def _zero_state() -> StateGenome:
    return StateGenome(
        variable_assignment_counts={}, state_space_size=0,
        mutation_rate=0.0, heap_object_types={},
        stack_depth_profile={}, state_transition_count=0,
        provenance={},
    )


def _zero_resource() -> ResourceGenome:
    _stats = {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    return ResourceGenome(
        execution_time_ms_stats=dict(_stats),
        trace_length_stats=dict(_stats),
        function_call_total=0,
        exception_rate=0.0,
        avg_local_var_count=0.0,
        provenance={},
    )


def _zero_temporal() -> TemporalGenome:
    return TemporalGenome(
        call_return_latency_profile={},
        event_sequence_ngrams={},
        phase_timing={},
        temporal_entropy=0.0,
        provenance={},
    )


def _zero_interaction() -> InteractionGenome:
    return InteractionGenome(
        output_value_types={},
        output_value_histogram={},
        function_call_patterns=[],
        io_pattern_signature="0" * 16,
        n_distinct_outputs=0,
        provenance={},
    )


def _full_zero_genome() -> dict:
    return {
        "CONTROL": _zero_control(),
        "DATA": _zero_data(),
        "STATE": _zero_state(),
        "RESOURCE": _zero_resource(),
        "TEMPORAL": _zero_temporal(),
        "ERROR": _zero_error(),
        "INTERACTION": _zero_interaction(),
        "EXECUTION": _zero_execution(),
    }


def _non_zero_control() -> ControlGenome:
    return ControlGenome(
        branch_probability_profile={"If": 0.5, "For": 0.5},
        call_graph_edges=[("main", "helper")],
        loop_nesting_profile=[0, 2],
        cyclomatic_complexity=3,
        control_flow_entropy=1.0,
        provenance={},
    )


def _non_zero_interaction() -> InteractionGenome:
    from sbg.extraction.dynamic.interaction_genome import _io_pattern_signature
    h = {"positive_int": 5}
    return InteractionGenome(
        output_value_types={"int": 5},
        output_value_histogram=h,
        function_call_patterns=["main|helper"],
        io_pattern_signature=_io_pattern_signature(h),
        n_distinct_outputs=1,
        provenance={},
    )


# ---------------------------------------------------------------------------
# 1. DEFAULT_WEIGHTS sanity checks
# ---------------------------------------------------------------------------

class TestDefaultWeights:
    def test_weights_sum_to_one(self):
        total = sum(DEFAULT_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_all_dimensions_covered(self):
        expected = {"CONTROL", "DATA", "STATE", "RESOURCE",
                    "TEMPORAL", "ERROR", "INTERACTION", "EXECUTION"}
        assert set(DEFAULT_WEIGHTS.keys()) == expected

    def test_all_weights_non_negative(self):
        for dim, w in DEFAULT_WEIGHTS.items():
            assert w >= 0.0, f"Weight for {dim} is negative"


# ---------------------------------------------------------------------------
# 2. distance(g, g) == 0 for every dimension
# ---------------------------------------------------------------------------

class TestSelfDistance:
    def test_control_self_distance(self):
        from sbg.extraction.static.extractor import distance as d
        g = _zero_control()
        assert d(g, g) == 0.0

    def test_data_self_distance(self):
        from sbg.extraction.static.data_genome import distance as d
        g = _zero_data()
        assert d(g, g) == 0.0

    def test_error_self_distance(self):
        from sbg.extraction.static.error_genome import distance as d
        g = _zero_error()
        assert d(g, g) == 0.0

    def test_execution_self_distance(self):
        from sbg.extraction.dynamic.tracer import distance as d
        g = _zero_execution()
        assert d(g, g) == 0.0

    def test_state_self_distance(self):
        from sbg.extraction.dynamic.state_genome import distance as d
        g = _zero_state()
        assert d(g, g) == 0.0

    def test_resource_self_distance(self):
        from sbg.extraction.dynamic.resource_genome import distance as d
        g = _zero_resource()
        assert d(g, g) == 0.0

    def test_temporal_self_distance(self):
        from sbg.extraction.dynamic.temporal_genome import distance as d
        g = _zero_temporal()
        assert d(g, g) == 0.0

    def test_interaction_self_distance(self):
        from sbg.extraction.dynamic.interaction_genome import distance as d
        g = _zero_interaction()
        assert d(g, g) == 0.0


# ---------------------------------------------------------------------------
# 3. behavioral_distance — all dimensions present
# ---------------------------------------------------------------------------

class TestBehavioralDistanceAllDimensions:
    def test_identical_genomes_distance_zero(self):
        genome = _full_zero_genome()
        result = behavioral_distance(genome, genome)
        assert result["total_distance"] == 0.0

    def test_total_distance_in_range(self):
        ga = _full_zero_genome()
        gb = _full_zero_genome()
        gb["CONTROL"] = _non_zero_control()
        gb["INTERACTION"] = _non_zero_interaction()
        result = behavioral_distance(ga, gb)
        assert 0.0 <= result["total_distance"] <= 1.0

    def test_returns_all_required_keys(self):
        genome = _full_zero_genome()
        result = behavioral_distance(genome, genome)
        assert "total_distance" in result
        assert "dimension_distances" in result
        assert "dimensions_used" in result
        assert "weights_used" in result
        assert "missing_dimensions" in result

    def test_all_dimensions_used_when_all_present(self):
        genome = _full_zero_genome()
        result = behavioral_distance(genome, genome)
        assert len(result["dimensions_used"]) == 8

    def test_no_missing_dimensions_when_all_present(self):
        genome = _full_zero_genome()
        result = behavioral_distance(genome, genome)
        assert result["missing_dimensions"] == []

    def test_symmetric(self):
        ga = _full_zero_genome()
        gb = _full_zero_genome()
        gb["CONTROL"] = _non_zero_control()
        r1 = behavioral_distance(ga, gb)
        r2 = behavioral_distance(gb, ga)
        assert abs(r1["total_distance"] - r2["total_distance"]) < 1e-10

    def test_dimension_distances_in_range(self):
        ga = _full_zero_genome()
        gb = _full_zero_genome()
        gb["CONTROL"] = _non_zero_control()
        result = behavioral_distance(ga, gb)
        for dim, d in result["dimension_distances"].items():
            assert 0.0 <= d <= 1.0, f"Dimension {dim} distance {d} out of [0,1]"

    def test_weights_used_sum_to_one(self):
        genome = _full_zero_genome()
        result = behavioral_distance(genome, genome)
        w_sum = sum(result["weights_used"].values())
        assert abs(w_sum - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# 4. behavioral_distance — subset of dimensions
# ---------------------------------------------------------------------------

class TestBehavioralDistanceSubset:
    def test_subset_dimensions_parameter(self):
        ga = _full_zero_genome()
        gb = _full_zero_genome()
        result = behavioral_distance(ga, gb, dimensions=["CONTROL", "DATA"])
        assert set(result["dimensions_used"]) == {"CONTROL", "DATA"}

    def test_subset_missing_dimensions_tracked(self):
        ga = {"CONTROL": _zero_control()}
        gb = {"CONTROL": _zero_control()}
        result = behavioral_distance(ga, gb)
        # All 8 default weight keys are present; 7 are missing from the genomes
        assert len(result["missing_dimensions"]) == 7

    def test_one_dimension_result_is_that_dimension_distance(self):
        from sbg.extraction.static.extractor import distance as d_ctrl
        g_zero = _zero_control()
        g_nonzero = _non_zero_control()
        expected = d_ctrl(g_zero, g_nonzero)

        ga = {"CONTROL": g_zero}
        gb = {"CONTROL": g_nonzero}
        weights = {"CONTROL": 1.0}
        result = behavioral_distance(ga, gb, weights=weights, dimensions=["CONTROL"])
        assert abs(result["total_distance"] - expected) < 1e-10

    def test_empty_genome_dicts_returns_zero(self):
        result = behavioral_distance({}, {})
        assert result["total_distance"] == 0.0

    def test_total_distance_nonzero_when_different(self):
        ga = {"CONTROL": _zero_control(), "DATA": _zero_data()}
        gb = {"CONTROL": _non_zero_control(), "DATA": _zero_data()}
        weights = {"CONTROL": 0.5, "DATA": 0.5}
        result = behavioral_distance(ga, gb, weights=weights)
        assert result["total_distance"] > 0.0


# ---------------------------------------------------------------------------
# 5. canonicalize_all is idempotent
# ---------------------------------------------------------------------------

class TestCanonicalizeAll:
    def test_canonicalize_all_returns_same_keys(self):
        genome = _full_zero_genome()
        result = canonicalize_all(genome)
        assert set(result.keys()) == set(genome.keys())

    def test_canonicalize_all_idempotent_types(self):
        genome = _full_zero_genome()
        c1 = canonicalize_all(genome)
        c2 = canonicalize_all(c1)
        for dim in c1:
            # Check types match
            assert type(c1[dim]) is type(c2[dim])

    def test_canonicalize_all_idempotent_content(self):
        from sbg.extraction.dynamic.interaction_genome import _io_pattern_signature
        h = {"positive_int": 5, "None": 0}  # has zero entry that should be cleaned
        genome = {
            "INTERACTION": InteractionGenome(
                output_value_types={"int": 5, "float": 0},
                output_value_histogram=h,
                function_call_patterns=["a|b", "a|b"],
                io_pattern_signature="bad",
                n_distinct_outputs=99,
            )
        }
        c1 = canonicalize_all(genome)
        c2 = canonicalize_all(c1)
        g1 = c1["INTERACTION"]
        g2 = c2["INTERACTION"]
        assert g1.output_value_types == g2.output_value_types
        assert g1.output_value_histogram == g2.output_value_histogram
        assert g1.function_call_patterns == g2.function_call_patterns
        assert g1.io_pattern_signature == g2.io_pattern_signature

    def test_canonicalize_all_unknown_key_passthrough(self):
        genome = {"UNKNOWN": "raw_value"}
        result = canonicalize_all(genome)
        assert result["UNKNOWN"] == "raw_value"

    def test_canonicalize_all_empty_dict(self):
        result = canonicalize_all({})
        assert result == {}


# ---------------------------------------------------------------------------
# 6. canonicalize single-dispatch
# ---------------------------------------------------------------------------

class TestCanonicalizeSingleDispatch:
    def test_dispatches_correctly_for_each_type(self):
        for dim, (cls, canon_fn) in GENOME_REGISTRY.items():
            if dim == "CONTROL":
                g = _zero_control()
            elif dim == "DATA":
                g = _zero_data()
            elif dim == "ERROR":
                g = _zero_error()
            elif dim == "EXECUTION":
                g = _zero_execution()
            elif dim == "STATE":
                g = _zero_state()
            elif dim == "RESOURCE":
                g = _zero_resource()
            elif dim == "TEMPORAL":
                g = _zero_temporal()
            elif dim == "INTERACTION":
                g = _zero_interaction()
            else:
                continue
            result = canonicalize(g)
            assert isinstance(result, cls), f"canonicalize({dim}) returned wrong type"

    def test_raises_type_error_for_unknown(self):
        with pytest.raises(TypeError):
            canonicalize("not a genome")
