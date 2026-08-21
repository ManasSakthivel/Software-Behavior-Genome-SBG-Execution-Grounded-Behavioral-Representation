"""
sbg/v2/test_static_proxy.py
============================
Unit tests for sbg.v2.static_proxy.

Coverage
--------
- Identical programs return distance ≈ 0 (and similarity ≈ 1)
- Distance is in [0, 1]
- Distance is symmetric: d(a, b) == d(b, a)
- None is returned gracefully on invalid / nonexistent input
- v1_behavioral_similarity == 1 - v1_behavioral_distance
"""

from __future__ import annotations

import pathlib
import tempfile
import textwrap
import unittest

from sbg.v2.static_proxy import v1_behavioral_distance, v1_behavioral_similarity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_source(directory: pathlib.Path, name: str, source: str) -> str:
    """Write *source* to *directory/name* and return the absolute path string."""
    p = directory / name
    p.write_text(textwrap.dedent(source), encoding="utf-8")
    return str(p)


# Minimal Python programs used across tests
_SIMPLE_A = """\
    def main(x):
        if x > 0:
            return x * 2
        return 0
"""

_SIMPLE_B = """\
    def main(x):
        for i in range(x):
            pass
        return x
"""

_EMPTY = ""

_INVALID_PYTHON = "def this is not valid python !!!"


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestIdentical(unittest.TestCase):
    """Identical programs should return near-zero distance."""

    def test_identical_distance_is_near_zero(self):
        """
        Two files with identical source content should yield distance close
        to 0.  It will not be exactly 0 because dynamic dimensions (e.g.
        RESOURCE, TEMPORAL) record wall-clock timing that varies between
        independent trace runs.  We assert distance < 0.10 as a generous but
        meaningful upper bound.

        The exact-zero case is tested by test_same_path_twice, where the
        genome cache guarantees a single extraction object compared to itself.
        """
        with tempfile.TemporaryDirectory() as d:
            dp = pathlib.Path(d)
            path_a = _write_source(dp, "a.py", _SIMPLE_A)
            path_b = _write_source(dp, "b.py", _SIMPLE_A)  # same content, different path

            dist = v1_behavioral_distance(path_a, path_b)
            self.assertIsNotNone(dist, "Expected a float, got None for identical programs")
            self.assertLess(dist, 0.10,
                            msg=f"Identical source programs should have near-zero distance, got {dist}")

    def test_identical_similarity_is_near_one(self):
        with tempfile.TemporaryDirectory() as d:
            dp = pathlib.Path(d)
            path_a = _write_source(dp, "a.py", _SIMPLE_A)
            path_b = _write_source(dp, "b.py", _SIMPLE_A)

            sim = v1_behavioral_similarity(path_a, path_b)
            self.assertIsNotNone(sim)
            self.assertGreater(sim, 0.90,
                               msg=f"Identical source programs should have near-one similarity, got {sim}")

    def test_same_path_twice(self):
        """
        Passing the same physical path twice must return distance exactly 0.
        The genome cache returns the same object for both lookups; the CONTROL,
        DATA, ERROR static distance functions all satisfy d(g, g) == 0, and
        dynamic functions also satisfy d(g, g) == 0 when given the same object.
        """
        with tempfile.TemporaryDirectory() as d:
            dp = pathlib.Path(d)
            path = _write_source(dp, "a.py", _SIMPLE_A)

            dist = v1_behavioral_distance(path, path)
            self.assertIsNotNone(dist)
            self.assertAlmostEqual(dist, 0.0, places=6)


class TestRange(unittest.TestCase):
    """Distance must be a float in [0, 1]."""

    def test_distance_in_unit_interval(self):
        with tempfile.TemporaryDirectory() as d:
            dp = pathlib.Path(d)
            path_a = _write_source(dp, "a.py", _SIMPLE_A)
            path_b = _write_source(dp, "b.py", _SIMPLE_B)

            dist = v1_behavioral_distance(path_a, path_b)
            self.assertIsNotNone(dist)
            self.assertGreaterEqual(dist, 0.0)
            self.assertLessEqual(dist, 1.0)

    def test_similarity_in_unit_interval(self):
        with tempfile.TemporaryDirectory() as d:
            dp = pathlib.Path(d)
            path_a = _write_source(dp, "a.py", _SIMPLE_A)
            path_b = _write_source(dp, "b.py", _SIMPLE_B)

            sim = v1_behavioral_similarity(path_a, path_b)
            self.assertIsNotNone(sim)
            self.assertGreaterEqual(sim, 0.0)
            self.assertLessEqual(sim, 1.0)


