"""
benchmark/ground_truth/test_validator.py
=========================================
Unit-test suite for the SBG ground-truth validation system.

Test plan
---------
1.  DifferentialTester on known-equivalent programs
2.  DifferentialTester on known-different programs
3.  DifferentialTester: exception handling (A raises, B doesn't → divergent)
4.  DifferentialTester: timeout handling
5.  InputGenerator: random strategy produces correct count and valid values
6.  InputGenerator: boundary strategy hits edge values
7.  InputGenerator: partition strategy covers all equivalence classes
8.  InputGenerator: combinatorial strategy covers cartesian product subsets
9.  GroundTruthRecord: serialises to / deserialises from JSON correctly
10. GroundTruthRecord: schema-compatible output
11. GroundTruthValidator: SP pair → EQUIVALENT label
12. GroundTruthValidator: mutation pair → CHANGED label with witness
13. PairValidator.validate_sp_pair: divergent result triggers GT-T4 alert
14. PairValidator.validate_sc_pair: known-SC pair produces witnessed CHANGED record
15. PairValidator.validate_sc_pair: no divergence yields low-confidence CHANGED
16. Confidence calibration: more tests → higher confidence (monotone)
17. Confidence calibration: SC with witness → confidence 0.999

All tests use in-memory program strings written to a temp directory so no
persistent filesystem artefacts are created.
"""

from __future__ import annotations

import json
import math
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# Make the package importable when run from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmark.ground_truth.validator import (
    DifferentialTester,
    DifferentialResult,
    GroundTruthRecord,
    GroundTruthValidator,
    InputGenerator,
    PairValidator,
    ProgramSpec,
    _calibrate_confidence,
    PRNG_SEED,
    EXECUTION_TIMEOUT_SECONDS,
)


# ---------------------------------------------------------------------------
# Stable temp directory — created once at module import time so the path
# remains valid for the entire pytest session (avoids macOS APFS daemon
# cleanup of short-lived /var/folders entries between test methods).
# ---------------------------------------------------------------------------
import atexit as _atexit
import shutil as _shutil

_SESSION_TMPDIR = tempfile.mkdtemp(prefix="sbg_gt_tests_")
_atexit.register(_shutil.rmtree, _SESSION_TMPDIR, True)

_test_counter = [0]


