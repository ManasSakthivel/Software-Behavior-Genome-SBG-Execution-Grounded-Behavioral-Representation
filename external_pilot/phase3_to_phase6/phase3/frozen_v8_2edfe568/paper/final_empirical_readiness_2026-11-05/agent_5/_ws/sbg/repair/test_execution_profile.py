"""
tests for sbg.repair.execution_profile

Covers:
- Unit tests for each component
- Output-leakage adversarial tests (Phase 7)
- Determinism tests
- Edge-case tests
- Regression tests
"""
from __future__ import annotations

import sys
import os

# Ensure repo root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from sbg.repair.execution_profile import (
    ExecutionProfileExtractor,
    ExecutionProfile,
    compute_eep_distance,
    _trace_length_distance,
    _line_seq_divergence,
    _run_and_collect,
)


# ---------------------------------------------------------------------------
# Helper programs for testing
# ---------------------------------------------------------------------------

def _double(x):
    return x * 2


def _double_renamed(lst):
    return lst * 2


def _sum_range_correct(n):
    s = 0
    for i in range(1, n + 1):
        s += i
    return s


def _sum_range_buggy(n):
    s = 0
    for i in range(n):   # BUG: off-by-one
        s += i
    return s


def _loop_with_break_correct(lst, target):
    for i, x in enumerate(lst):
        if x == target:
            return i
    return -1


def _loop_missing_break_buggy(lst, target):
    result = -1
    for i, x in enumerate(lst):
        if x == target:
            result = i  # BUG: no break, finds last
    return result


def _fib_mutable_buggy(n, memo={}):   # noqa: B006
    if n <= 1:
        return n
    if n in memo:
        return memo[n]
    memo[n] = _fib_mutable_buggy(n - 1) + _fib_mutable_buggy(n - 2)
    return memo[n]


def _fib_correct(n, memo=None):
    if memo is None:
        memo = {}
    if n <= 1:
        return n
    if n in memo:
        return memo[n]
    memo[n] = _fib_correct(n - 1, memo) + _fib_correct(n - 2, memo)
    return memo[n]


def _reverse_correct(lst):
    result = []
    i = len(lst) - 1
    while i >= 0:
        result.append(lst[i])
        i -= 1
    return result


def _reverse_buggy(lst):
    result = []
    i = len(lst) - 1
    while i > 0:   # BUG: off-by-one, misses first element
        result.append(lst[i])
        i -= 1
    return result


# Program that computes different OUTPUT but has IDENTICAL control flow
def _compute_x_plus_1(x):
    return x + 1


def _compute_x_plus_2(x):
    return x + 2  # Different output, SAME control flow


# ===========================================================================
# PHASE 7 — OUTPUT LEAKAGE ADVERSARIAL TESTS
# ===========================================================================

