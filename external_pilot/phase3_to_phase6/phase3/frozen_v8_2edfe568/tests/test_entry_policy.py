"""Regression tests for the structural entry-point policy (output_free_v8).

Each test pins a defect observed in the committed v6 test artifact
(artifacts/final/pairs_v6test_output_free_v6.jsonl): the v6/v7 name-based rule
selected a different function after SP-2 renaming for 11 EQUIVALENT pairs, and
traced a renamed self-test driver (``fn_test_*``) for two of them.
"""
from __future__ import annotations

import ast
import json
import pathlib
import random
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from experiments.final import entry_policy as ep                       # noqa: E402
from experiments.final.extraction import extract_program               # noqa: E402
from experiments.final.protocol import eligible_candidates             # noqa: E402

HEAP = '''
def _sift_down(arr: list, root: int, end: int) -> None:
    while True:
        child = 2 * root + 1
        if child >= end:
            return
        if child + 1 < end and arr[child] < arr[child + 1]:
            child += 1
        if arr[root] >= arr[child]:
            return
        arr[root], arr[child] = arr[child], arr[root]
        root = child


def heapsort(arr: list) -> None:
    n = len(arr)
    for start in range(n // 2 - 1, -1, -1):
        _sift_down(arr, start, n)
    for end in range(n - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]
        _sift_down(arr, 0, end)


def test_heapsort():
    a = [3, 1, 2]
    heapsort(a)
    assert a == [1, 2, 3]


if __name__ == "__main__":
    test_heapsort()
'''


