"""Zero-score remediation tests (SBG V4 session).

Covers: legitimate zeros stay zero; unevaluated != zero; no silent fallback; the abstraction-collapse characterisation (V5) and its
V6-graded counterpart; V6 invariants; frozen artifact preservation; label-defect detectors (SP-8 NameError, SP-11 deque);
determinism; numerical edge cases.  No scorer defect that produces zeros was found (ZERO_SCORE_ROOT_CAUSE_V1.md), so these tests
characterise and protect the behaviour rather than fix it.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments" / "final"))

SUM = "def total(values):\n    acc = 0\n    for v in values:\n        acc += v\n    return acc\n"
COUNT = ("def count_pos(values):\n    n = 0\n    for v in values:\n        if v > 0:\n            n += 1\n    return n\n")


def _w(tmp, name, src):
    p = tmp / name
    p.write_text(src)
    return str(p)


def _score(a, b):
    from experiments.final import extraction as ex
    ra, rb = ex.extract_program(a, {}, "output_free_v8"), ex.extract_program(b, {}, "output_free_v8")
    return ex.score_pair(ra, rb), ra, rb


# ------------------------------------------------------------------ legitimate zeros / unevaluated != zero
def test_identical_program_scores_exactly_zero(tmp_path):
    s, *_ = _score(_w(tmp_path, "a.py", SUM), _w(tmp_path, "b.py", SUM))
    assert s["sbg_v5"] == 0.0 and s["sbg_v3"] == 0.0 and s["sbg_state"] == 0.0 and s["sbg_temporal"] == 0.0
    assert s["v5_full"] == 1.0


def test_variable_rename_scores_exactly_zero(tmp_path):
    s, *_ = _score(_w(tmp_path, "a.py", SUM), _w(tmp_path, "b.py", SUM.replace("acc", "total_so_far").replace("values", "xs")))
    assert s["sbg_v5"] == 0.0


def test_unevaluable_side_is_none_not_zero(tmp_path):
    from experiments.final import extraction as ex
    good = ex.extract_program(_w(tmp_path, "a.py", SUM), {}, "output_free_v8")
    bad = ex.extract_program(str(tmp_path / "missing.py"), {}, "output_free_v8")
    assert not bad.ok and bad.failure_kind == "file_missing"
    assert ex.score_pair(good, bad) is None and ex.score_pair(bad, good) is None


def test_syntax_error_variant_is_unevaluated(tmp_path):
    s, ra, rb = _score(_w(tmp_path, "a.py", SUM), _w(tmp_path, "b.py", "def total(:\n"))
    assert s is None and not rb.ok


def test_scored_scores_are_finite_and_in_unit_interval(tmp_path):
    s, *_ = _score(_w(tmp_path, "a.py", SUM), _w(tmp_path, "b.py", SUM.replace("acc += v", "acc += v * v")))
    for k in ("sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state"):
        assert 0.0 <= s[k] <= 1.0 and s[k] == s[k]


def test_scoring_is_deterministic(tmp_path):
    a, b = _w(tmp_path, "a.py", SUM), _w(tmp_path, "b.py", SUM.replace("acc += v", "acc += 2 * v"))
    assert _score(a, b)[0] == _score(a, b)[0]


def test_genuinely_different_behaviour_is_not_zero(tmp_path):
    s, *_ = _score(_w(tmp_path, "a.py", SUM), _w(tmp_path, "b.py", COUNT.replace("count_pos", "total")))
    assert s["sbg_v5"] > 0.0


# ------------------------------------------------------------------ frozen files: unevaluated rows have no scores; no fallback fired
FILES = ["pairs_v9c_train_output_free_v8.jsonl", "pairs_v9c_dev_output_free_v8.jsonl", "pairs_v9c_val_output_free_v8.jsonl",
         "pairs_v8train_output_free_v8.jsonl", "pairs_v8val_output_free_v8.jsonl", "pairs_v8devrescore_output_free_v8.jsonl"]


@pytest.mark.parametrize("name", FILES)
def test_frozen_scored_files_separate_unevaluated_from_zero(name):
    for line in (REPO / "artifacts" / "final" / name).read_text().splitlines():
        r = json.loads(line)
        if r["evaluated"]:
            assert r["scores"]["v5_full"] == 1.0, r["pair_id"]          # d_temporal/d_state fallbacks never fired
            assert 0.0 <= r["scores"]["sbg_v5"] <= 1.0
        else:
            assert "scores" not in r and r.get("failure_kind"), r["pair_id"]   # unevaluated is never a zero score


def test_every_exact_zero_has_all_components_zero():
    for name in FILES[:3]:
        for line in (REPO / "artifacts" / "final" / name).read_text().splitlines():
            r = json.loads(line)
            if r["evaluated"] and r["scores"]["sbg_v5"] == 0:
                sc = r["scores"]
                assert sc["sbg_v3"] == sc["sbg_temporal"] == sc["sbg_state"] == 0, r["pair_id"]


def test_37_percent_figure_reproduces():
    import evaluate_v9 as e
    pop = e.matched_complete(e.load("v9c", "val"))
    z = sum(1 for r in pop if r["scores"]["sbg_v5"] == 0)
    assert (z, len(pop)) == (160, 432)
    ev = json.loads((REPO / "artifacts/paper_evidence/V9_VAL_EVALUATION.json").read_text())
    assert ev["v9c_matched"]["fraction_sbg_v5_exactly_zero"] == round(z / len(pop), 4)


# ------------------------------------------------------------------ abstraction collapse: V5 characterisation, V6 resolution
def test_v5_abstraction_collapses_distinct_values():
    from sbg.v5.state_transition_genome import _repr_to_abstract as a
    assert a("2") == a("1") == a("37")                      # every positive int -> POSITIVE
    assert a("[3.0]") == a("[1.0]")
    assert a("[1, 2]") == a("[1, 2, 3, 4]")                 # every >=2-element container -> MULTI_ELEMENT
    assert a("3.0") == a("1.0")


def test_v6_graded_abstraction_separates_them():
    from sbg.v6.state_transition_genome_v6 import _repr_to_abstract as a
    assert a("2") != a("1") and a("[1, 2]") != a("[1, 2, 3, 4]") and a("3.0") != a("1.0")
    assert a("[3.0]") == a("[1.0]")                         # a one-element list: element value is deliberately not tracked


@pytest.mark.parametrize("r,expected", [("None", "NULL"), ("0", "ZERO"), ("0.0", "ZERO"), ("False", "ZERO"), ("True", "POSITIVE"),
                                        ("[]", "EMPTY_COLLECTION"), ("{}", "EMPTY_COLLECTION"), ("''", "EMPTY_COLLECTION"),
                                        ("<Foo object at 0x1>", "NON_NULL"), ("nan", "UNKNOWN"), ("inf", "UNKNOWN")])
def test_v6_preserves_v5_labels_where_values_are_not_graded(r, expected):
    from sbg.v6.state_transition_genome_v6 import _repr_to_abstract as a
    assert a(r) == expected


def test_v6_abstraction_is_total_and_deterministic():
    from sbg.v6.state_transition_genome_v6 import _repr_to_abstract as a
    for r in ["", " ", "(", "[", "'", "-", "1e999", "-0", "-0.0", "+5", "1_000", "[[[[", "{'a': (1, 2), 'b': [3]}", "x" * 500, "[" + "1," * 80]:
        assert isinstance(a(r), str) and a(r) == a(r)
    assert a("-0") == "ZERO" and a("-0.0") == "ZERO"
    assert a("[" + "1, " * 80) == "COL_LEN=9+"               # truncated repr (tracer caps at 100 chars)


def test_v6_distance_is_identity_symmetric_and_bounded():
    from sbg.v6.state_transition_genome_v6 import StateTransitionGenome, StateTransitionGraph
    g = StateTransitionGenome()
    a = StateTransitionGraph(transitions={(0, "ZERO", "state_mutation", "POS=1"): 3, (0, "POS=1", "state_mutation", "POS=2"): 1})
    b = StateTransitionGraph(transitions={(0, "ZERO", "state_mutation", "POS=1"): 1})
    assert g.distance(a, a) == 0.0 and g.distance(a, b) == g.distance(b, a) and 0.0 < g.distance(a, b) <= 1.0
    assert g.distance(StateTransitionGraph(), StateTransitionGraph()) == 0.0        # empty/empty: legitimately 0


def test_v6_state_distance_detects_count_change_that_v5_misses(tmp_path):
    """Loop bound 2 vs 3: every counter value stays POSITIVE after its first step, so V5's sign abstraction records identical
    transitions up to multiplicity; the V6 graded abstraction sees the extra POS=2->POS=3 step.  Same traces feed both genomes."""
    import re
    from experiments.final.entry_policy import select_entry_structural  # noqa: F401
    from sbg.extraction.dynamic.tracer import Tracer
    from sbg.v5.state_transition_genome import StateTransitionGenome as G5
    from sbg.v6.state_transition_genome_v6 import StateTransitionGenome as G6

    def traces(src, name):
        ns = {}
        exec(compile(src, name, "exec"), ns)
        return Tracer().trace(ns["f"], [1, 2], max_events=5000, timeout_s=2.0, max_timeouts=2)

    base = "def f(n):\n    c = 0\n    while c < 2:\n        c += 1\n    return c\n"
    ta, tb = traces(base, "a"), traces(base.replace("< 2", "< 3"), "b")
    re.purge()
    d5 = G5().distance(G5().extract(ta), G5().extract(tb))
    d6 = G6().distance(G6().extract(ta), G6().extract(tb))
    assert d6 > 0.0 and d6 >= d5


def test_v5_files_unmodified_by_v6():
    """V6 is a versioned copy: the frozen V5 module must still define the sign abstraction."""
    src = (REPO / "sbg/v5/state_transition_genome.py").read_text()
    assert "AV_POSITIVE if v > 0 else AV_NEGATIVE" in src and "COL_LEN" not in src


# ------------------------------------------------------------------ label-defect detectors (SP-8 NameError, SP-11 deque)
def test_audit_flags_sp8_undefined_helper_and_sp11_type_change():
    from audit_external_negatives import undefined_names
    base = "def f(xs):\n    return sorted(xs)\n"
    sp8_bad = "def f(xs):\n    return _extracted_1_0(xs)\n"
    assert undefined_names(base) == [] and undefined_names(sp8_bad) == ["_extracted_1_0"]


def test_equivalent_label_audit_artifact_is_consistent():
    a = json.loads((REPO / "artifacts/paper_evidence/EQUIVALENT_LABEL_AUDIT.json").read_text())
    assert "TEST split is deliberately NOT audited" in a["status"]
    assert set(a["splits"]) == {"train", "dev", "val"}


# ------------------------------------------------------------------ frozen-artifact preservation
def test_frozen_v9_val_files_match_freeze():
    fz = json.loads((REPO / "artifacts/final/FREEZE_V9.json").read_text())
    sh = lambda p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()                 # noqa: E731
    assert sh("artifacts/final/pairs_v9c_val_output_free_v8.jsonl") == fz["scored_v9c_val_sha256"]
    assert sh("artifacts/final/pairs_v8val_output_free_v8.jsonl") == fz["scored_v8_val_sha256"]
    assert sh("artifacts/final/V9_MODELS_FROZEN.json") == fz["models_sha256"]
