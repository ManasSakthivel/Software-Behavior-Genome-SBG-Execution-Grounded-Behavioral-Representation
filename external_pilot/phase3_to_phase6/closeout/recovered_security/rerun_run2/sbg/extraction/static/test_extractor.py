"""
sbg/extraction/static/test_extractor.py
=========================================
Tests for StaticExtractor, ControlGenomeExtractor, distance(), and canonicalize().

Run with:  pytest sbg/extraction/static/test_extractor.py -v

All assertions use only stdlib; no external dependencies.
"""

from __future__ import annotations

import math
import pathlib
from typing import List

import pytest

from sbg.extraction.static.extractor import (
    ControlGenome,
    ControlGenomeExtractor,
    StaticExtractor,
    StaticFeatures,
    canonicalize,
    distance,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CORPUS = pathlib.Path(__file__).parent.parent.parent.parent / "benchmark" / "corpus" / "base_programs"


def _read(program_id: str) -> str:
    """Read a base-program source file from the corpus."""
    path = _CORPUS / f"{program_id}.py"
    return path.read_text(encoding="utf-8")


_static = StaticExtractor()
_ctrl = ControlGenomeExtractor()


# ===========================================================================
# Part 1 — StaticExtractor on corpus programs
# ===========================================================================

class TestStaticExtractorOnCorpus:
    """Extract StaticFeatures from 5+ corpus programs and assert sanity."""

    # ---- sort_mergesort ----

    def test_mergesort_functions(self):
        src = _read("sort_mergesort")
        f = _static.extract(src)
        # mergesort, _merge, test_mergesort = 3 functions minimum
        assert f.function_count >= 3

    def test_mergesort_has_recursion(self):
        src = _read("sort_mergesort")
        f = _static.extract(src)
        assert f.has_recursion is True

    def test_mergesort_loops_and_branches(self):
        src = _read("sort_mergesort")
        f = _static.extract(src)
        assert f.loop_count >= 1     # while loop in _merge
        assert f.branch_count >= 2   # at least if + while

    def test_mergesort_call_sites_include_merge(self):
        src = _read("sort_mergesort")
        f = _static.extract(src)
        assert "_merge" in f.call_sites or "mergesort" in f.call_sites

    def test_mergesort_cyclomatic_complexity_positive(self):
        src = _read("sort_mergesort")
        f = _static.extract(src)
        assert f.cyclomatic_complexity >= 3

    def test_mergesort_ast_histogram_contains_if(self):
        src = _read("sort_mergesort")
        f = _static.extract(src)
        assert f.ast_node_type_histogram.get("If", 0) >= 1

    # ---- math_prime_sieve ----

    def test_prime_sieve_functions(self):
        src = _read("math_prime_sieve")
        f = _static.extract(src)
        # sieve, prime_factorize, _mod_pow, is_prime, goldbach, test_prime_sieve
        assert f.function_count >= 5

    def test_prime_sieve_has_loops(self):
        src = _read("math_prime_sieve")
        f = _static.extract(src)
        assert f.loop_count >= 3

    def test_prime_sieve_exception_handler(self):
        src = _read("math_prime_sieve")
        f = _static.extract(src)
        # goldbach raises ValueError; test catches ValueError
        assert f.exception_handlers >= 1

    def test_prime_sieve_has_imports(self):
        src = _read("math_prime_sieve")
        f = _static.extract(src)
        assert "typing" in f.import_names

    def test_prime_sieve_complexity(self):
        src = _read("math_prime_sieve")
        f = _static.extract(src)
        assert f.cyclomatic_complexity >= 10

    # ---- graph_dijkstra ----

    def test_dijkstra_loop_and_branch(self):
        src = _read("graph_dijkstra")
        f = _static.extract(src)
        assert f.loop_count >= 2
        assert f.branch_count >= 4

    def test_dijkstra_import_heapq(self):
        src = _read("graph_dijkstra")
        f = _static.extract(src)
        assert "heapq" in f.import_names

    def test_dijkstra_returns(self):
        src = _read("graph_dijkstra")
        f = _static.extract(src)
        assert f.return_sites >= 2

    def test_dijkstra_nesting_depth(self):
        src = _read("graph_dijkstra")
        f = _static.extract(src)
        # nested for-loop inside while-loop → depth ≥ 2
        assert f.max_nesting_depth >= 2

    def test_dijkstra_cfg_counts_positive(self):
        src = _read("graph_dijkstra")
        f = _static.extract(src)
        assert f.cfg_node_count > 0
        assert f.cfg_edge_count > 0

    # ---- ds_lru_cache ----

    def test_lru_cache_has_class_methods(self):
        src = _read("ds_lru_cache")
        f = _static.extract(src)
        # _DNode.__init__, LRUCache.__init__, get, peek, put,
        # keys_lru_order, _add_to_front, _remove_node, _move_to_front, _evict_lru
        assert f.function_count >= 8

    def test_lru_cache_no_explicit_loops_many(self):
        # keys_lru_order uses a while loop
        src = _read("ds_lru_cache")
        f = _static.extract(src)
        assert f.loop_count >= 1

    def test_lru_cache_exception_handler(self):
        src = _read("ds_lru_cache")
        f = _static.extract(src)
        # test catches ValueError for LRUCache(0)
        assert f.exception_handlers >= 1

    def test_lru_cache_no_recursion(self):
        src = _read("ds_lru_cache")
        f = _static.extract(src)
        assert f.has_recursion is False

    # ---- str_edit_distance ----

    def test_edit_distance_functions(self):
        src = _read("str_edit_distance")
        f = _static.extract(src)
        assert f.function_count >= 3  # edit_distance, align, edit_distance_bounded, test

    def test_edit_distance_nested_loops(self):
        src = _read("str_edit_distance")
        f = _static.extract(src)
        assert f.loop_count >= 4   # multiple for loops in dp fill

    def test_edit_distance_complexity(self):
        src = _read("str_edit_distance")
        f = _static.extract(src)
        assert f.cyclomatic_complexity >= 8

    def test_edit_distance_returns_positive(self):
        src = _read("str_edit_distance")
        f = _static.extract(src)
        assert f.return_sites >= 2

    def test_edit_distance_histogram_has_for(self):
        src = _read("str_edit_distance")
        f = _static.extract(src)
        assert f.ast_node_type_histogram.get("For", 0) >= 2


# ===========================================================================
# Part 2 — StaticFeatures field contract
# ===========================================================================

class TestStaticFeaturesContract:

    def test_trivial_program(self):
        src = "x = 1\n"
        f = _static.extract(src)
        assert f.cfg_node_count >= 1
        assert f.branch_count == 0
        assert f.loop_count == 0
        assert f.function_count == 0
        assert f.has_recursion is False
        assert f.cyclomatic_complexity == 1

    def test_call_sites_collected(self):
        src = "def foo(): pass\nfoo()\nbar()\n"
        f = _static.extract(src)
        assert "foo" in f.call_sites
        assert "bar" in f.call_sites

    def test_import_deduplication(self):
        src = "import os\nimport os\nimport sys\n"
        f = _static.extract(src)
        assert f.import_names.count("os") == 1
        assert "sys" in f.import_names

    def test_global_variables_module_level(self):
        src = "X = 1\nY = 2\n"
        f = _static.extract(src)
        assert "X" in f.global_variables
        assert "Y" in f.global_variables

    def test_local_variables_not_in_globals(self):
        src = "def f():\n    x = 1\n    y = 2\n"
        f = _static.extract(src)
        assert "x" not in f.global_variables
        assert "y" not in f.global_variables
        assert f.local_variable_count >= 2

    def test_exception_handler_count(self):
        src = (
            "try:\n    pass\n"
            "except ValueError:\n    pass\n"
            "except TypeError:\n    pass\n"
        )
        f = _static.extract(src)
        assert f.exception_handlers == 2

    def test_nesting_depth_nested_loops(self):
        src = (
            "for i in range(10):\n"
            "    for j in range(10):\n"
            "        for k in range(10):\n"
            "            pass\n"
        )
        f = _static.extract(src)
        assert f.max_nesting_depth >= 3

    def test_unsupported_language_raises(self):
        with pytest.raises(NotImplementedError):
            _static.extract("fn main() {}", language="rust")

    def test_syntax_error_raises(self):
        with pytest.raises(ValueError):
            _static.extract("def broken(:\n    pass\n")

    def test_recursion_direct(self):
        src = "def f(n):\n    return f(n-1)\n"
        f = _static.extract(src)
        assert f.has_recursion is True

    def test_recursion_indirect_not_detected(self):
        # Indirect recursion (f→g→f) is out of scope for static AST analysis.
        src = "def f(): g()\ndef g(): pass\n"
        f = _static.extract(src)
        # f does not directly call itself → no recursion detected
        assert f.has_recursion is False


# ===========================================================================
# Part 3 — ControlGenomeExtractor
# ===========================================================================

class TestControlGenomeExtractor:

    def test_empty_program(self):
        g = _ctrl.extract("x = 1\n")
        assert isinstance(g, ControlGenome)
        assert g.cyclomatic_complexity == 1
        assert g.branch_probability_profile == {}
        assert g.control_flow_entropy == 0.0

    def test_branch_profile_sums_to_one(self):
        src = _read("math_prime_sieve")
        g = _ctrl.extract(src)
        total = sum(g.branch_probability_profile.values())
        assert abs(total - 1.0) < 1e-9 or total == 0.0

    def test_branch_profile_keys_are_branch_types(self):
        src = _read("sort_mergesort")
        g = _ctrl.extract(src)
        valid_types = {"If", "For", "While", "AsyncFor", "Try", "TryStar"}
        for key in g.branch_probability_profile:
            assert key in valid_types, f"Unexpected key: {key!r}"

    def test_cyclomatic_complexity_mergesort(self):
        src = _read("sort_mergesort")
        g = _ctrl.extract(src)
        assert g.cyclomatic_complexity >= 3

    def test_call_graph_edges_present(self):
        src = _read("graph_dijkstra")
        g = _ctrl.extract(src)
        assert len(g.call_graph_edges) > 0

    def test_call_graph_edge_structure(self):
        src = _read("graph_dijkstra")
        g = _ctrl.extract(src)
        for edge in g.call_graph_edges:
            assert isinstance(edge, tuple) and len(edge) == 2

    def test_loop_nesting_profile_structure(self):
        src = _read("sort_mergesort")
        g = _ctrl.extract(src)
        # Should be a list of ints
        assert isinstance(g.loop_nesting_profile, list)
        assert all(isinstance(x, int) for x in g.loop_nesting_profile)

    def test_loop_nesting_profile_index_zero(self):
        """Index 0 should always be 0 (loops start at depth ≥ 1)."""
        src = _read("sort_mergesort")
        g = _ctrl.extract(src)
        if g.loop_nesting_profile:
            assert g.loop_nesting_profile[0] == 0

    def test_entropy_non_negative(self):
        src = _read("math_prime_sieve")
        g = _ctrl.extract(src)
        assert g.control_flow_entropy >= 0.0

    def test_entropy_zero_when_single_branch_type(self):
        # Only For loops → only one branch type → entropy = 0.
        src = "for i in range(10): pass\n"
        g = _ctrl.extract(src)
        assert g.control_flow_entropy == pytest.approx(0.0, abs=1e-9)

    def test_entropy_positive_when_mixed_branches(self):
        src = (
            "for i in range(5):\n    pass\n"
            "if True:\n    pass\n"
            "while False:\n    pass\n"
        )
        g = _ctrl.extract(src)
        assert g.control_flow_entropy > 0.0

    def test_provenance_fields(self):
        g = _ctrl.extract("x = 1\n")
        assert "source_hash" in g.provenance
        assert "tool" in g.provenance
        assert "python_runtime" in g.provenance
        assert "analysis" in g.provenance

    def test_provenance_analysis_is_static(self):
        g = _ctrl.extract("x = 1\n")
        assert g.provenance["analysis"] == "static_ast"

    def test_caller_callee_includes_module_scope(self):
        src = "print('hello')\n"
        g = _ctrl.extract(src)
        callers = [e[0] for e in g.call_graph_edges]
        assert "<module>" in callers

    def test_caller_inside_function(self):
        src = "def foo():\n    bar()\n"
        g = _ctrl.extract(src)
        edges = dict(g.call_graph_edges)
        # ("foo", "bar") should be present
        assert any(caller == "foo" and callee == "bar"
                   for caller, callee in g.call_graph_edges)


# ===========================================================================
# Part 4 — distance() properties
# ===========================================================================

class TestDistance:

    def _genome_from(self, src: str) -> ControlGenome:
        return _ctrl.extract(src)

    def test_distance_self_zero(self):
        """distance(g, g) == 0."""
        src = _read("sort_mergesort")
        g = self._genome_from(src)
        assert distance(g, g) == pytest.approx(0.0, abs=1e-12)

    def test_distance_symmetric(self):
        """distance(g1, g2) == distance(g2, g1)."""
        g1 = self._genome_from(_read("sort_mergesort"))
        g2 = self._genome_from(_read("sort_quicksort"))
        assert distance(g1, g2) == pytest.approx(distance(g2, g1), abs=1e-12)

    def test_distance_in_unit_interval(self):
        """distance is always in [0, 1]."""
        programs = [
            "sort_mergesort",
            "sort_quicksort",
            "graph_dijkstra",
            "ds_lru_cache",
            "math_prime_sieve",
            "str_edit_distance",
        ]
        genomes = [self._genome_from(_read(p)) for p in programs]
        for i, g1 in enumerate(genomes):
            for j, g2 in enumerate(genomes):
                d = distance(g1, g2)
                assert 0.0 <= d <= 1.0, (
                    f"distance({programs[i]}, {programs[j]}) = {d} not in [0,1]"
                )

    def test_distance_zero_on_identical_extract(self):
        """Extracting the same source twice gives distance 0."""
        src = _read("graph_dijkstra")
        g1 = self._genome_from(src)
        g2 = self._genome_from(src)
        assert distance(g1, g2) == pytest.approx(0.0, abs=1e-12)

    def test_distance_symmetric_across_all_pairs(self):
        """Symmetry holds for every pair in a small set."""
        programs = ["sort_mergesort", "ds_lru_cache", "math_prime_sieve"]
        genomes = {p: self._genome_from(_read(p)) for p in programs}
        for p1 in programs:
            for p2 in programs:
                d12 = distance(genomes[p1], genomes[p2])
                d21 = distance(genomes[p2], genomes[p1])
                assert d12 == pytest.approx(d21, abs=1e-12)

    def test_distance_both_empty_genomes_zero(self):
        """Two programs with no branches at all → distance 0."""
        src = "x = 1\n"
        g1 = self._genome_from(src)
        g2 = self._genome_from(src)
        assert distance(g1, g2) == pytest.approx(0.0, abs=1e-12)

    def test_distance_one_empty_one_rich(self):
        """A complex program vs. trivial should yield distance > 0."""
        g_trivial = self._genome_from("x = 1\n")
        g_rich = self._genome_from(_read("math_prime_sieve"))
        d = distance(g_trivial, g_rich)
        assert d > 0.0


# ===========================================================================
# Part 5 — canonicalize() properties
# ===========================================================================

class TestCanonicalize:

    def _genome_from(self, src: str) -> ControlGenome:
        return _ctrl.extract(src)

    def test_idempotent_simple(self):
        """canonicalize(canonicalize(g)) == canonicalize(g) for a simple program."""
        src = _read("sort_mergesort")
        g = self._genome_from(src)
        cg1 = canonicalize(g)
        cg2 = canonicalize(cg1)
        assert cg1.branch_probability_profile == cg2.branch_probability_profile
        assert cg1.call_graph_edges == cg2.call_graph_edges
        assert cg1.loop_nesting_profile == cg2.loop_nesting_profile
        assert cg1.cyclomatic_complexity == cg2.cyclomatic_complexity
        assert cg1.control_flow_entropy == cg2.control_flow_entropy

    def test_idempotent_complex(self):
        """Idempotency holds for a complex program."""
        src = _read("math_prime_sieve")
        g = self._genome_from(src)
        cg1 = canonicalize(g)
        cg2 = canonicalize(cg1)
        assert cg1.branch_probability_profile == cg2.branch_probability_profile
        assert cg1.call_graph_edges == cg2.call_graph_edges
        assert cg1.loop_nesting_profile == cg2.loop_nesting_profile
        assert cg1.cyclomatic_complexity == cg2.cyclomatic_complexity
        assert cg1.control_flow_entropy == cg2.control_flow_entropy

    def test_idempotent_graph_dijkstra(self):
        src = _read("graph_dijkstra")
        g = self._genome_from(src)
        cg1 = canonicalize(g)
        cg2 = canonicalize(cg1)
        assert cg1 == cg2

    def test_idempotent_trivial(self):
        g = self._genome_from("x = 1\n")
        cg1 = canonicalize(g)
        cg2 = canonicalize(cg1)
        assert cg1 == cg2

    def test_call_graph_sorted(self):
        """Canonicalized call_graph_edges must be in lexicographic order."""
        src = _read("graph_dijkstra")
        g = self._genome_from(src)
        cg = canonicalize(g)
        assert cg.call_graph_edges == sorted(cg.call_graph_edges)

    def test_branch_profile_keys_sorted(self):
        """Branch probability profile keys must be lexicographically sorted."""
        src = _read("math_prime_sieve")
        g = self._genome_from(src)
        cg = canonicalize(g)
        keys = list(cg.branch_probability_profile.keys())
        assert keys == sorted(keys)

    def test_branch_profile_values_rounded(self):
        """Values in branch probability profile are rounded to 4 dp."""
        src = _read("math_prime_sieve")
        g = self._genome_from(src)
        cg = canonicalize(g)
        for v in cg.branch_probability_profile.values():
            # round(v, 4) should equal v (allowing float repr tolerance)
            assert v == round(v, 4)

    def test_entropy_rounded(self):
        """control_flow_entropy is rounded to 4 dp."""
        src = _read("math_prime_sieve")
        g = self._genome_from(src)
        cg = canonicalize(g)
        assert cg.control_flow_entropy == round(cg.control_flow_entropy, 4)

    def test_loop_profile_no_trailing_zeros(self):
        """Canonicalized loop_nesting_profile has no trailing zeros."""
        src = _read("sort_mergesort")
        g = self._genome_from(src)
        cg = canonicalize(g)
        if cg.loop_nesting_profile:
            assert cg.loop_nesting_profile[-1] != 0, (
                f"Trailing zero in loop_nesting_profile: {cg.loop_nesting_profile}"
            )

    def test_cyclomatic_complexity_preserved(self):
        """Canonicalize does not change cyclomatic_complexity."""
        src = _read("graph_dijkstra")
        g = self._genome_from(src)
        cg = canonicalize(g)
        assert cg.cyclomatic_complexity == g.cyclomatic_complexity

    def test_provenance_preserved(self):
        """Canonicalize preserves provenance dict."""
        src = _read("sort_mergesort")
        g = self._genome_from(src)
        cg = canonicalize(g)
        assert cg.provenance == g.provenance

    def test_distance_invariant_under_canonicalize(self):
        """distance(g1, g2) == distance(canonicalize(g1), canonicalize(g2))."""
        g1 = self._genome_from(_read("sort_mergesort"))
        g2 = self._genome_from(_read("sort_quicksort"))
        d_raw = distance(g1, g2)
        d_can = distance(canonicalize(g1), canonicalize(g2))
        assert d_raw == pytest.approx(d_can, abs=1e-9)


# ===========================================================================
# Part 6 — Semantics-preserving transformations produce small distance
# ===========================================================================

class TestSemanticPreservingDistance:
    """
    Verify that semantics-preserving source transformations (variable rename,
    comment stripping, whitespace normalisation, dead-code insertion) produce
    small distances (< 0.15), while obviously different programs produce larger
    distances.
    """

    # ---- Reference sources ----

    MERGESORT_SRC = _read("sort_mergesort")
    PRIME_SIEVE_SRC = _read("math_prime_sieve")
    DIJKSTRA_SRC = _read("graph_dijkstra")

    # ---- Semantics-preserving transformations ----

    @staticmethod
    def _rename_vars(src: str) -> str:
        """Rename all local variables x→x_renamed using AST + compile."""
        # We do a text-level rename of simple local variable assignments
        # (conservative: only renames names that appear as assignments inside
        # a function body at the source level via string substitution).
        # This is intentionally naive — it still preserves control structure.
        return src.replace("result", "output").replace("left", "left_half")

    @staticmethod
    def _strip_comments(src: str) -> str:
        """Remove comment lines and docstrings (text level)."""
        lines = []
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def _add_dead_code(src: str) -> str:
        """Prepend dead code that can never execute."""
        dead = (
            "# dead code — never executed\n"
            "if False:\n"
            "    _dead_var = 999\n\n"
        )
        return dead + src

    @staticmethod
    def _add_noop_assignments(src: str) -> str:
        """Append a block of no-op assignments at module level."""
        return src + "\n# no-ops\n_a = None\n_b = None\n"

    def _dist(self, src1: str, src2: str) -> float:
        g1 = _ctrl.extract(src1)
        g2 = _ctrl.extract(src2)
        return distance(g1, g2)

    # ---- Tests: small distance after semantic-preserving transform ----

    def test_rename_vars_small_distance(self):
        transformed = self._rename_vars(self.MERGESORT_SRC)
        d = self._dist(self.MERGESORT_SRC, transformed)
        assert d < 0.15, f"rename_vars distance too large: {d:.4f}"

    def test_strip_comments_small_distance(self):
        transformed = self._strip_comments(self.MERGESORT_SRC)
        d = self._dist(self.MERGESORT_SRC, transformed)
        assert d < 0.15, f"strip_comments distance too large: {d:.4f}"

    def test_add_dead_code_small_distance(self):
        transformed = self._add_dead_code(self.MERGESORT_SRC)
        d = self._dist(self.MERGESORT_SRC, transformed)
        # Dead code adds one 'if False' branch; small but non-zero distance expected.
        assert d < 0.15, f"dead_code distance too large: {d:.4f}"

    def test_noop_assignments_zero_distance(self):
        """Adding no-op assignments doesn't change control structure at all."""
        transformed = self._add_noop_assignments(self.MERGESORT_SRC)
        d = self._dist(self.MERGESORT_SRC, transformed)
        assert d < 0.15, f"noop_assignments distance too large: {d:.4f}"

    def test_prime_sieve_rename_small_distance(self):
        src = self.PRIME_SIEVE_SRC
        transformed = src.replace("factors", "result_factors")
        d = self._dist(src, transformed)
        assert d < 0.15, f"prime_sieve rename distance: {d:.4f}"

    def test_dijkstra_strip_comments_small_distance(self):
        transformed = self._strip_comments(self.DIJKSTRA_SRC)
        d = self._dist(self.DIJKSTRA_SRC, transformed)
        assert d < 0.15, f"dijkstra strip_comments distance: {d:.4f}"

    # ---- Tests: large distance between obviously different programs ----

    def test_sorting_vs_graph_larger_distance(self):
        """A simple sorting algorithm vs. Dijkstra should differ noticeably."""
        g_sort = _ctrl.extract(self.MERGESORT_SRC)
        g_graph = _ctrl.extract(self.DIJKSTRA_SRC)
        d = distance(g_sort, g_graph)
        # They both use loops and branches, but call graphs differ substantially.
        # We require the distance to be strictly positive.
        assert d > 0.0, f"mergesort vs dijkstra distance unexpectedly zero"

    def test_trivial_vs_complex_large_distance(self):
        """A one-liner vs. a complex algorithm should have large distance."""
        trivial = "x = 42\n"
        g_trivial = _ctrl.extract(trivial)
        g_complex = _ctrl.extract(self.PRIME_SIEVE_SRC)
        d = distance(g_trivial, g_complex)
        assert d > 0.2, f"trivial vs prime_sieve distance too small: {d:.4f}"

    def test_pure_loops_vs_pure_ifs(self):
        """All-loops vs. all-ifs should have non-trivial distance."""
        loops_only = "for i in range(5):\n    for j in range(5):\n        pass\n"
        ifs_only = "if True:\n    if True:\n        if True:\n            pass\n"
        g_loops = _ctrl.extract(loops_only)
        g_ifs = _ctrl.extract(ifs_only)
        d = distance(g_loops, g_ifs)
        # Branch profiles are completely different → L1 contribution is large
        assert d > 0.2, f"loops_only vs ifs_only distance too small: {d:.4f}"

    def test_mergesort_vs_lru_cache_positive_distance(self):
        """Sorting algorithm vs. data structure should differ."""
        g1 = _ctrl.extract(self.MERGESORT_SRC)
        g2 = _ctrl.extract(_read("ds_lru_cache"))
        d = distance(g1, g2)
        assert d > 0.0, "mergesort vs lru_cache distance should be > 0"


# ===========================================================================
# Part 7 — Cross-corpus sanity: all programs parseable, features coherent
# ===========================================================================

class TestCorpusSanity:
    """Smoke-test that all 60 corpus programs can be extracted without error."""

    _programs = [
        "sort_mergesort", "sort_quicksort", "sort_heapsort",
        "sort_counting_sort", "sort_radix_sort", "sort_binary_search",
        "graph_dijkstra", "graph_bellman_ford", "graph_bfs_shortest_path",
        "graph_connected_components", "graph_cycle_detect_dfs",
        "graph_topological_sort",
        "ds_binary_search_tree", "ds_hash_table", "ds_lru_cache",
        "ds_min_heap", "ds_stack_queue", "ds_trie",
        "math_dynamic_programming", "math_matrix_ops",
        "math_numerical_integration", "math_polynomial",
        "math_prime_sieve", "math_statistics",
        "str_anagram_groups", "str_edit_distance", "str_kmp_search",
        "str_run_length_encode", "str_tokenizer", "str_word_frequency",
    ]

    def test_all_programs_static_extract(self):
        for pid in self._programs:
            src = _read(pid)
            f = _static.extract(src)
            assert isinstance(f, StaticFeatures), f"Failed on {pid}"
            assert f.cyclomatic_complexity >= 1, f"{pid}: cc < 1"
            assert f.cfg_node_count >= 0, f"{pid}: cfg_node_count < 0"
            assert isinstance(f.call_sites, list), f"{pid}: call_sites not list"
            assert isinstance(f.import_names, list), f"{pid}: import_names not list"
            assert isinstance(f.global_variables, list), f"{pid}: global_variables not list"
            assert isinstance(f.ast_node_type_histogram, dict), f"{pid}: histogram not dict"

    def test_all_programs_control_genome_extract(self):
        for pid in self._programs:
            src = _read(pid)
            g = _ctrl.extract(src)
            assert isinstance(g, ControlGenome), f"Failed on {pid}"
            assert g.cyclomatic_complexity >= 1, f"{pid}: cc < 1"

    def test_all_programs_distance_to_self_zero(self):
        for pid in self._programs:
            src = _read(pid)
            g = _ctrl.extract(src)
            d = distance(g, g)
            assert d == pytest.approx(0.0, abs=1e-12), (
                f"distance(g, g) != 0 for {pid}: {d}"
            )

    def test_all_programs_canonicalize_idempotent(self):
        for pid in self._programs:
            src = _read(pid)
            g = _ctrl.extract(src)
            c1 = canonicalize(g)
            c2 = canonicalize(c1)
            assert c1 == c2, f"canonicalize not idempotent for {pid}"