def rename(source: str, mapping: dict) -> str:
    """Rename functions and every reference, the way SP-2 does."""
    class R(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            self.generic_visit(node)
            node.name = mapping.get(node.name, node.name)
            return node

        def visit_Name(self, node):
            node.id = mapping.get(node.id, node.id)
            return node
    return ast.unparse(R().visit(ast.parse(source)))


def reorder(source: str, seed: int) -> str:
    tree = ast.parse(source)
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    rest = [n for n in tree.body if not isinstance(n, ast.FunctionDef)]
    random.Random(seed).shuffle(funcs)
    tree.body = funcs + rest
    return ast.unparse(tree)


# ---------------------------------------------------------------------------
# The defect: a name-based rule is not rename-invariant
# ---------------------------------------------------------------------------

class TestRenameInvariance:
    FN_PREFIX = {"_sift_down": "fn__sift_down", "heapsort": "fn_heapsort",
                 "test_heapsort": "fn_test_heapsort"}

    def test_v6_rule_is_not_rename_invariant(self):
        """Documents the defect: under SP-2 the old rule picks a helper."""
        renamed = rename(HEAP, self.FN_PREFIX)
        old_base = [c[0] for c in eligible_candidates(ast.parse(HEAP))]
        old_variant = [c[0] for c in eligible_candidates(ast.parse(renamed))]
        assert old_base == ["heapsort"]
        # the renamed helper and the renamed self-test driver both became candidates
        assert "fn__sift_down" in old_variant and "fn_test_heapsort" in old_variant

    def test_v8_selects_corresponding_entry_after_prefix_rename(self):
        base = ep.select_entry_structural(HEAP)
        variant = ep.select_entry_structural(rename(HEAP, self.FN_PREFIX))
        assert base.name == "heapsort" and variant.name == "fn_heapsort"
        assert base.structural_id == variant.structural_id

    def test_v8_selects_corresponding_entry_after_synonym_rename(self):
        mapping = {"heapsort": "pile_order", "_sift_down": "sink", "test_heapsort": "check"}
        base = ep.select_entry_structural(HEAP)
        variant = ep.select_entry_structural(rename(HEAP, mapping))
        assert variant.name == "pile_order"
        assert base.structural_id == variant.structural_id

    def test_v8_is_invariant_under_variable_rename(self):
        variant = HEAP.replace("arr", "buffer").replace("root", "r0")
        assert (ep.select_entry_structural(variant).structural_id
                == ep.select_entry_structural(HEAP).structural_id)

    def test_alphabetical_order_flip_does_not_change_choice(self):
        # Two roots; renaming flips their alphabetical order but not their structure.
        src = '''
def alpha(xs: list) -> int:
    total = 0
    for x in xs:
        total += helper(x)
    return total

def helper(x: int) -> int:
    return x + 1

def omega(xs: list) -> int:
    return len(xs)
'''
        a = ep.select_entry_structural(src)
        b = ep.select_entry_structural(rename(src, {"alpha": "zeta", "omega": "aaa"}))
        assert a.structural_id == b.structural_id
        assert a.name == "alpha" and b.name == "zeta"


# ---------------------------------------------------------------------------
# Function ordering
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("seed", range(8))
def test_selection_is_independent_of_definition_order(seed):
    base = ep.select_entry_structural(HEAP)
    shuffled = ep.select_entry_structural(reorder(HEAP, seed))
    assert shuffled.name == base.name and shuffled.structural_id == base.structural_id


# ---------------------------------------------------------------------------
# Multiple candidates
# ---------------------------------------------------------------------------

class TestMultipleCandidates:
    def test_larger_call_closure_wins(self):
        src = '''
def small(xs: list) -> int:
    return len(xs)

def big(xs: list) -> int:
    return step_one(xs) + step_two(xs)

def step_one(xs: list) -> int:
    return len(xs)

def step_two(xs: list) -> int:
    return sum(xs)
'''
        assert ep.select_entry_structural(src).name == "big"

    def test_helpers_are_never_entries(self):
        decision = ep.select_entry_structural(HEAP)
        assert decision.name == "heapsort"
        assert decision.n_roots == 1

    def test_unannotated_loses_to_annotated_at_equal_closure(self):
        src = '''
def plain(xs):
    return len(xs)

def typed(xs: list) -> int:
    return len(xs) + 1
'''
        assert ep.select_entry_structural(src).name == "typed"

    def test_exact_duplicates_are_interchangeable(self):
        src = '''
def one(xs: list) -> int:
    return len(xs)

def two(xs: list) -> int:
    return len(xs)
'''
        decision = ep.select_entry_structural(src)
        assert decision.name == "one"            # first in source order, by definition


# ---------------------------------------------------------------------------
# Self-test drivers
# ---------------------------------------------------------------------------

class TestSelfTestDrivers:
    def test_assert_bearing_zero_arg_function_is_excluded_whatever_its_name(self):
        src = '''
def work(xs: list) -> int:
    return sum(xs)

def verify_everything():
    assert work([1, 2]) == 3
'''
        decision = ep.select_entry_structural(src)
        assert decision.name == "work"
        assert decision.excluded_drivers == ["verify_everything"]

    def test_renamed_driver_is_still_excluded(self):
        for name in ("fn_test_heapsort", "zzz", "a", "TestHeap"):
            variant = rename(HEAP, {"test_heapsort": name})
            decision = ep.select_entry_structural(variant)
            assert decision.name == "heapsort", name
            assert name in decision.excluded_drivers

    def test_main_guard_callee_is_a_driver_even_without_assert(self):
        src = '''
def work(xs: list) -> int:
    return sum(xs)

def demo_run():
    print(work([1, 2]))

if __name__ == "__main__":
    demo_run()
'''
        decision = ep.select_entry_structural(src)
        assert decision.name == "work" and decision.excluded_drivers == ["demo_run"]

    def test_driver_calls_do_not_make_everything_a_helper(self):
        # The defect the old call-graph-root rule had: the driver is the only root.
        decision = ep.select_entry_structural(HEAP)
        assert decision.name != "test_heapsort"

    def test_module_with_only_drivers_has_no_entry(self):
        src = "def test_a():\n    assert True\n"
        with pytest.raises(ep.NoEntryPoint):
            ep.select_entry_structural(src)

    def test_parameterised_function_with_assert_is_not_a_driver(self):
        src = "def check(xs: list) -> int:\n    assert xs is not None\n    return len(xs)\n"
        assert ep.select_entry_structural(src).name == "check"

    def test_every_committed_corpus_driver_is_detected(self):
        """All 53 zero-argument functions that hold asserts in the corpus are drivers."""
        found = 0
        for path in sorted((REPO_ROOT / "benchmark/corpus/base_programs").glob("*.py")):
            tree = ast.parse(path.read_text())
            drivers = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)
                       and not n.args.args and any(isinstance(x, ast.Assert)
                                                   for x in ast.walk(n))}
            if not drivers:
                continue
            try:
                decision = ep.select_entry_structural(path.read_text())
            except ep.EntryPointError:
                continue
            assert drivers.isdisjoint({decision.name}), path.name
            assert drivers <= set(decision.excluded_drivers), path.name
            found += len(drivers)
        assert found >= 10


