"""Unit tests for DynamicGenomeExtractor and distance."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent.parent))

from sbg.v2.execution.runner import SandboxRunner
from sbg.v2.execution.normalizer import TraceNormalizer
from sbg.v2.execution.genome import DynamicGenomeExtractor, DynamicGenome, distance


def _mergesort(lst):
    if len(lst) <= 1:
        return lst
    mid = len(lst) // 2
    left = _mergesort(lst[:mid])
    right = _mergesort(lst[mid:])
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]


def _linear_search(lst):
    """Completely different algorithm: linear search for max."""
    if not lst:
        return None
    best = lst[0]
    for x in lst:
        if x > best:
            best = x
    return best


def test_extract_basic():
    runner = SandboxRunner()
    normalizer = TraceNormalizer()
    extractor = DynamicGenomeExtractor()
    inputs = [[3, 1, 2], [5, 4, 6, 1]]

    r = runner.run("mergesort", _mergesort, inputs, n_runs=1)
    nb = normalizer.normalize("mergesort", r.traces)
    g = extractor.extract(nb)

    assert isinstance(g, DynamicGenome)
    assert g.coverage_size > 0
    assert 0.0 <= g.coverage_consistency <= 1.0
    assert 0.0 <= g.exception_rate <= 1.0


def test_distance_self_zero():
    runner = SandboxRunner()
    normalizer = TraceNormalizer()
    extractor = DynamicGenomeExtractor()
    inputs = [[3, 1, 2]]

    r = runner.run("mergesort", _mergesort, inputs, n_runs=1)
    nb = normalizer.normalize("mergesort", r.traces)
    g = extractor.extract(nb)

    assert distance(g, g) == 0.0


def test_distance_different_programs():
    runner = SandboxRunner()
    normalizer = TraceNormalizer()
    extractor = DynamicGenomeExtractor()
    inputs = [[3, 1, 2], [5, 4]]

    r1 = runner.run("mergesort", _mergesort, inputs, n_runs=1)
    r2 = runner.run("linsearch", _linear_search, inputs, n_runs=1)

    nb1 = normalizer.normalize("mergesort", r1.traces)
    nb2 = normalizer.normalize("linsearch", r2.traces)

    g1 = extractor.extract(nb1)
    g2 = extractor.extract(nb2)

    d = distance(g1, g2)
    assert 0.0 <= d <= 1.0
    # Different programs should have nonzero distance
    assert d > 0.0


def test_distance_in_bounds():
    from sbg.v2.execution.genome import DynamicGenome
    g1 = DynamicGenome("a", 100, 0.9, {0: 0.5, 1: 0.5}, "abc", [], 0.0, 3.0, 5.0, 20.0, 2.0, 2)
    g2 = DynamicGenome("b", 50, 0.5, {0: 0.3, 2: 0.7}, "def", ["ValueError"], 0.1, 2.0, 4.0, 15.0, 3.0, 3)
    d = distance(g1, g2)
    assert 0.0 <= d <= 1.0
