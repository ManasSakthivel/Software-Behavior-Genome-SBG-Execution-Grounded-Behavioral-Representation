"""
sbg/extraction/static/test_data_genome.py
==========================================
Tests for DataGenome, DataGenomeExtractor, distance(), and canonicalize().

Run with:
    python3 -m pytest sbg/extraction/static/test_data_genome.py -v
"""

from __future__ import annotations
import unittest
from sbg.extraction.static.data_genome import (
    DataGenome, DataGenomeExtractor, canonicalize, distance,
)

_extractor = DataGenomeExtractor()

# --- Source fixtures -------------------------------------------------------

_SRC_INTS = """\
x = 1
y = 2
z = x + y
w = z * 3
result = w - 1
"""

_SRC_STRS = """\
a = "hello"
b = "world"
c = a + " " + b
items = [a, b, c]
"""

_SRC_FLOATS = """\
pi = 3.14159
r = 2.5
area = pi * r * r
circumference = 2.0 * pi * r
"""

_SRC_CMPS = """\
x = 10
if x > 5:
    pass
if x == 10:
    pass
if x != 0:
    pass
if x <= 20:
    pass
"""

_SRC_ARITH = """\
a = 10
b = 3
c = a + b
d = a - b
e = a * b
f = a // b
g = a % b
h = a ** b
"""

_SRC_CONTAINERS = """\
lst = [1, 2, 3]
dct = {"a": 1, "b": 2}
st = {1, 2, 3}
tpl = (1, 2, 3)
nested = {"key": [1, 2]}
"""

_SRC_INTS_RENAMED = """\
a = 1
b = 2
c = a + b
d = c * 3
answer = d - 1
"""

_SRC_EMPTY = ""
_SRC_MINIMAL = "x = 42"


def _make_zero_genome():
    return DataGenome(
        value_type_histogram={t: 0 for t in ("int", "str", "float", "bool", "None")},
        constant_value_profile={
            "int_count": 0.0, "str_count": 0.0,
            "float_count": 0.0, "bool_count": 0.0,
        },
        container_usage={"list": 0, "dict": 0, "set": 0, "tuple": 0},
        arithmetic_op_histogram={op: 0 for op in
                                  ("Add", "Sub", "Mul", "Div", "Mod", "FloorDiv", "Pow")},
        comparison_op_histogram={op: 0 for op in
                                  ("Eq", "NotEq", "Lt", "LtE", "Gt", "GtE", "In", "NotIn")},
        data_flow_complexity=0.0,
    )


# --- Basic extraction tests ------------------------------------------------

class TestDataGenomeExtractorBasic(unittest.TestCase):

    def test_extract_returns_data_genome(self):
        g = _extractor.extract(_SRC_INTS)
        self.assertIsInstance(g, DataGenome)

    def test_empty_source_does_not_raise(self):
        g = _extractor.extract(_SRC_EMPTY)
        self.assertIsInstance(g, DataGenome)

    def test_syntax_error_raises_value_error(self):
        with self.assertRaises(ValueError):
            _extractor.extract("def broken(:")

    def test_int_literals_counted(self):
        g = _extractor.extract(_SRC_INTS)
        self.assertGreater(g.value_type_histogram["int"], 0)

    def test_str_literals_counted(self):
        g = _extractor.extract(_SRC_STRS)
        self.assertGreater(g.value_type_histogram["str"], 0)

    def test_float_literals_counted(self):
        g = _extractor.extract(_SRC_FLOATS)
        self.assertGreater(g.value_type_histogram["float"], 0)

    def test_bool_literal_counted(self):
        g = _extractor.extract("flag = True")
        self.assertGreater(g.value_type_histogram["bool"], 0)

    def test_none_literal_counted(self):
        g = _extractor.extract("x = None")
        self.assertGreater(g.value_type_histogram["None"], 0)

    def test_bool_not_confused_with_int(self):
        g = _extractor.extract("a = True\nb = False")
        self.assertEqual(g.value_type_histogram["bool"], 2)
        self.assertEqual(g.value_type_histogram["int"], 0)


# --- Container extraction tests --------------------------------------------

class TestDataGenomeExtractorContainers(unittest.TestCase):

    def test_list_literal(self):
        g = _extractor.extract("x = [1, 2, 3]")
        self.assertGreater(g.container_usage["list"], 0)

    def test_dict_literal(self):
        g = _extractor.extract('x = {"a": 1}')
        self.assertGreater(g.container_usage["dict"], 0)

    def test_set_literal(self):
        g = _extractor.extract("x = {1, 2}")
        self.assertGreater(g.container_usage["set"], 0)

    def test_tuple_literal(self):
        g = _extractor.extract("x = (1, 2)")
        self.assertGreater(g.container_usage["tuple"], 0)

    def test_list_comprehension_counted(self):
        g = _extractor.extract("x = [i*2 for i in range(10)]")
        self.assertGreater(g.container_usage["list"], 0)

    def test_dict_comprehension_counted(self):
        g = _extractor.extract("x = {k: v for k, v in {}.items()}")
        self.assertGreater(g.container_usage["dict"], 0)

    def test_container_heavy_source(self):
        g = _extractor.extract(_SRC_CONTAINERS)
        for ctype in ("list", "dict", "set", "tuple"):
            self.assertGreater(g.container_usage[ctype], 0, ctype)