def _make_test_dir() -> str:
    """Return a unique sub-directory under the stable session tmpdir."""
    _test_counter[0] += 1
    d = os.path.join(_SESSION_TMPDIR, f"t{_test_counter[0]}")
    os.makedirs(d, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_program(directory: str, filename: str, source: str) -> str:
    """Write ``source`` to ``directory/filename``, return the full path."""
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(textwrap.dedent(source))
    return path


# ---------------------------------------------------------------------------
# 1–4: DifferentialTester
# ---------------------------------------------------------------------------

class TestDifferentialTesterEquivalent(unittest.TestCase):
    """Programs that compute the same thing must produce no divergences."""

    def setUp(self):
        self.tmpdir = _make_test_dir()
        self.tester = DifferentialTester(timeout=EXECUTION_TIMEOUT_SECONDS, seed=PRNG_SEED)


    def test_identical_programs_no_divergence(self):
        src = """\
            def main(n: int) -> int:
                return n * n
        """
        a = _write_program(self.tmpdir, "prog_a.py", src)
        b = _write_program(self.tmpdir, "prog_b.py", src)
        inputs = list(range(-10, 11))
        result = self.tester.run_differential(a, b, inputs)
        self.assertIsInstance(result, DifferentialResult)
        self.assertTrue(result.same_outputs)
        self.assertEqual(result.divergent_inputs, [])
        self.assertEqual(result.n_tested, len(inputs))

    def test_semantically_equivalent_different_style(self):
        """for-loop vs sum() — same result."""
        src_a = """\
            def main(lst):
                total = 0
                for x in lst:
                    total += x
                return total
        """
        src_b = """\
            def main(lst):
                return sum(lst)
        """
        a = _write_program(self.tmpdir, "sum_a.py", src_a)
        b = _write_program(self.tmpdir, "sum_b.py", src_b)
        spec = ProgramSpec(param_types={"lst": "list[int]"}, n_params=1, list_length=(0, 10))
        gen = InputGenerator(seed=PRNG_SEED)
        inputs = gen.generate_inputs(spec, n=200)
        result = self.tester.run_differential(a, b, inputs)
        self.assertTrue(result.same_outputs)
        self.assertEqual(result.n_divergent, 0)

    def test_coverage_is_between_zero_and_one(self):
        src = "def main(x): return x"
        a = _write_program(self.tmpdir, "id_a.py", src)
        b = _write_program(self.tmpdir, "id_b.py", src)
        result = self.tester.run_differential(a, b, [0, 1, -1, 42])
        self.assertGreaterEqual(result.coverage, 0.0)
        self.assertLessEqual(result.coverage, 1.0)

    def test_empty_input_list(self):
        src = "def main(x): return x"
        a = _write_program(self.tmpdir, "empty_a.py", src)
        b = _write_program(self.tmpdir, "empty_b.py", src)
        result = self.tester.run_differential(a, b, [])
        self.assertEqual(result.n_tested, 0)
        self.assertTrue(result.same_outputs)


class TestDifferentialTesterDivergent(unittest.TestCase):
    """Programs with trivially different semantics must produce divergences."""

    def setUp(self):
        self.tmpdir = _make_test_dir()
        self.tester = DifferentialTester(timeout=EXECUTION_TIMEOUT_SECONDS, seed=PRNG_SEED)


    def test_arithmetic_mutation_detected(self):
        """SC-2: + replaced with -."""
        src_a = "def main(a, b): return a + b"
        src_b = "def main(a, b): return a - b"
        a = _write_program(self.tmpdir, "add_a.py", src_a)
        b = _write_program(self.tmpdir, "add_b.py", src_b)
        inputs = [(i, j) for i in range(-5, 6) for j in range(-5, 6) if i != 0 and j != 0]
        result = self.tester.run_differential(a, b, inputs)
        self.assertFalse(result.same_outputs)
        self.assertGreater(len(result.divergent_inputs), 0)

    def test_comparison_operator_mutation(self):
        """SC-4: < replaced with <=."""
        src_a = "def main(n): return n < 0"
        src_b = "def main(n): return n <= 0"
        a = _write_program(self.tmpdir, "cmp_a.py", src_a)
        b = _write_program(self.tmpdir, "cmp_b.py", src_b)
        result = self.tester.run_differential(a, b, [0])
        self.assertFalse(result.same_outputs)

    def test_return_value_change(self):
        """SC-6: returns constant 0 instead of n."""
        src_a = "def main(n): return n"
        src_b = "def main(n): return 0"
        a = _write_program(self.tmpdir, "ret_a.py", src_a)
        b = _write_program(self.tmpdir, "ret_b.py", src_b)
        result = self.tester.run_differential(a, b, [1, 2, 3])
        self.assertFalse(result.same_outputs)
        self.assertGreater(len(result.divergent_inputs), 0)

    def test_divergent_inputs_capped_at_five_by_validator(self):
        """GroundTruthValidator stores at most 5 divergent examples."""
        src_a = "def main(n): return n"
        src_b = "def main(n): return n + 1"
        a = _write_program(self.tmpdir, "d5_a.py", src_a)
        b = _write_program(self.tmpdir, "d5_b.py", src_b)
        validator = GroundTruthValidator(n_tests=20, seed=PRNG_SEED)
        record = validator.validate_pair(a, b, "SC-6",
                                         ProgramSpec(param_types={"n": "int"}, n_params=1))
        self.assertLessEqual(len(record.divergent_examples), 5)


class TestDifferentialTesterExceptions(unittest.TestCase):
    """If A raises but B does not, that is a divergent behaviour."""

    def setUp(self):
        self.tmpdir = _make_test_dir()
        self.tester = DifferentialTester(timeout=EXECUTION_TIMEOUT_SECONDS, seed=PRNG_SEED)


    def test_exception_in_a_not_b_is_divergent(self):
        src_a = """\
            def main(n):
                if n == 0:
                    raise ValueError("zero!")
                return n
        """
        src_b = "def main(n): return n"
        a = _write_program(self.tmpdir, "exc_a.py", src_a)
        b = _write_program(self.tmpdir, "exc_b.py", src_b)
        result = self.tester.run_differential(a, b, [0])
        self.assertFalse(result.same_outputs)
        self.assertEqual(len(result.divergent_inputs), 1)

    def test_same_exception_type_is_not_divergent(self):
        """Both raise ValueError → same observable exception type → not divergent."""
        src_a = """\
            def main(n):
                raise ValueError("msg from a")
        """
        src_b = """\
            def main(n):
                raise ValueError("different msg")
        """
        a = _write_program(self.tmpdir, "exc_same_a.py", src_a)
        b = _write_program(self.tmpdir, "exc_same_b.py", src_b)
        result = self.tester.run_differential(a, b, [1, 2, 3])
        # Exception messages differ but types match → no divergence
        self.assertTrue(result.same_outputs)

    def test_different_exception_types_are_divergent(self):
        src_a = """\
            def main(n):
                raise ValueError("v")
        """
        src_b = """\
            def main(n):
                raise TypeError("t")
        """
        a = _write_program(self.tmpdir, "exc_diff_a.py", src_a)
        b = _write_program(self.tmpdir, "exc_diff_b.py", src_b)
        result = self.tester.run_differential(a, b, [1])
        self.assertFalse(result.same_outputs)


class TestDifferentialTesterTimeout(unittest.TestCase):
    """A hanging program must be caught within the timeout budget."""

    def setUp(self):
        self.tmpdir = _make_test_dir()


    def test_timeout_treated_as_exception_output(self):
        src_a = """\
            import time
            def main(n):
                time.sleep(60)   # will time out
                return n
        """
        src_b = "def main(n): return n"
        a = _write_program(self.tmpdir, "hang_a.py", src_a)
        b = _write_program(self.tmpdir, "hang_b.py", src_b)

        # Use a very short timeout so the test runs quickly
        tester = DifferentialTester(timeout=0.5, seed=PRNG_SEED)
        result = tester.run_differential(a, b, [42])

        # The hanging program times out, returns TimeoutError sentinel;
        # the normal program returns 42 — they diverge.
        self.assertFalse(result.same_outputs)
        self.assertEqual(len(result.divergent_inputs), 1)

    def test_both_timeout_not_divergent(self):
        src = """\
            import time
            def main(n):
                time.sleep(60)
                return n
        """
        a = _write_program(self.tmpdir, "hang2_a.py", src)
        b = _write_program(self.tmpdir, "hang2_b.py", src)
        tester = DifferentialTester(timeout=0.5, seed=PRNG_SEED)
        result = tester.run_differential(a, b, [1])
        # Both time out with TimeoutError → same exception type → not divergent
        self.assertTrue(result.same_outputs)


# ---------------------------------------------------------------------------
# 5–8: InputGenerator
# ---------------------------------------------------------------------------

class TestInputGeneratorRandom(unittest.TestCase):

    def setUp(self):
        self.gen = InputGenerator(seed=PRNG_SEED)

    def test_produces_correct_count(self):
        spec = ProgramSpec(param_types={"n": "int"}, n_params=1)
        inputs = self.gen.generate_inputs(spec, n=500)
        self.assertEqual(len(inputs), 500)

    def test_integer_inputs_in_range(self):
        spec = ProgramSpec(param_types={"n": "int"}, n_params=1, int_range=(-100, 100))
        inputs = self.gen.generate_inputs(spec, n=200)
        for inp in inputs:
            self.assertIsInstance(inp, int)
            self.assertGreaterEqual(inp, -100)
            self.assertLessEqual(inp, 100)

    def test_string_inputs_are_strings(self):
        spec = ProgramSpec(param_types={"s": "str"}, n_params=1, str_length=(0, 10))
        inputs = self.gen.generate_inputs(spec, n=100)
        for inp in inputs:
            self.assertIsInstance(inp, str)
            self.assertLessEqual(len(inp), 10)

    def test_list_inputs_are_lists(self):
        spec = ProgramSpec(param_types={"lst": "list[int]"}, n_params=1, list_length=(0, 8))
        inputs = self.gen.generate_inputs(spec, n=100)
        for inp in inputs:
            self.assertIsInstance(inp, list)
            self.assertLessEqual(len(inp), 8)

    def test_two_param_inputs_are_tuples(self):
        # No param_types → generator uses positional packing → tuple
        spec = ProgramSpec(n_params=2)
        inputs = self.gen.generate_inputs(spec, n=50)
        for inp in inputs:
            self.assertIsInstance(inp, tuple)
            self.assertEqual(len(inp), 2)

    def test_dict_param_inputs_are_dicts(self):
        spec = ProgramSpec(param_types={"a": "int", "b": "str"}, n_params=2)
        inputs = self.gen.generate_inputs(spec, n=50)
        for inp in inputs:
            self.assertIsInstance(inp, dict)
            self.assertIn("a", inp)
            self.assertIn("b", inp)

    def test_bool_inputs(self):
        spec = ProgramSpec(param_types={"flag": "bool"}, n_params=1)
        inputs = self.gen.generate_inputs(spec, n=50)
        for inp in inputs:
            self.assertIsInstance(inp, bool)

    def test_deterministic_with_same_seed(self):
        spec = ProgramSpec(param_types={"n": "int"}, n_params=1)
        g1 = InputGenerator(seed=7)
        g2 = InputGenerator(seed=7)
        self.assertEqual(
            g1.generate_inputs(spec, n=100),
            g2.generate_inputs(spec, n=100),
        )


class TestInputGeneratorBoundary(unittest.TestCase):

    def setUp(self):
        self.gen = InputGenerator(seed=PRNG_SEED)

    def test_boundary_contains_zero(self):
        spec = ProgramSpec(param_types={"n": "int"}, n_params=1, int_range=(-100, 100))
        inputs = self.gen.generate_inputs(spec, n=1000, strategy="boundary")
        self.assertIn(0, inputs)

    def test_boundary_contains_min_value(self):
        spec = ProgramSpec(param_types={"n": "int"}, n_params=1, int_range=(-50, 50))
        inputs = self.gen.generate_inputs(spec, n=1000, strategy="boundary")
        self.assertIn(-50, inputs)

    def test_boundary_contains_max_value(self):
        spec = ProgramSpec(param_types={"n": "int"}, n_params=1, int_range=(-50, 50))
        inputs = self.gen.generate_inputs(spec, n=1000, strategy="boundary")
        self.assertIn(50, inputs)

    def test_boundary_str_includes_empty(self):
        spec = ProgramSpec(param_types={"s": "str"}, n_params=1)
        inputs = self.gen.generate_inputs(spec, n=200, strategy="boundary")
        self.assertIn("", inputs)


class TestInputGeneratorPartition(unittest.TestCase):

    def setUp(self):
        self.gen = InputGenerator(seed=PRNG_SEED)

    def test_partition_covers_negative_zero_positive(self):
        spec = ProgramSpec(param_types={"n": "int"}, n_params=1, int_range=(-1000, 1000))
        inputs = self.gen.generate_inputs(spec, n=1000, strategy="partition")
        # Must include at least one representative from each class
        has_neg = any(isinstance(x, int) and x < 0 for x in inputs)
        has_zero = 0 in inputs
        has_pos = any(isinstance(x, int) and x > 0 for x in inputs)
        self.assertTrue(has_neg, "No negative integers in partition inputs")
        self.assertTrue(has_zero, "No zero in partition inputs")
        self.assertTrue(has_pos, "No positive integers in partition inputs")

    def test_partition_str_includes_empty_and_nonempty(self):
        spec = ProgramSpec(param_types={"s": "str"}, n_params=1)
        inputs = self.gen.generate_inputs(spec, n=200, strategy="partition")
        self.assertIn("", inputs)
        has_nonempty = any(isinstance(x, str) and len(x) > 0 for x in inputs)
        self.assertTrue(has_nonempty)


class TestInputGeneratorCombinatorial(unittest.TestCase):

    def setUp(self):
        self.gen = InputGenerator(seed=PRNG_SEED)

    def test_combinatorial_returns_n_or_fewer(self):
        spec = ProgramSpec(param_types={"a": "int", "b": "int"}, n_params=2,
                           int_range=(-5, 5))
        inputs = self.gen.generate_inputs(spec, n=50, strategy="combinatorial")
        self.assertLessEqual(len(inputs), 50)
        self.assertGreater(len(inputs), 0)

    def test_invalid_strategy_raises(self):
        spec = ProgramSpec(n_params=1)
        with self.assertRaises(ValueError):
            self.gen.generate_inputs(spec, n=10, strategy="nonexistent")


# ---------------------------------------------------------------------------
# 9–10: GroundTruthRecord serialisation
# ---------------------------------------------------------------------------

class TestGroundTruthRecordSerialization(unittest.TestCase):

    def _make_record(self, **overrides) -> GroundTruthRecord:
        defaults = dict(
            base_id="prog_a",
            variant_id="prog_b",
            transformation_type="SP-3",
            semantic_relation="EQUIVALENT",
            gt_tier="GT-T3",
            confidence=0.955,
            n_tests_run=1000,
            n_divergent=0,
            divergent_examples=[],
            witness_input=None,
            validation_method="certified_transformation_differential_testing",
            validator_version="1.0.0",
            timestamp="2025-01-01T00:00:00+00:00",
        )
        defaults.update(overrides)
        return GroundTruthRecord(**defaults)

    def test_to_dict_is_dict(self):
        rec = self._make_record()
        d = rec.to_dict()
        self.assertIsInstance(d, dict)

    def test_to_json_is_valid_json(self):
        rec = self._make_record()
        j = rec.to_json()
        parsed = json.loads(j)
        self.assertIsInstance(parsed, dict)

    def test_all_required_fields_present(self):
        rec = self._make_record()
        d = rec.to_dict()
        required = [
            "base_id", "variant_id", "transformation_type", "semantic_relation",
            "gt_tier", "confidence", "n_tests_run", "n_divergent",
            "divergent_examples", "witness_input", "validation_method",
            "validator_version", "timestamp",
        ]
        for field in required:
            self.assertIn(field, d, f"Field '{field}' missing from GroundTruthRecord dict")

    def test_from_dict_roundtrip(self):
        rec = self._make_record()
        d = rec.to_dict()
        rec2 = GroundTruthRecord.from_dict(d)
        self.assertEqual(rec, rec2)

    def test_divergent_examples_serialized_as_list(self):
        rec = self._make_record(
            semantic_relation="CHANGED",
            n_divergent=2,
            divergent_examples=["1", "2"],
            witness_input="1",
        )
        d = rec.to_dict()
        self.assertIsInstance(d["divergent_examples"], list)

    def test_confidence_is_float_between_0_and_1(self):
        rec = self._make_record(confidence=0.95)
        d = rec.to_dict()
        self.assertIsInstance(d["confidence"], float)
        self.assertGreaterEqual(d["confidence"], 0.0)
        self.assertLessEqual(d["confidence"], 1.0)

    def test_semantic_relation_values(self):
        for relation in ("EQUIVALENT", "CHANGED"):
            rec = self._make_record(semantic_relation=relation)
            d = rec.to_dict()
            self.assertIn(d["semantic_relation"], ("EQUIVALENT", "CHANGED"))

    def test_gt_tier_values(self):
        for tier in ("GT-T1", "GT-T2", "GT-T3", "GT-T4"):
            rec = self._make_record(gt_tier=tier)
            d = rec.to_dict()
            self.assertIn(d["gt_tier"], ("GT-T1", "GT-T2", "GT-T3", "GT-T4"))


# ---------------------------------------------------------------------------
# 11–12: GroundTruthValidator integration
# ---------------------------------------------------------------------------

class TestGroundTruthValidatorIntegration(unittest.TestCase):

    def setUp(self):
        self.tmpdir = _make_test_dir()
        # Use small n_tests for speed; real runs use 1000+
        self.validator = GroundTruthValidator(n_tests=100, timeout=2.0, seed=PRNG_SEED)


    def test_sp_pair_returns_equivalent(self):
        """Two identical programs → EQUIVALENT."""
        src = "def main(n: int) -> int:\n    return n * n\n"
        a = _write_program(self.tmpdir, "sp_a.py", src)
        b = _write_program(self.tmpdir, "sp_b.py", src)
        record = self.validator.validate_pair(a, b, "SP-3")
        self.assertEqual(record.semantic_relation, "EQUIVALENT")
        self.assertGreaterEqual(record.confidence, 0.0)
        self.assertIn(record.gt_tier, ("GT-T1", "GT-T2", "GT-T3", "GT-T4"))

    def test_sp_pair_n_tests_matches_requested(self):
        src = "def main(n: int) -> int:\n    return abs(n)\n"
        a = _write_program(self.tmpdir, "ntest_a.py", src)
        b = _write_program(self.tmpdir, "ntest_b.py", src)
        record = self.validator.validate_pair(a, b, "SP-1")
        self.assertEqual(record.n_tests_run, 100)

    def test_sc_pair_returns_changed_with_witness(self):
        """SC-2 mutation (+ → -) must be caught."""
        src_a = "def main(a: int, b: int) -> int:\n    return a + b\n"
        src_b = "def main(a: int, b: int) -> int:\n    return a - b\n"
        a = _write_program(self.tmpdir, "sc_a.py", src_a)
        b = _write_program(self.tmpdir, "sc_b.py", src_b)
        spec = ProgramSpec(param_types={"a": "int", "b": "int"}, n_params=2, int_range=(-20, 20))
        record = self.validator.validate_pair(a, b, "SC-2", program_spec=spec)
        self.assertEqual(record.semantic_relation, "CHANGED")
        self.assertGreater(record.n_divergent, 0)
        self.assertIsNotNone(record.witness_input)

    def test_record_has_valid_timestamp(self):
        src = "def main(n: int) -> int:\n    return n\n"
        a = _write_program(self.tmpdir, "ts_a.py", src)
        b = _write_program(self.tmpdir, "ts_b.py", src)
        record = self.validator.validate_pair(a, b, "SP-1")
        from datetime import datetime
        # Should not raise
        dt = datetime.fromisoformat(record.timestamp)
        self.assertIsNotNone(dt)

    def test_record_validator_version_set(self):
        src = "def main(n: int) -> int:\n    return n\n"
        a = _write_program(self.tmpdir, "ver_a.py", src)
        b = _write_program(self.tmpdir, "ver_b.py", src)
        record = self.validator.validate_pair(a, b, "SP-1")
        self.assertRegex(record.validator_version, r"^\d+\.\d+\.\d+$")


# ---------------------------------------------------------------------------
# 13–15: PairValidator
# ---------------------------------------------------------------------------

class TestPairValidatorSP(unittest.TestCase):

    def setUp(self):
        self.tmpdir = _make_test_dir()
        self.pv = PairValidator(n_tests=100, timeout=2.0, seed=PRNG_SEED)


    def test_validate_sp_pair_equivalent_programs(self):
        src = "def main(n): return n ** 2\n"
        a = _write_program(self.tmpdir, "pv_sp_a.py", src)
        b = _write_program(self.tmpdir, "pv_sp_b.py", src)
        record = self.pv.validate_sp_pair(a, b, "SP-5")
        self.assertEqual(record.semantic_relation, "EQUIVALENT")

    def test_validate_sp_pair_divergent_triggers_alert(self):
        """Divergent pair labelled SP gets a GT-T4 alert in validation_method."""
        src_a = "def main(n: int) -> int:\n    return n\n"
        src_b = "def main(n: int) -> int:\n    return n + 1\n"
        a = _write_program(self.tmpdir, "pv_alert_a.py", src_a)
        b = _write_program(self.tmpdir, "pv_alert_b.py", src_b)
        spec = ProgramSpec(param_types={"n": "int"}, n_params=1)
        record = self.pv.validate_sp_pair(a, b, "SP-3", program_spec=spec)
        self.assertEqual(record.semantic_relation, "CHANGED")
        self.assertIn("alert", record.validation_method)
        self.assertEqual(record.gt_tier, "GT-T4")

    def test_validate_sp_pair_returns_ground_truth_record(self):
        src = "def main(n): return n\n"
        a = _write_program(self.tmpdir, "pv_rt_a.py", src)
        b = _write_program(self.tmpdir, "pv_rt_b.py", src)
        record = self.pv.validate_sp_pair(a, b)
        self.assertIsInstance(record, GroundTruthRecord)


class TestPairValidatorSC(unittest.TestCase):

    def setUp(self):
        self.tmpdir = _make_test_dir()
        self.pv = PairValidator(n_tests=200, timeout=2.0, seed=PRNG_SEED)


    def test_validate_sc_pair_finds_divergence(self):
        src_a = "def main(n: int) -> bool:\n    return n > 0\n"
        src_b = "def main(n: int) -> bool:\n    return n >= 0\n"  # SC-4
        a = _write_program(self.tmpdir, "sc_gt_a.py", src_a)
        b = _write_program(self.tmpdir, "sc_gt_b.py", src_b)
        spec = ProgramSpec(param_types={"n": "int"}, n_params=1, int_range=(-10, 10))
        record = self.pv.validate_sc_pair(a, b, "SC-4", program_spec=spec)
        self.assertEqual(record.semantic_relation, "CHANGED")
        self.assertGreater(record.n_divergent, 0)
        self.assertIsNotNone(record.witness_input)

    def test_validate_sc_pair_witness_input_prepended(self):
        """Supplying a known witness ensures it is tested first."""
        src_a = "def main(n: int) -> int:\n    return n * 2\n"
        src_b = "def main(n: int) -> int:\n    return n * 3\n"
        a = _write_program(self.tmpdir, "sc_wit_a.py", src_a)
        b = _write_program(self.tmpdir, "sc_wit_b.py", src_b)
        record = self.pv.validate_sc_pair(
            a, b, "SC-2", witness_input="5"
        )
        self.assertEqual(record.semantic_relation, "CHANGED")
        self.assertGreater(record.n_divergent, 0)

    def test_validate_sc_pair_no_divergence_low_confidence(self):
        """
        Artificially hard SC pair where the test inputs never trigger the bug.
        Confidence must be < 0.999 to signal uncertainty.
        """
        # A pair where the mutation only manifests at n=9999999 (never hit in tests)
        src_a = """\
            def main(n: int) -> int:
                if n == 9999999:
                    return 0   # never triggered in normal testing
                return n
        """
        src_b = "def main(n: int) -> int:\n    return n\n"
        a = _write_program(self.tmpdir, "sc_hard_a.py", src_a)
        b = _write_program(self.tmpdir, "sc_hard_b.py", src_b)
        spec = ProgramSpec(param_types={"n": "int"}, n_params=1, int_range=(-100, 100))
        record = self.pv.validate_sc_pair(a, b, "SC-6", program_spec=spec)
        # Still labelled CHANGED (SC type is sufficient by taxonomy)
        self.assertEqual(record.semantic_relation, "CHANGED")
        # But confidence must be below 0.999 since no witness was found
        self.assertLess(record.confidence, 0.999)


# ---------------------------------------------------------------------------
# 16–17: Confidence calibration unit tests
# ---------------------------------------------------------------------------

class TestConfidenceCalibration(unittest.TestCase):

    def test_more_tests_higher_confidence_sp(self):
        """Confidence is monotonically non-decreasing with more SP tests (no divergence)."""
        prev_conf = 0.0
        for n in [10, 50, 100, 500, 1000, 5000]:
            _, conf, _ = _calibrate_confidence(n, 0, "SP-3", is_sp=True)
            self.assertGreaterEqual(conf, prev_conf,
                                    f"Confidence dropped from {prev_conf} to {conf} at n={n}")
            prev_conf = conf

    def test_zero_tests_low_confidence(self):
        _, conf, _ = _calibrate_confidence(0, 0, "SP-3", is_sp=True)
        self.assertLessEqual(conf, 0.6)

    def test_sc_with_witness_max_confidence(self):
        tier, conf, method = _calibrate_confidence(100, 5, "SC-2", is_sp=False)
        self.assertEqual(conf, 0.999)
        self.assertEqual(tier, "GT-T1")

    def test_sp_divergence_returns_changed(self):
        """If divergence is found in an SP context, relation flips and confidence is high."""
        tier, conf, method = _calibrate_confidence(100, 3, "SP-3", is_sp=False)
        # is_sp=False here because the record builder already flipped the relation
        self.assertEqual(conf, 0.999)

    def test_gt_t3_requires_sp_type(self):
        """GT-T3 tier is only assigned to SP- typed transformations at n >= 1000."""
        tier, _, _ = _calibrate_confidence(1000, 0, "SP-5", is_sp=True)
        self.assertEqual(tier, "GT-T3")

    def test_non_sp_type_at_1000_gets_t4(self):
        tier, _, _ = _calibrate_confidence(1000, 0, "MANUAL-TRANSFORM", is_sp=True)
        self.assertEqual(tier, "GT-T4")

    def test_gt_t2_at_10000_tests(self):
        tier, conf, _ = _calibrate_confidence(10_000, 0, "SP-9", is_sp=True)
        self.assertEqual(tier, "GT-T2")
        self.assertGreaterEqual(conf, 0.990)

    def test_confidence_always_between_0_and_1(self):
        for n in [0, 1, 10, 100, 1000, 100000]:
            for n_div in [0, 1]:
                for sp in [True, False]:
                    _, conf, _ = _calibrate_confidence(n, n_div, "SP-1", is_sp=sp)
                    self.assertGreaterEqual(conf, 0.0, f"Negative confidence at n={n}")
                    self.assertLessEqual(conf, 1.0, f"Confidence > 1.0 at n={n}")


# ---------------------------------------------------------------------------
# Stdout capture in differential testing
# ---------------------------------------------------------------------------

class TestStdoutCapture(unittest.TestCase):

    def setUp(self):
        self.tmpdir = _make_test_dir()
        self.tester = DifferentialTester(timeout=2.0, seed=PRNG_SEED)


    def test_stdout_difference_is_divergent(self):
        """Programs that print different things diverge on observable output."""
        src_a = """\
            def main(n):
                print("Hello")
                return n
        """
        src_b = """\
            def main(n):
                print("World")
                return n
        """
        a = _write_program(self.tmpdir, "stdout_a.py", src_a)
        b = _write_program(self.tmpdir, "stdout_b.py", src_b)
        result = self.tester.run_differential(a, b, [1])
        self.assertFalse(result.same_outputs)

    def test_same_stdout_not_divergent(self):
        src = """\
            def main(n):
                print("same")
                return n
        """
        a = _write_program(self.tmpdir, "same_out_a.py", src)
        b = _write_program(self.tmpdir, "same_out_b.py", src)
        result = self.tester.run_differential(a, b, [1, 2, 3])
        self.assertTrue(result.same_outputs)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