class TestOutputLeakage:
    """
    Phase 7: Adversarial output-leakage tests.

    REQUIREMENT: Programs with identical execution structure but different
    return values MUST produce identical EEP distances (or near-zero).
    """

    def test_OL1_identical_control_flow_different_return(self):
        """
        OL-1: Programs differing only in returned value with IDENTICAL control flow
        must produce d_eep ≈ 0.
        """
        extractor = ExecutionProfileExtractor()
        inputs = [1, 2, 5, 10]

        pa = extractor.extract(_compute_x_plus_1, inputs)
        pb = extractor.extract(_compute_x_plus_2, inputs)

        # Trace lengths MUST be identical — same number of events
        assert pa.trace_lengths == pb.trace_lengths, (
            f"LEAKAGE: trace lengths differ for identical-structure programs: "
            f"{pa.trace_lengths} vs {pb.trace_lengths}"
        )

        # Line sequence hashes MUST be identical
        assert pa.line_seq_hashes == pb.line_seq_hashes, (
            f"LEAKAGE: line hashes differ for identical-structure programs"
        )

        # EEP distance must be near zero (only possible difference: exception fraction)
        d = compute_eep_distance(pa, pb)
        assert d < 0.01, (
            f"LEAKAGE: EEP distance {d:.4f} > 0.01 for programs differing only in return value"
        )

    def test_OL2_sorting_direction_same_structure(self):
        """
        OL-2: sorted(lst) vs sorted(lst, reverse=True) — same control structure,
        different output. Must be close to 0 in structure-only features.
        """
        def sort_asc(lst):
            return sorted(lst)

        def sort_desc(lst):
            return sorted(lst, reverse=True)

        extractor = ExecutionProfileExtractor()
        inputs = [[3, 1, 2], [5, 4], [1]]

        pa = extractor.extract(sort_asc, inputs)
        pb = extractor.extract(sort_desc, inputs)

        # Trace lengths should be identical
        assert pa.trace_lengths == pb.trace_lengths, (
            f"LEAKAGE: trace lengths differ: {pa.trace_lengths} vs {pb.trace_lengths}"
        )

        d = compute_eep_distance(pa, pb)
        assert d < 0.05, f"LEAKAGE: distance {d:.4f} too large for same-structure sort"

    def test_OL3_arithmetic_mutation_no_branch_change(self):
        """
        OL-3: `x * 2` vs `x * 3` — different output, same control flow.
        """
        def mult2(x): return x * 2
        def mult3(x): return x * 3

        extractor = ExecutionProfileExtractor()
        inputs = [1, 2, 3, 4, 5]

        pa = extractor.extract(mult2, inputs)
        pb = extractor.extract(mult3, inputs)

        assert pa.trace_lengths == pb.trace_lengths
        assert pa.line_seq_hashes == pb.line_seq_hashes

        d = compute_eep_distance(pa, pb)
        assert d < 0.01, f"LEAKAGE: d={d:.4f} for pure arithmetic mutation"

    def test_OL4_trace_length_does_not_encode_return_value(self):
        """
        OL-4: Verify trace length is independent of return value.
        """
        events1, _ = _run_and_collect(_compute_x_plus_1, 5)
        events2, _ = _run_and_collect(_compute_x_plus_2, 5)

        assert len(events1) == len(events2), (
            f"LEAKAGE: event counts differ ({len(events1)} vs {len(events2)}) "
            f"for programs with identical structure"
        )

    def test_OL5_exception_features_unchanged_for_value_mutation(self):
        """
        OL-5: A mutation that changes return value but not exception behavior
        must leave exception features unchanged.
        """
        def returns_none(x):
            return None  # No exception

        def returns_zero(x):
            return 0  # No exception, different value

        extractor = ExecutionProfileExtractor()
        inputs = [1, 2, 3]

        pa = extractor.extract(returns_none, inputs)
        pb = extractor.extract(returns_zero, inputs)

        assert pa.exception_fraction() == pb.exception_fraction() == 0.0
        assert pa.exception_type_set() == pb.exception_type_set() == set()


# ===========================================================================
# UNIT TESTS — individual components
# ===========================================================================

class TestTraceCapture:
    """Tests for _run_and_collect."""

    def test_captures_events(self):
        events, exc = _run_and_collect(_double, 5)
        assert len(events) > 0
        assert exc is None

    def test_captures_exception(self):
        def raises(x):
            raise ValueError("test error")

        events, exc = _run_and_collect(raises, 1)
        assert exc == "ValueError"

    def test_deterministic(self):
        events1, _ = _run_and_collect(_double, 5)
        events2, _ = _run_and_collect(_double, 5)
        assert len(events1) == len(events2)

    def test_timeout_returns_empty(self):
        def slow(x):
            time_start = __import__("time").time()
            while __import__("time").time() - time_start < 10:
                pass

        events, exc = _run_and_collect(slow, 1, timeout_s=0.1)
        assert exc == "TimeoutError"