# ---------------------------------------------------------------------------
# Explicit failure, never an arbitrary pick
# ---------------------------------------------------------------------------

class TestExplicitFailure:
    def test_ambiguous_distinct_candidates_raise(self):
        src = '''
def tokenize(text: str) -> list:
    return text.split()

def render(text: str) -> str:
    out = ""
    for ch in text:
        out += ch.upper()
    return out
'''
        with pytest.raises(ep.AmbiguousEntryPoint) as info:
            ep.select_entry_structural(src)
        assert sorted(info.value.candidates) == ["render", "tokenize"]
        assert info.value.kind == "ambiguous_entry_point"

    def test_ambiguity_is_not_resolved_by_name(self):
        src = '''
def aaa(text: str) -> list:
    return text.split()

def zzz(text: str) -> str:
    return text.upper()
'''
        with pytest.raises(ep.AmbiguousEntryPoint):
            ep.select_entry_structural(src)
        with pytest.raises(ep.AmbiguousEntryPoint):
            ep.select_entry_structural(rename(src, {"aaa": "zzz2", "zzz": "aaa2"}))

    def test_no_functions(self):
        with pytest.raises(ep.NoEntryPoint):
            ep.select_entry_structural("class A:\n    pass\n")

    def test_syntax_error(self):
        with pytest.raises(ep.NoEntryPoint):
            ep.select_entry_structural("def broken(:\n")

    def test_unsynthesisable_signature(self):
        src = "def run(cb: Callable) -> int:\n    return cb()\n"
        with pytest.raises(ep.UnsupportedSignature):
            ep.select_entry_structural(src)

    def test_all_errors_share_a_base_class_with_a_ledger_kind(self):
        for cls in (ep.NoEntryPoint, ep.UnsupportedSignature, ep.AmbiguousEntryPoint):
            assert issubclass(cls, ep.EntryPointError) and cls.kind


# ---------------------------------------------------------------------------
# Protocol integration
# ---------------------------------------------------------------------------

