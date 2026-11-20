"""
Tests for sbg.extraction.static.error_genome
=============================================
All tests are deterministic (pure static analysis, no execution).

Coverage targets
----------------
* ErrorGenomeExtractor.extract
  - programs with no error handling → error_coverage_score = 0
  - programs with all functions having try/except → score > 0
  - err_circuit_breaker.py corpus program → multiple exception types detected
  - exception_types_raised, exception_types_caught populated correctly
  - bare_except_count, try_block_count, finally_block_count, assertion_count
  - error_propagation_pattern classification
* distance → identity (d(g,g)==0), symmetry, bounds [0,1]
  - programs with different error patterns → distance > 0
* canonicalize → idempotency, clamping, deduplication
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from sbg.extraction.static.error_genome import (
    ErrorGenome,
    ErrorGenomeExtractor,
    canonicalize,
    distance,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EXTRACTOR = ErrorGenomeExtractor()


def _extract(source: str) -> ErrorGenome:
    return _EXTRACTOR.extract(textwrap.dedent(source))


def _make_genome(
    *,
    raised: list | None = None,
    caught: list | None = None,
    bare: int = 0,
    try_count: int = 0,
    finally_count: int = 0,
    assertions: int = 0,
    pattern: str = "none",
    score: float = 0.0,
) -> ErrorGenome:
    return ErrorGenome(
        exception_types_raised=raised or [],
        exception_types_caught=caught or [],
        bare_except_count=bare,
        try_block_count=try_count,
        finally_block_count=finally_count,
        assertion_count=assertions,
        error_propagation_pattern=pattern,
        error_coverage_score=score,
        provenance={},
    )


# ---------------------------------------------------------------------------
# Corpus path
# ---------------------------------------------------------------------------

_CORPUS_DIR = Path(__file__).parent.parent.parent.parent / "benchmark" / "corpus" / "base_programs"
_CIRCUIT_BREAKER_PATH = _CORPUS_DIR / "err_circuit_breaker.py"


# ---------------------------------------------------------------------------
# Programs with no error handling
# ---------------------------------------------------------------------------

class TestNoErrorHandling:

    def test_no_functions_empty_module(self) -> None:
        g = _extract("x = 1\n")
        assert g.error_coverage_score == 0.0
        assert g.try_block_count == 0
        assert g.bare_except_count == 0
        assert g.exception_types_raised == []
        assert g.exception_types_caught == []

    def test_single_function_no_try(self) -> None:
        g = _extract("""
            def foo(x):
                return x + 1
        """)
        assert g.error_coverage_score == 0.0
        assert g.try_block_count == 0

    def test_multiple_functions_no_try(self) -> None:
        g = _extract("""
            def add(a, b):
                return a + b

            def mul(a, b):
                return a * b

            def div(a, b):
                return a / b
        """)
        assert g.error_coverage_score == 0.0
        assert g.try_block_count == 0

    def test_pattern_is_none_for_no_error_handling(self) -> None:
        g = _extract("""
            def compute(x):
                return x * 2
        """)
        assert g.error_propagation_pattern == "none"

    def test_assertion_count_no_try(self) -> None:
        g = _extract("""
            def validate(x):
                assert x > 0
                assert x < 100
                return x
        """)
        assert g.assertion_count == 2
        assert g.error_coverage_score == 0.0  # assert is not try/except


# ---------------------------------------------------------------------------
# Programs with all functions having try/except
# ---------------------------------------------------------------------------

class TestFullErrorHandling:

    def test_all_functions_have_try_score_is_one(self) -> None:
        g = _extract("""
            def f():
                try:
                    pass
                except ValueError:
                    pass

            def g():
                try:
                    pass
                except TypeError:
                    pass
        """)
        assert g.error_coverage_score == pytest.approx(1.0)

    def test_partial_coverage_score(self) -> None:
        g = _extract("""
            def f():
                try:
                    pass
                except ValueError:
                    pass

            def g():
                return 1
        """)
        assert g.error_coverage_score == pytest.approx(0.5)

    def test_try_block_count_matches(self) -> None:
        g = _extract("""
            def f():
                try:
                    pass
                except:
                    pass

            def h():
                try:
                    pass
                except ValueError:
                    pass
                finally:
                    pass
        """)
        assert g.try_block_count == 2
        assert g.finally_block_count == 1

    def test_error_coverage_score_positive_for_covered_functions(self) -> None:
        g = _extract("""
            def run():
                try:
                    result = 1 / 0
                except ZeroDivisionError:
                    result = 0
                return result
        """)
        assert g.error_coverage_score > 0.0

    def test_nested_function_counts_separately(self) -> None:
        g = _extract("""
            def outer():
                def inner():
                    try:
                        pass
                    except ValueError:
                        pass
                inner()
        """)
        # outer has no try; inner has try → 1/2 = 0.5
        assert g.error_coverage_score == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Exception type extraction
# ---------------------------------------------------------------------------

class TestExceptionTypeExtraction:

    def test_raised_exception_type(self) -> None:
        g = _extract("""
            def f():
                raise ValueError("bad")
        """)
        assert "ValueError" in g.exception_types_raised

    def test_caught_exception_type(self) -> None:
        g = _extract("""
            def f():
                try:
                    pass
                except TypeError:
                    pass
        """)
        assert "TypeError" in g.exception_types_caught

    def test_multiple_raised_types(self) -> None:
        g = _extract("""
            def f(x):
                if x < 0:
                    raise ValueError("neg")
                if x > 100:
                    raise OverflowError("big")
        """)
        assert "ValueError" in g.exception_types_raised
        assert "OverflowError" in g.exception_types_raised

    def test_bare_reraise_sentinel(self) -> None:
        g = _extract("""
            def f():
                try:
                    pass
                except ValueError:
                    raise
        """)
        assert "<re-raise>" in g.exception_types_raised

    def test_bare_except_counted(self) -> None:
        g = _extract("""
            def f():
                try:
                    pass
                except:
                    pass
        """)
        assert g.bare_except_count == 1

    def test_multiple_except_handlers(self) -> None:
        g = _extract("""
            def f():
                try:
                    pass
                except ValueError:
                    pass
                except TypeError:
                    pass
                except:
                    pass
        """)
        assert "ValueError" in g.exception_types_caught
        assert "TypeError" in g.exception_types_caught
        assert g.bare_except_count == 1

    def test_finally_block_counted(self) -> None:
        g = _extract("""
            def f():
                try:
                    pass
                finally:
                    pass
        """)
        assert g.finally_block_count == 1

    def test_no_finally_when_absent(self) -> None:
        g = _extract("""
            def f():
                try:
                    pass
                except ValueError:
                    pass
        """)
        assert g.finally_block_count == 0


# ---------------------------------------------------------------------------
# Error propagation pattern
# ---------------------------------------------------------------------------

class TestErrorPropagationPattern:

    def test_pattern_raise_when_reraise_only(self) -> None:
        g = _extract("""
            def f():
                try:
                    pass
                except ValueError:
                    raise
        """)
        assert g.error_propagation_pattern == "raise"

    def test_pattern_return_none(self) -> None:
        g = _extract("""
            def f():
                try:
                    return 1
                except ValueError:
                    return None
        """)
        assert g.error_propagation_pattern == "return_none"

    def test_pattern_return_sentinel(self) -> None:
        g = _extract("""
            def f():
                try:
                    return 1
                except ValueError:
                    return -1
        """)
        assert g.error_propagation_pattern == "return_sentinel"

    def test_pattern_mixed(self) -> None:
        g = _extract("""
            def f():
                try:
                    return 1
                except ValueError:
                    raise
                except TypeError:
                    return -1
        """)
        assert g.error_propagation_pattern == "mixed"

    def test_pattern_none_no_handling(self) -> None:
        g = _extract("x = 1\n")
        assert g.error_propagation_pattern == "none"


# ---------------------------------------------------------------------------
# err_circuit_breaker.py corpus test
# ---------------------------------------------------------------------------

class TestCircuitBreakerCorpus:

    @pytest.fixture(scope="class")
    def genome(self) -> ErrorGenome:
        source = _CIRCUIT_BREAKER_PATH.read_text(encoding="utf-8")
        return _EXTRACTOR.extract(source)

    def test_circuit_breaker_file_exists(self) -> None:
        assert _CIRCUIT_BREAKER_PATH.exists(), f"Corpus file not found: {_CIRCUIT_BREAKER_PATH}"

    def test_raises_value_error(self, genome: ErrorGenome) -> None:
        assert "ValueError" in genome.exception_types_raised

    def test_raises_runtime_error(self, genome: ErrorGenome) -> None:
        assert "RuntimeError" in genome.exception_types_raised

    def test_catches_exception(self, genome: ErrorGenome) -> None:
        # The 'except Exception as exc:' handler in call()
        assert "Exception" in genome.exception_types_caught

    def test_multiple_exception_types_detected(self, genome: ErrorGenome) -> None:
        # Should have at least 2 distinct raised exception types
        assert len(genome.exception_types_raised) >= 2

    def test_try_block_count_positive(self, genome: ErrorGenome) -> None:
        assert genome.try_block_count >= 1

    def test_assertion_count_positive(self, genome: ErrorGenome) -> None:
        # The __main__ block contains multiple assert statements
        assert genome.assertion_count >= 1

    def test_error_coverage_score_positive(self, genome: ErrorGenome) -> None:
        # At least one method has a try block (call, __init__)
        assert genome.error_coverage_score > 0.0

    def test_error_coverage_score_in_unit_interval(self, genome: ErrorGenome) -> None:
        assert 0.0 <= genome.error_coverage_score <= 1.0


# ---------------------------------------------------------------------------
# distance
# ---------------------------------------------------------------------------

class TestErrorGenomeDistance:

    def test_distance_self_is_zero(self) -> None:
        g = _make_genome(raised=["ValueError"], caught=["TypeError"], try_count=2)
        assert distance(g, g) == pytest.approx(0.0)

    def test_distance_identical_genomes_is_zero(self) -> None:
        g1 = _make_genome(raised=["ValueError"], caught=["TypeError"])
        g2 = _make_genome(raised=["ValueError"], caught=["TypeError"])
        assert distance(g1, g2) == pytest.approx(0.0)

    def test_distance_in_unit_interval(self) -> None:
        g1 = _make_genome(raised=["A"], caught=["B"], try_count=1)
        g2 = _make_genome(raised=["C"], caught=["D"], try_count=99)
        d = distance(g1, g2)
        assert 0.0 <= d <= 1.0

    def test_distance_symmetry(self) -> None:
        g1 = _make_genome(raised=["ValueError"], caught=["TypeError"])
        g2 = _make_genome(raised=["RuntimeError"], caught=["KeyError"])
        assert distance(g1, g2) == pytest.approx(distance(g2, g1))

    def test_different_exception_types_nonzero_distance(self) -> None:
        g1 = _make_genome(raised=["ValueError"])
        g2 = _make_genome(raised=["RuntimeError"])
        assert distance(g1, g2) > 0.0

    def test_different_patterns_nonzero_distance(self) -> None:
        g1 = _make_genome(pattern="raise")
        g2 = _make_genome(pattern="return_none")
        assert distance(g1, g2) > 0.0

    def test_empty_genomes_zero_distance(self) -> None:
        g1 = _make_genome()
        g2 = _make_genome()
        assert distance(g1, g2) == pytest.approx(0.0)

    def test_no_handling_vs_full_handling_nonzero(self) -> None:
        no_handling = _extract("""
            def f(x):
                return x
        """)
        full_handling = _extract("""
            def f(x):
                try:
                    return x
                except Exception:
                    return None
        """)
        assert distance(no_handling, full_handling) > 0.0

    def test_distance_circuit_breaker_vs_no_error_handling(self) -> None:
        source = _CIRCUIT_BREAKER_PATH.read_text(encoding="utf-8")
        g_cb = _EXTRACTOR.extract(source)
        g_plain = _extract("def noop():\n    return 1\n")
        assert distance(g_cb, g_plain) > 0.0

    def test_distance_never_exceeds_one(self) -> None:
        g1 = _make_genome(
            raised=[f"E{i}" for i in range(20)],
            caught=[f"H{i}" for i in range(20)],
            bare=10,
            try_count=50,
            assertions=100,
            pattern="raise",
            score=1.0,
        )
        g2 = _make_genome()
        assert distance(g1, g2) <= 1.0


# ---------------------------------------------------------------------------
# canonicalize
# ---------------------------------------------------------------------------

class TestErrorGenomeCanonicalize:

    def test_canonicalize_idempotent(self) -> None:
        g = _make_genome(raised=["ValueError", "TypeError"], caught=["Exception"], try_count=2)
        c1 = canonicalize(g)
        c2 = canonicalize(c1)
        assert c1.exception_types_raised == c2.exception_types_raised
        assert c1.exception_types_caught == c2.exception_types_caught
        assert c1.try_block_count == c2.try_block_count
        assert c1.error_coverage_score == c2.error_coverage_score
        assert c1.bare_except_count == c2.bare_except_count

    def test_canonicalize_deduplicates_exception_types(self) -> None:
        g = _make_genome(raised=["ValueError", "ValueError", "TypeError"])
        c = canonicalize(g)
        assert c.exception_types_raised.count("ValueError") == 1

    def test_canonicalize_sorts_exception_types(self) -> None:
        g = _make_genome(raised=["Z", "A", "M"], caught=["Y", "B"])
        c = canonicalize(g)
        assert c.exception_types_raised == sorted(c.exception_types_raised)
        assert c.exception_types_caught == sorted(c.exception_types_caught)

    def test_canonicalize_clamps_negative_counts(self) -> None:
        g = _make_genome(bare=-3, try_count=-1, assertions=-10)
        c = canonicalize(g)
        assert c.bare_except_count == 0
        assert c.try_block_count == 0
        assert c.assertion_count == 0

    def test_canonicalize_clamps_score_to_one(self) -> None:
        g = _make_genome(score=1.5)
        c = canonicalize(g)
        assert c.error_coverage_score == pytest.approx(1.0)

    def test_canonicalize_clamps_score_to_zero(self) -> None:
        g = _make_genome(score=-0.5)
        c = canonicalize(g)
        assert c.error_coverage_score == pytest.approx(0.0)

    def test_canonicalize_sets_canonicalized_flag(self) -> None:
        g = _make_genome()
        c = canonicalize(g)
        assert c.provenance.get("canonicalized") is True

    def test_canonicalize_preserves_pattern(self) -> None:
        for pat in ("raise", "return_none", "return_sentinel", "mixed", "none"):
            g = _make_genome(pattern=pat)
            c = canonicalize(g)
            assert c.error_propagation_pattern == pat

    def test_canonicalize_distance_self_zero_after_canonicalize(self) -> None:
        source = _CIRCUIT_BREAKER_PATH.read_text(encoding="utf-8")
        g = _EXTRACTOR.extract(source)
        c = canonicalize(g)
        assert distance(c, c) == pytest.approx(0.0)

    def test_canonicalize_extracted_genome_idempotent(self) -> None:
        source = _CIRCUIT_BREAKER_PATH.read_text(encoding="utf-8")
        g = _EXTRACTOR.extract(source)
        c1 = canonicalize(g)
        c2 = canonicalize(c1)
        assert c1.exception_types_raised == c2.exception_types_raised
        assert c1.try_block_count == c2.try_block_count
        assert c1.error_coverage_score == pytest.approx(c2.error_coverage_score)