class TestTraceLengthDistance:
    """Tests for _trace_length_distance."""

    def test_identical_vectors_zero_distance(self):
        d = _trace_length_distance([10, 20, 30], [10, 20, 30])
        assert d == 0.0

    def test_different_vectors_positive_distance(self):
        d = _trace_length_distance([10, 20, 30], [5, 15, 25])
        assert d > 0.0

    def test_empty_vectors_zero_distance(self):
        d = _trace_length_distance([], [])
        assert d == 0.0

    def test_distance_in_range(self):
        d = _trace_length_distance([100], [1])
        assert 0.0 <= d <= 1.0

    def test_symmetric(self):
        a, b = [10, 20], [5, 30]
        assert _trace_length_distance(a, b) == _trace_length_distance(b, a)


class TestLineSeqDivergence:
    """Tests for _line_seq_divergence."""

    def test_identical_hashes_zero(self):
        d = _line_seq_divergence(["abc", "def"], ["abc", "def"])
        assert d == 0.0

    def test_all_different_one(self):
        d = _line_seq_divergence(["abc", "def"], ["xyz", "uvw"])
        assert d == 1.0

    def test_half_different(self):
        d = _line_seq_divergence(["abc", "def"], ["abc", "uvw"])
        assert abs(d - 0.5) < 1e-9

    def test_empty_zero(self):
        d = _line_seq_divergence([], [])
        assert d == 0.0

    def test_symmetric(self):
        a, b = ["abc", "def"], ["abc", "uvw"]
        assert _line_seq_divergence(a, b) == _line_seq_divergence(b, a)


class TestExecutionProfileExtractor:
    """Tests for ExecutionProfileExtractor."""

    def test_extract_basic(self):
        extractor = ExecutionProfileExtractor()
        profile = extractor.extract(_double, [1, 2, 3])

        assert profile.n_inputs == 3
        assert len(profile.trace_lengths) == 3
        assert len(profile.line_seq_hashes) == 3
        assert all(tl > 0 for tl in profile.trace_lengths)

    def test_identical_program_zero_distance(self):
        extractor = ExecutionProfileExtractor()
        inputs = [1, 2, 5]

        pa = extractor.extract(_double, inputs)
        pb = extractor.extract(_double, inputs)

        d = compute_eep_distance(pa, pb)
        assert d == 0.0, f"Self-distance should be 0, got {d}"

    def test_deterministic_extraction(self):
        extractor = ExecutionProfileExtractor()
        inputs = [3, 5, 7]

        pa1 = extractor.extract(_sum_range_correct, inputs)
        pa2 = extractor.extract(_sum_range_correct, inputs)

        assert pa1.trace_lengths == pa2.trace_lengths
        assert pa1.line_seq_hashes == pa2.line_seq_hashes


class TestEEPSensitivity:
    """Tests that EEP detects known regressions."""

    def test_off_by_one_value_only_not_detected(self):
        """
        SCIENTIFIC FINDING: range(n) vs range(1, n+1) — identical iteration count.
        This is a PURE VALUE MUTATION (same loop count, different loop variable).
        EEP correctly returns near-zero: output-free guarantee confirmed.
        This is a correct True Negative for the EEP system.
        """
        extractor = ExecutionProfileExtractor()
        inputs = [5, 10, 3]

        pa = extractor.extract(_sum_range_correct, inputs)
        pb = extractor.extract(_sum_range_buggy, inputs)

        # Trace lengths are identical — same iteration count for all n
        assert pa.trace_lengths == pb.trace_lengths, (
            "Unexpected: trace lengths differ for pure-value loop mutation"
        )
        d = compute_eep_distance(pa, pb)
        # Should be near-zero: control flow is identical
        assert d < 0.05, f"Unexpected distance {d:.4f} for pure-value mutation"

    def test_detects_off_by_one_iteration_count(self):
        """
        Off-by-one that changes ITERATION COUNT is detected.
        _reverse_buggy uses i > 0 vs i >= 0 — one fewer iteration.
        Trace length is shorter → EEP detects it.
        """
        extractor = ExecutionProfileExtractor()
        inputs = [[1, 2, 3, 4], [1, 2, 3], [5, 6]]

        pa = extractor.extract(_reverse_correct, inputs)
        pb = extractor.extract(_reverse_buggy, inputs)

        d = compute_eep_distance(pa, pb)
        assert d > 0.05, (
            f"EEP distance {d:.4f} too small for off-by-one iteration count "
            f"(trace lengths: {pa.trace_lengths} vs {pb.trace_lengths})"
        )

    def test_detects_missing_break(self):
        """Missing break runs loop to completion instead of early exit."""
        extractor = ExecutionProfileExtractor()
        # Tuple inputs are auto-unpacked: fn(*inp)
        inputs = [
            ([1, 2, 3, 4, 5], 2),  # target at index 1
            ([1, 2, 3, 4, 5], 4),  # target at index 3
        ]

        pa = extractor.extract(_loop_with_break_correct, inputs)
        pb = extractor.extract(_loop_missing_break_buggy, inputs)

        d = compute_eep_distance(pa, pb)
        assert d > 0.05, (
            f"EEP distance {d:.4f} too small for missing-break bug "
            f"(trace lengths: {pa.trace_lengths} vs {pb.trace_lengths})"
        )

    def test_detects_reverse_off_by_one(self):
        """Reverse with i>0 vs i>=0 misses first element — loop runs N-1 vs N times."""
        extractor = ExecutionProfileExtractor()
        inputs = [[1, 2, 3, 4], [1, 2, 3], [5, 6]]

        pa = extractor.extract(_reverse_correct, inputs)
        pb = extractor.extract(_reverse_buggy, inputs)

        d = compute_eep_distance(pa, pb)
        # Buggy runs one fewer loop iteration → shorter trace
        assert d > 0.05, (
            f"EEP distance {d:.4f} too small for reverse off-by-one "
            f"(trace lengths: {pa.trace_lengths} vs {pb.trace_lengths})"
        )