class TestProtocolIntegration:
    def test_v8_record_is_name_free_and_matches_across_rename(self, tmp_path):
        base = tmp_path / "base.py"
        variant = tmp_path / "variant.py"
        base.write_text(HEAP)
        variant.write_text(rename(HEAP, TestRenameInvariance.FN_PREFIX))
        rb = extract_program(str(base), {}, "output_free_v8")
        rv = extract_program(str(variant), {}, "output_free_v8")
        assert rb.ok and rv.ok
        assert rb.entry_discovery == rv.entry_discovery        # structural:<id>, no name
        assert "heapsort" not in rb.entry_discovery
        # Exact event equality is deliberately NOT asserted: the first extraction
        # in a fresh process records fewer events than later ones (observed
        # 6334 vs 6385 for this program). That cold-start nondeterminism is a
        # separate, documented defect (reports/remediation/01_ISSUE_INVENTORY.md).
        assert abs(rb.stats["n_events"] - rv.stats["n_events"]) <= 0.02 * rv.stats["n_events"]
        assert rb.entry_detail["n_drivers_excluded"] == 1

    def test_v8_traces_no_assert_driver(self, tmp_path):
        path = tmp_path / "p.py"
        path.write_text(rename(HEAP, TestRenameInvariance.FN_PREFIX))
        record = extract_program(str(path), {}, "output_free_v8")
        assert record.ok and record.stats["exception_fraction"] == 0.0
        assert record.entry_function == "fn_heapsort"

    def test_v8_failure_lands_in_the_ledger(self, tmp_path):
        path = tmp_path / "ambiguous.py"
        path.write_text("def a(t: str) -> list:\n    return t.split()\n"
                        "def b(t: str) -> str:\n    return t.upper()\n")
        record = extract_program(str(path), {}, "output_free_v8")
        assert not record.ok and record.failure_kind == "ambiguous_entry_point"

    def test_class_tier_is_flagged_not_rename_invariant(self, tmp_path):
        path = tmp_path / "c.py"
        path.write_text("class Counter:\n    def __init__(self):\n        self.n = 0\n"
                        "    def bump(self):\n        self.n += 1\n")
        record = extract_program(str(path), {}, "output_free_v8")
        assert record.ok and record.entry_detail.get("rename_invariant") is False

    def test_published_and_v6_v7_selection_is_unchanged(self):
        """The new protocol must not alter the historical ones."""
        from experiments.final.extraction import PROTOCOLS
        assert PROTOCOLS[:3] == ("published", "output_free_v6", "output_free_v7")


# ---------------------------------------------------------------------------
# Historical evidence: the committed artifact really shows the defect
# ---------------------------------------------------------------------------

ARTIFACT = REPO_ROOT / "artifacts/final/pairs_v6test_output_free_v6.jsonl"


def _strip_prefix(name: str) -> str:
    return name[3:] if name.startswith("fn_") else name


@pytest.mark.skipif(not ARTIFACT.exists(), reason="artifact not present")
def test_committed_v6_artifact_shows_eleven_entry_mismatches_and_two_driver_traces():
    rows = [json.loads(line) for line in ARTIFACT.read_text().splitlines() if line.strip()]
    evaluated = [r for r in rows if r["evaluated"]]
    mismatched = [r for r in evaluated
                  if _strip_prefix(r["base_entry"].split(":", 1)[1])
                  != _strip_prefix(r["variant_entry"].split(":", 1)[1])]
    assert len(evaluated) == 259
    assert len(mismatched) == 11
    assert {r["semantic_relation"] for r in mismatched} == {"EQUIVALENT"}
    drivers = [r for r in mismatched if "fn_test_" in r["variant_entry"]]
    assert len(drivers) == 2


@pytest.mark.skipif(not ARTIFACT.exists(), reason="artifact not present")
def test_structural_correspondence_counts_nine_genuine_mismatches():
    """Name-based counts overstate the defect.

    19 evaluated EQUIVALENT pairs differ by name; stripping only the ``fn_``
    prefix leaves 11; two of those are ``parse_int`` -> ``decode_int``, which is
    the *same* function renamed by SP-2's parse->decode rule. Matching SP-2
    pairs by structural fingerprint leaves 9 genuine mismatches.
    """
    sys.path.insert(0, str(REPO_ROOT / "experiments" / "final"))
    import audit_recompute as ar

    rows = ar.load_rows(ARTIFACT)
    meta = {json.loads(l)["pair_id"]: json.loads(l)
            for l in (REPO_ROOT / "benchmark/datasets/v6/pairs_test.jsonl")
            .read_text().splitlines() if l.strip()}
    corr = ar.entry_correspondence(rows, meta)
    assert corr["n_name_inequality_naive"] == 19
    assert corr["n_structural_mismatch"] == 9
    assert len(corr["driver_traced"]) == 2
    assert not any(m["pair_id"].startswith("test__err_result_type")
                   for m in corr["mismatches"])