# --- Operator histogram tests ----------------------------------------------

class TestDataGenomeExtractorOperators(unittest.TestCase):

    def test_addition_counted(self):
        g = _extractor.extract("x = 1 + 2")
        self.assertGreater(g.arithmetic_op_histogram["Add"], 0)

    def test_subtraction_counted(self):
        g = _extractor.extract("x = 5 - 3")
        self.assertGreater(g.arithmetic_op_histogram["Sub"], 0)

    def test_multiplication_counted(self):
        g = _extractor.extract("x = 4 * 3")
        self.assertGreater(g.arithmetic_op_histogram["Mul"], 0)

    def test_floor_division_counted(self):
        g = _extractor.extract("x = 10 // 3")
        self.assertGreater(g.arithmetic_op_histogram["FloorDiv"], 0)

    def test_modulo_counted(self):
        g = _extractor.extract("x = 7 % 2")
        self.assertGreater(g.arithmetic_op_histogram["Mod"], 0)

    def test_power_counted(self):
        g = _extractor.extract("x = 2 ** 8")
        self.assertGreater(g.arithmetic_op_histogram["Pow"], 0)

    def test_eq_comparison(self):
        g = _extractor.extract("x = (1 == 1)")
        self.assertGreater(g.comparison_op_histogram["Eq"], 0)

    def test_lt_comparison(self):
        g = _extractor.extract("x = (1 < 2)")
        self.assertGreater(g.comparison_op_histogram["Lt"], 0)

    def test_in_comparison(self):
        g = _extractor.extract("x = (1 in [1, 2])")
        self.assertGreater(g.comparison_op_histogram["In"], 0)

    def test_notin_comparison(self):
        g = _extractor.extract("x = (3 not in [1, 2])")
        self.assertGreater(g.comparison_op_histogram["NotIn"], 0)

    def test_arith_heavy_source(self):
        g = _extractor.extract(_SRC_ARITH)
        for op in ("Add", "Sub", "Mul", "FloorDiv", "Mod", "Pow"):
            self.assertGreater(g.arithmetic_op_histogram[op], 0, op)


# --- data_flow_complexity tests --------------------------------------------

class TestDataFlowComplexity(unittest.TestCase):

    def test_dfc_in_range(self):
        g = _extractor.extract(_SRC_INTS)
        self.assertGreaterEqual(g.data_flow_complexity, 0.0)
        self.assertLessEqual(g.data_flow_complexity, 1.0)

    def test_pure_assignments_max_dfc(self):
        g = _extractor.extract("x = 1\ny = 2\nz = 3")
        self.assertAlmostEqual(g.data_flow_complexity, 1.0, places=4)

    def test_no_assignments_zero_dfc(self):
        g = _extractor.extract("pass\npass\npass")
        self.assertAlmostEqual(g.data_flow_complexity, 0.0, places=4)

    def test_provenance_keys_present(self):
        g = _extractor.extract(_SRC_INTS)
        self.assertIn("source_hash", g.provenance)
        self.assertIn("tool", g.provenance)
        self.assertIn("python_runtime", g.provenance)


# --- distance tests --------------------------------------------------------

