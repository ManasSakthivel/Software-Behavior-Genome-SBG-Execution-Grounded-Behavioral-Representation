"""Unit tests for TraceNormalizer."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent.parent))

from sbg.v2.execution.runner import SandboxRunner
from sbg.v2.execution.normalizer import TraceNormalizer, NormalizedBehavior


def _bubble_sort(lst):
    arr = list(lst)
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def _renamed_bubble_sort(lst):
    """Same logic, different local var names."""
    items = list(lst)
    length = len(items)
    for outer in range(length):
        for inner in range(length - outer - 1):
            if items[inner] > items[inner + 1]:
                items[inner], items[inner + 1] = items[inner + 1], items[inner]
    return items


def test_normalizer_basic():
    runner = SandboxRunner()
    normalizer = TraceNormalizer()
    inputs = [[3, 1, 2], [5, 4, 6]]

    r1 = runner.run("sort1", _bubble_sort, inputs, n_runs=1)
    nb1 = normalizer.normalize("sort1", r1.traces)

    assert isinstance(nb1, NormalizedBehavior)
    assert nb1.coverage_vector_size > 0
    assert nb1.n_unique_functions > 0


def test_normalizer_rename_invariance():
    """SP-1/SP-2 (rename) should produce identical normalized behavior."""
    runner = SandboxRunner()
    normalizer = TraceNormalizer()
    inputs = [[3, 1, 2], [5, 4]]

    r1 = runner.run("sort_orig", _bubble_sort, inputs, n_runs=1)
    r2 = runner.run("sort_renamed", _renamed_bubble_sort, inputs, n_runs=1)

    nb1 = normalizer.normalize("sort_orig", r1.traces)
    nb2 = normalizer.normalize("sort_renamed", r2.traces)

    # Coverage size should be same (same lines executed)
    assert nb1.coverage_vector_size == nb2.coverage_vector_size
    # Exception rate should be same
    assert nb1.exception_rate == nb2.exception_rate


def test_normalizer_empty():
    normalizer = TraceNormalizer()
    nb = normalizer.normalize("empty", [])
    assert nb.coverage_vector_size == 0
    assert nb.n_unique_functions == 0