class TestSymmetry(unittest.TestCase):
    """Distance must be symmetric: d(a, b) == d(b, a)."""

    def test_symmetric_different_programs(self):
        with tempfile.TemporaryDirectory() as d:
            dp = pathlib.Path(d)
            path_a = _write_source(dp, "a.py", _SIMPLE_A)
            path_b = _write_source(dp, "b.py", _SIMPLE_B)

            d_ab = v1_behavioral_distance(path_a, path_b)
            d_ba = v1_behavioral_distance(path_b, path_a)

            self.assertIsNotNone(d_ab)
            self.assertIsNotNone(d_ba)
            self.assertAlmostEqual(d_ab, d_ba, places=9,
                                   msg=f"Distance not symmetric: d(a,b)={d_ab} d(b,a)={d_ba}")

    def test_symmetric_identical_programs(self):
        with tempfile.TemporaryDirectory() as d:
            dp = pathlib.Path(d)
            path_a = _write_source(dp, "a.py", _SIMPLE_A)
            path_b = _write_source(dp, "b.py", _SIMPLE_A)

            d_ab = v1_behavioral_distance(path_a, path_b)
            d_ba = v1_behavioral_distance(path_b, path_a)
            self.assertEqual(d_ab, d_ba)


class TestGracefulFailure(unittest.TestCase):
    """None must be returned on all failure modes — never a sentinel float."""

    def test_nonexistent_path_a(self):
        dist = v1_behavioral_distance("/does/not/exist/a.py", "/does/not/exist/b.py")
        self.assertIsNone(dist, "Expected None for nonexistent path, got a float")

    def test_nonexistent_path_b(self):
        with tempfile.TemporaryDirectory() as d:
            dp = pathlib.Path(d)
            path_a = _write_source(dp, "a.py", _SIMPLE_A)
            dist = v1_behavioral_distance(path_a, "/does/not/exist/b.py")
            self.assertIsNone(dist)

    def test_invalid_python_returns_none_or_partial(self):
        """
        Invalid Python may still return a float if at least one static
        dimension fails but distance returns 0 (no active dims).
        The important constraint: it must NOT raise an exception.
        """
        with tempfile.TemporaryDirectory() as d:
            dp = pathlib.Path(d)
            path_a = _write_source(dp, "a.py", _INVALID_PYTHON)
            path_b = _write_source(dp, "b.py", _SIMPLE_A)

            # Must not raise; result is either None or a float in [0,1]
            try:
                dist = v1_behavioral_distance(path_a, path_b)
            except Exception as exc:
                self.fail(f"v1_behavioral_distance raised unexpectedly: {exc}")

            if dist is not None:
                self.assertGreaterEqual(dist, 0.0)
                self.assertLessEqual(dist, 1.0)

    def test_similarity_none_on_failure(self):
        """v1_behavioral_similarity must also return None on failure."""
        sim = v1_behavioral_similarity("/no/such/file.py", "/no/such/other.py")
        self.assertIsNone(sim)


class TestSimilarityConsistency(unittest.TestCase):
    """v1_behavioral_similarity must equal 1 - v1_behavioral_distance."""

    def test_sim_equals_one_minus_dist(self):
        with tempfile.TemporaryDirectory() as d:
            dp = pathlib.Path(d)
            path_a = _write_source(dp, "a.py", _SIMPLE_A)
            path_b = _write_source(dp, "b.py", _SIMPLE_B)

            dist = v1_behavioral_distance(path_a, path_b)
            sim = v1_behavioral_similarity(path_a, path_b)

            if dist is None:
                self.assertIsNone(sim)
            else:
                self.assertIsNotNone(sim)
                self.assertAlmostEqual(sim, 1.0 - dist, places=12)


if __name__ == "__main__":
    unittest.main()