class TestDataGenomeDistance(unittest.TestCase):

    def test_distance_self_zero(self):
        g = _extractor.extract(_SRC_INTS)
        self.assertAlmostEqual(distance(g, g), 0.0, places=10)

    def test_distance_symmetric(self):
        g1 = _extractor.extract(_SRC_INTS)
        g2 = _extractor.extract(_SRC_STRS)
        self.assertAlmostEqual(distance(g1, g2), distance(g2, g1), places=10)

    def test_distance_in_range(self):
        g1 = _extractor.extract(_SRC_INTS)
        g2 = _extractor.extract(_SRC_STRS)
        d = distance(g1, g2)
        self.assertGreaterEqual(d, 0.0)
        self.assertLessEqual(d, 1.0)

    def test_distance_empty_to_nonempty_in_range(self):
        g1 = _extractor.extract(_SRC_EMPTY)
        g2 = _extractor.extract(_SRC_ARITH)
        d = distance(g1, g2)
        self.assertGreaterEqual(d, 0.0)
        self.assertLessEqual(d, 1.0)

    def test_distance_empty_self_zero(self):
        g = _extractor.extract(_SRC_EMPTY)
        self.assertAlmostEqual(distance(g, g), 0.0, places=10)

    def test_distance_two_empty_zero(self):
        g1 = _extractor.extract(_SRC_EMPTY)
        g2 = _extractor.extract(_SRC_EMPTY)
        self.assertAlmostEqual(distance(g1, g2), 0.0, places=10)

    def test_semantics_preserving_small_distance(self):
        """Renaming variables should produce a small distance (< 0.2)."""
        g1 = _extractor.extract(_SRC_INTS)
        g2 = _extractor.extract(_SRC_INTS_RENAMED)
        d = distance(g1, g2)
        self.assertLess(d, 0.2, "Expected d < 0.2, got {:.4f}".format(d))

    def test_obviously_different_programs_larger_distance(self):
        """Integer-only vs. container-heavy -> distance > 0.05."""
        g1 = _extractor.extract(_SRC_INTS)
        g2 = _extractor.extract(_SRC_CONTAINERS)
        d = distance(g1, g2)
        self.assertGreater(d, 0.05, "Expected d > 0.05, got {:.4f}".format(d))

    def test_float_vs_int_program_different(self):
        g1 = _extractor.extract(_SRC_INTS)
        g2 = _extractor.extract(_SRC_FLOATS)
        self.assertGreater(distance(g1, g2), 0.0)

    def test_manual_zero_genomes(self):
        g1 = _make_zero_genome()
        g2 = _make_zero_genome()
        self.assertAlmostEqual(distance(g1, g2), 0.0, places=10)


# --- canonicalize tests ----------------------------------------------------

class TestDataGenomeCanonicalize(unittest.TestCase):

    def test_returns_data_genome(self):
        g = _extractor.extract(_SRC_INTS)
        self.assertIsInstance(canonicalize(g), DataGenome)

    def test_idempotent(self):
        """canonicalize(canonicalize(g)) == canonicalize(g)."""
        g = _extractor.extract(_SRC_CONTAINERS)
        c1 = canonicalize(g)
        c2 = canonicalize(c1)
        self.assertEqual(c1.value_type_histogram, c2.value_type_histogram)
        self.assertEqual(c1.constant_value_profile, c2.constant_value_profile)
        self.assertEqual(c1.container_usage, c2.container_usage)
        self.assertEqual(c1.arithmetic_op_histogram, c2.arithmetic_op_histogram)
        self.assertEqual(c1.comparison_op_histogram, c2.comparison_op_histogram)
        self.assertAlmostEqual(c1.data_flow_complexity, c2.data_flow_complexity, places=10)

    def test_sorts_arith_keys(self):
        g = _extractor.extract(_SRC_ARITH)
        c = canonicalize(g)
        keys = list(c.arithmetic_op_histogram.keys())
        self.assertEqual(keys, sorted(keys))

    def test_sorts_cmp_keys(self):
        g = _extractor.extract(_SRC_CMPS)
        c = canonicalize(g)
        keys = list(c.comparison_op_histogram.keys())
        self.assertEqual(keys, sorted(keys))

    def test_sorts_value_type_keys(self):
        g = _extractor.extract(_SRC_INTS)
        c = canonicalize(g)
        keys = list(c.value_type_histogram.keys())
        self.assertEqual(keys, sorted(keys))

    def test_rounds_floats(self):
        g = _extractor.extract(_SRC_FLOATS)
        c = canonicalize(g)
        for v in c.constant_value_profile.values():
            self.assertAlmostEqual(v, round(v, 4), places=10)

    def test_clamps_dfc(self):
        g = _extractor.extract(_SRC_INTS)
        c = canonicalize(g)
        self.assertGreaterEqual(c.data_flow_complexity, 0.0)
        self.assertLessEqual(c.data_flow_complexity, 1.0)

    def test_preserves_total_counts(self):
        g = _extractor.extract(_SRC_ARITH)
        c = canonicalize(g)
        self.assertEqual(
            sum(g.arithmetic_op_histogram.values()),
            sum(c.arithmetic_op_histogram.values()),
        )

    def test_marks_provenance(self):
        g = _extractor.extract(_SRC_INTS)
        c = canonicalize(g)
        self.assertTrue(c.provenance.get("canonicalized"))

    def test_distance_self_zero_after_canonicalize(self):
        g = _extractor.extract(_SRC_INTS)
        c = canonicalize(g)
        self.assertAlmostEqual(distance(c, c), 0.0, places=10)

    def test_canonical_distance_same_as_original(self):
        """Canonicalising before computing distance must not change the result."""
        g1 = _extractor.extract(_SRC_INTS)
        g2 = _extractor.extract(_SRC_STRS)
        d_raw = distance(g1, g2)
        d_can = distance(canonicalize(g1), canonicalize(g2))
        self.assertAlmostEqual(d_raw, d_can, places=4)


if __name__ == "__main__":
    unittest.main()
