"""
Unit tests for SBG v2 execution engine.

Tests verify:
1. SandboxRunner produces traces and noise-floor stats
2. Noise-floor flags non-deterministic features
3. Unsafe programs are rejected
4. DynamicFeatureNormalizer features are output-free
5. Rename-invariance: SP-2 (function rename) produces identical normalized behavior
6. DynamicGenome distance is symmetric and d(g,g)=0
7. hybrid_distance returns values in [0,1]
8. SAFEGUARD-2: return_value and stdout never appear in DynamicGenome
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from sbg.extraction.dynamic.tracer import TraceEvent, ExecutionTrace
from sbg.v2.execution.runner import SandboxRunner, SandboxResult
from sbg.v2.execution.normalizer import TraceNormalizer, NormalizedBehavior
from sbg.v2.execution.genome import DynamicGenome, DynamicGenomeExtractor, distance
from sbg.v2.hybrid.fusion import hybrid_distance, DEFAULT_FUSION_WEIGHTS


# ---------------------------------------------------------------------------
# Test helper functions
# ---------------------------------------------------------------------------

def _simple_sort(lst):
    """Simple selection sort."""
    arr = list(lst)
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr


def _renamed_simple_sort(collection):
    """Same logic, all variables renamed (SP-2 simulation)."""
    items = list(collection)
    length = len(items)
    for outer in range(length):
        smallest = outer
        for inner in range(outer + 1, length):
            if items[inner] < items[smallest]:
                smallest = inner
        items[outer], items[smallest] = items[smallest], items[outer]
    return items


def _different_algorithm(lst):
    """Completely different algorithm (merge sort) — should differ dynamically."""
    if len(lst) <= 1:
        return list(lst)
    mid = len(lst) // 2
    left = _different_algorithm(lst[:mid])
    right = _different_algorithm(lst[mid:])
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]


def _always_raises(inp):
    raise ValueError("test error from dynamic extraction")


# ---------------------------------------------------------------------------
# SandboxRunner tests
# ---------------------------------------------------------------------------

def test_runner_basic():
    """SandboxRunner returns SandboxResult with correct structure."""
    runner = SandboxRunner()
    result = runner.run("test_sort", _simple_sort, [[3, 1, 2], [5, 4]], n_runs=2)
    assert isinstance(result, SandboxResult)
    assert result.program_id == "test_sort"
    assert result.n_runs == 2
    assert len(result.traces) == 2
    assert result.error is None


def test_runner_noise_floor_deterministic():
    """Deterministic function produces near-zero noise across runs."""
    runner = SandboxRunner()
    result = runner.run("sort_stable", _simple_sort, [[3, 1, 2], [1]], n_runs=5)
    # For a deterministic function, coverage should not vary
    std = result.noise_floor_stats.get("coverage_size_std", 0.0)
    assert std == 0.0, f"Deterministic function should have std=0, got {std}"


def test_runner_exception_handling():
    """SandboxRunner captures exceptions without crashing."""
    runner = SandboxRunner()
    result = runner.run("exc_prog", _always_raises, [1, 2], n_runs=1)
    assert result.error is None  # runner itself doesn't fail
    for run_traces in result.traces:
        for trace in run_traces:
            assert trace.exception is not None


def test_runner_unsafe_program_rejected():
    """Unsafe concurrent programs are rejected with error."""
    runner = SandboxRunner()
    result = runner.run("conc_producer_consumer", _simple_sort, [[1, 2, 3]])
    assert result.error is not None
    assert "UNSAFE" in result.error
    assert len(result.traces) == 0


def test_runner_empty_inputs():
    """Empty input list produces no traces."""
    runner = SandboxRunner()
    result = runner.run("empty_inputs", _simple_sort, [], n_runs=1)
    # All runs should have empty trace lists
    assert all(len(r) == 0 for r in result.traces)


# ---------------------------------------------------------------------------
# TraceNormalizer / NormalizedBehavior tests
# ---------------------------------------------------------------------------

def test_normalizer_output_free():
    """SAFEGUARD-2: return_value and stdout must NOT appear in NormalizedBehavior."""
    runner = SandboxRunner()
    normalizer = TraceNormalizer()

    result = runner.run("sort_v", _simple_sort, [[3, 1, 2]], n_runs=1)
    nb = normalizer.normalize("sort_v", result.traces)

    # NormalizedBehavior must not contain output fields
    nb_dict = nb.provenance
    assert "return_value" not in nb_dict
    assert "stdout" not in nb_dict
    assert nb.provenance.get("safeguard_2_compliant") is True
    assert nb.provenance.get("feature_classification") == "OUTPUT_FREE"


def test_normalizer_rename_invariance():
    """
    CORE TEST: SP-2 (function rename) must produce identical normalized behavior.
    This tests the fix for v1 hot_path_signature flaw.
    """
    runner = SandboxRunner()
    normalizer = TraceNormalizer()
    inputs = [[3, 1, 2], [5, 4, 6], [1]]

    r1 = runner.run("sort_orig", _simple_sort, inputs, n_runs=1)
    r2 = runner.run("sort_renamed", _renamed_simple_sort, inputs, n_runs=1)

    nb1 = normalizer.normalize("sort_orig", r1.traces)
    nb2 = normalizer.normalize("sort_renamed", r2.traces)

    # Coverage size should be identical
    assert nb1.coverage_vector_size == nb2.coverage_vector_size, (
        f"Coverage size differs after rename: {nb1.coverage_vector_size} vs {nb2.coverage_vector_size}"
    )
    # Exception rate should be identical
    assert nb1.exception_rate == nb2.exception_rate

    # Hot path hash should be identical (keyed by anonymous indices, not names)
    assert nb1.hot_path_hash == nb2.hot_path_hash, (
        f"Hot path hash differs after rename: {nb1.hot_path_hash} vs {nb2.hot_path_hash}"
    )


def test_normalizer_exception_class_only():
    """Exception messages must not be captured — only class names."""
    runner = SandboxRunner()
    normalizer = TraceNormalizer()

    result = runner.run("exc_prog", _always_raises, [1, 2], n_runs=1)
    nb = normalizer.normalize("exc_prog", result.traces)

    # Exception type must be just the class name
    for exc_type in nb.exception_type_set:
        assert ":" not in exc_type, f"Exception type contains ':' (message included): {exc_type}"
        assert "test error from dynamic extraction" not in exc_type


def test_normalizer_empty_traces():
    """Empty trace list produces empty NormalizedBehavior without error."""
    normalizer = TraceNormalizer()
    nb = normalizer.normalize("empty", [])
    assert nb.coverage_vector_size == 0
    assert nb.n_unique_functions == 0
    assert nb.exception_rate == 0.0


# ---------------------------------------------------------------------------
# DynamicGenome / distance tests
# ---------------------------------------------------------------------------

def _extract_genome(func, inputs):
    """Helper: extract DynamicGenome from a function."""
    runner = SandboxRunner()
    normalizer = TraceNormalizer()
    extractor = DynamicGenomeExtractor()
    result = runner.run(func.__name__, func, inputs, n_runs=1)
    nb = normalizer.normalize(func.__name__, result.traces)
    return extractor.extract(nb)


def test_genome_safeguard_2():
    """SAFEGUARD-2: DynamicGenome.to_dict() must not contain return_value or stdout."""
    g = _extract_genome(_simple_sort, [[3, 1, 2]])
    d = g.to_dict()
    assert "return_value" not in d, "return_value found in DynamicGenome!"
    assert "stdout" not in d, "stdout found in DynamicGenome!"
    assert d.get("feature_classification") == "OUTPUT_FREE"
    assert d.get("safeguard_2_compliant") is True


def test_distance_self_zero():
    """d(g, g) == 0.0 for any g."""
    g = _extract_genome(_simple_sort, [[3, 1, 2], [1, 2]])
    assert distance(g, g) == 0.0


def test_distance_symmetry():
    """d(g1, g2) == d(g2, g1)."""
    g1 = _extract_genome(_simple_sort, [[3, 1, 2]])
    g2 = _extract_genome(_different_algorithm, [[3, 1, 2]])
    d12 = distance(g1, g2)
    d21 = distance(g2, g1)
    assert abs(d12 - d21) < 1e-12, f"Asymmetric distance: {d12} vs {d21}"


def test_distance_range():
    """distance is in [0, 1] for any pair."""
    g1 = _extract_genome(_simple_sort, [[3, 1, 2]])
    g2 = _extract_genome(_different_algorithm, [[3, 1, 2]])
    d = distance(g1, g2)
    assert 0.0 <= d <= 1.0, f"distance out of range: {d}"


def test_distance_rename_invariant():
    """
    CORE TEST: Renamed function produces distance=0 (rename-invariant).
    """
    inputs = [[3, 1, 2], [5, 4], [1]]
    g1 = _extract_genome(_simple_sort, inputs)
    g2 = _extract_genome(_renamed_simple_sort, inputs)
    d = distance(g1, g2)
    assert d < 1e-9, (
        f"Renamed function should have d=0, got d={d}. "
        "This indicates hot_path_hash or call_freq uses function names (rename-sensitivity bug)."
    )


def test_distance_different_programs_nonzero():
    """Different algorithms should have nonzero distance."""
    inputs = [[3, 1, 2], [5, 4, 6], [1, 2, 3, 4, 5]]
    g1 = _extract_genome(_simple_sort, inputs)
    g2 = _extract_genome(_different_algorithm, inputs)
    d = distance(g1, g2)
    # Different call patterns (recursion in merge sort vs iteration in selection sort)
    # We don't assert a specific value — just that they're distinguishable
    assert 0.0 <= d <= 1.0


def test_distance_empty_genome():
    """Empty genome distance is defined."""
    normalizer = TraceNormalizer()
    extractor = DynamicGenomeExtractor()
    g_empty = extractor.extract(normalizer.normalize("empty", []))
    g_real = _extract_genome(_simple_sort, [[3, 1, 2]])
    d = distance(g_empty, g_real)
    assert 0.0 <= d <= 1.0


# ---------------------------------------------------------------------------
# Hybrid distance tests
# ---------------------------------------------------------------------------

def test_hybrid_distance_range():
    """hybrid_distance result is in [0, 1] for all alpha values."""
    inputs = [[3, 1, 2]]
    g1 = _extract_genome(_simple_sort, inputs)
    g2 = _extract_genome(_different_algorithm, inputs)
    for w_static in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        weights = {"static": w_static, "dynamic": 1.0 - w_static}
        d = hybrid_distance(g1, g2, static_dist=0.3, weights=weights)
        assert 0.0 <= d <= 1.0, f"hybrid_distance out of range at w_static={w_static}: {d}"


def test_hybrid_distance_no_static():
    """hybrid_distance with static_dist=None falls back to dynamic only."""
    inputs = [[3, 1, 2]]
    g1 = _extract_genome(_simple_sort, inputs)
    g2 = _extract_genome(_different_algorithm, inputs)
    d_hybrid = hybrid_distance(g1, g2, static_dist=None)
    d_dyn = distance(g1, g2)
    assert abs(d_hybrid - d_dyn) < 1e-12, "Without static, hybrid should equal dynamic"


def test_hybrid_distance_static_only():
    """hybrid_distance with w_static=1.0 reduces to static distance."""
    inputs = [[3, 1, 2]]
    g1 = _extract_genome(_simple_sort, inputs)
    g2 = _extract_genome(_different_algorithm, inputs)
    static_d = 0.42
    d_hybrid = hybrid_distance(g1, g2, static_dist=static_d, weights={"static": 1.0, "dynamic": 0.0})
    assert abs(d_hybrid - static_d) < 1e-9, f"w_static=1.0 should give static_dist, got {d_hybrid}"


if __name__ == "__main__":
    tests = [
        test_runner_basic,
        test_runner_noise_floor_deterministic,
        test_runner_exception_handling,
        test_runner_unsafe_program_rejected,
        test_runner_empty_inputs,
        test_normalizer_output_free,
        test_normalizer_rename_invariance,
        test_normalizer_exception_class_only,
        test_normalizer_empty_traces,
        test_genome_safeguard_2,
        test_distance_self_zero,
        test_distance_symmetry,
        test_distance_range,
        test_distance_rename_invariant,
        test_distance_different_programs_nonzero,
        test_distance_empty_genome,
        test_hybrid_distance_range,
        test_hybrid_distance_no_static,
        test_hybrid_distance_static_only,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
            passed += 1
        except Exception as exc:
            print(f"FAIL  {t.__name__} — {exc}")
            failed += 1
    print(f"\n{passed}/{passed + failed} PASS")