class TestRobustness:
    """Robustness tests for EEP."""

    def test_rename_invariance(self):
        """Renaming variables should not change structural distance meaningfully."""
        def fn_a(lst):
            result = []
            for element in lst:
                result.append(element * 2)
            return result

        def fn_b(lst):
            output = []
            for item in lst:   # renamed variable
                output.append(item * 2)
            return output

        extractor = ExecutionProfileExtractor()
        inputs = [[1, 2, 3], [4, 5], []]

        pa = extractor.extract(fn_a, inputs)
        pb = extractor.extract(fn_b, inputs)

        # Trace lengths must be identical
        assert pa.trace_lengths == pb.trace_lengths, (
            f"Rename sensitivity: trace lengths differ {pa.trace_lengths} vs {pb.trace_lengths}"
        )

    def test_empty_input_no_crash(self):
        """Empty input list should not crash."""
        extractor = ExecutionProfileExtractor()
        pa = extractor.extract(_double, [])
        pb = extractor.extract(_double, [])
        d = compute_eep_distance(pa, pb)
        assert d == 0.0

    def test_exception_program(self):
        """Programs that always raise should produce zero distance against themselves."""
        def always_raises(x):
            raise ValueError("always")

        extractor = ExecutionProfileExtractor()
        pa = extractor.extract(always_raises, [1, 2])
        pb = extractor.extract(always_raises, [1, 2])

        d = compute_eep_distance(pa, pb)
        assert d == 0.0


# ===========================================================================
# Run tests if executed directly
# ===========================================================================

if __name__ == "__main__":
    import traceback

    test_classes = [
        TestOutputLeakage,
        TestTraceCapture,
        TestTraceLengthDistance,
        TestLineSeqDivergence,
        TestExecutionProfileExtractor,
        TestEEPSensitivity,
        TestRobustness,
    ]

    total_pass = 0
    total_fail = 0
    failures = []

    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        print(f"\n[{cls.__name__}]")
        for method in methods:
            try:
                getattr(instance, method)()
                print(f"  PASS  {method}")
                total_pass += 1
            except Exception as e:
                print(f"  FAIL  {method}: {e}")
                failures.append((cls.__name__, method, str(e)))
                total_fail += 1

    print(f"\n{'='*60}")
    print(f"RESULTS: {total_pass} passed, {total_fail} failed")
    if failures:
        print("\nFAILURES:")
        for cls_name, method, err in failures:
            print(f"  {cls_name}.{method}: {err}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
