import pathlib, sys, textwrap
import pytest
REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from sbgv6.observe import PythonAdapter
from sbgv6.distance import pair_record, UNKNOWN, ACTIVATED, NOT_ACTIVATED
from sbgv6 import features as F

BASE = '''
def total(xs: list[int]) -> int:
    acc = 0
    for v in xs:
        if v > 2:
            acc += v
    return acc
'''
import re
RENAMED = re.sub(r"\bv\b", "item", BASE.replace("total", "summ").replace("acc", "running"))
COMMENTED = "# header comment\n\n" + BASE.replace("    return acc", "    # done\n\n    return acc")
MUTANT = BASE.replace("v > 2", "v > 4")
DEADCODE = BASE.replace("    acc = 0", "    acc = 0\n    if False:\n        acc = -1")
NONDET = '''
import random
def total(xs: list[int]) -> int:
    return len(xs) + random.randint(0, 10**6)
'''
LOOP = '''
def total(xs: list[int]) -> int:
    while True:
        pass
'''


def obs(tmp_path, name, src):
    p = tmp_path / f"{name}.py"
    p.write_text(textwrap.dedent(src))
    return PythonAdapter().observe(str(p))


def rec(tmp_path, a, b):
    return pair_record(obs(tmp_path, "a", a), obs(tmp_path, "b", b))


def test_identity_is_zero_and_activated_or_not(tmp_path):
    r = rec(tmp_path, BASE, BASE)
    assert r["status"] in (ACTIVATED, NOT_ACTIVATED)
    assert r["d_A"] == 0 and r["d_B"] == 0 and r["d_C"] == 0 and r["d_v6"] == 0
    assert r["status"] == NOT_ACTIVATED        # no changed lines -> change never executed


@pytest.mark.parametrize("variant", [RENAMED, COMMENTED])
def test_rename_and_format_invariance(tmp_path, variant):
    r = rec(tmp_path, BASE, variant)
    assert r["status"] != UNKNOWN
    assert r["d_A"] == pytest.approx(0, abs=1e-9)
    assert r["d_B"] == pytest.approx(0, abs=1e-9)
    assert r["d_C"] == pytest.approx(0, abs=1e-9)
    assert r["delta_out"] == 0


def test_mutant_is_detected_by_output_and_structure(tmp_path):
    r = rec(tmp_path, BASE, MUTANT)
    assert r["delta_out"] > 0
    assert r["d_v6"] > 0 and r["status"] == ACTIVATED


def test_dead_code_not_executed_keeps_behaviour(tmp_path):
    r = rec(tmp_path, BASE, DEADCODE)
    assert r["delta_out"] == 0
    # KNOWN LIMITATION (documented): an inert `if False:` guard still executes as a traced line,
    # so the transition block B moves slightly (edit-size-like sensitivity). It must stay small.
    assert 0 < r["d_B"] < 0.2


def test_nondeterminism_gives_unknown_not_zero(tmp_path):
    r = rec(tmp_path, NONDET, NONDET)
    assert r["status"] == UNKNOWN and r["d_v6"] is None
    assert any("nondeterministic" in x for x in r["reasons"])


def test_instrumentation_failure_gives_unknown(tmp_path):
    r = rec(tmp_path, BASE, "def broken(:\n")
    assert r["status"] == UNKNOWN and r["d_v6"] is None and r["d_A"] is None


def test_nonterminating_is_not_equivalence(tmp_path):
    r = rec(tmp_path, BASE, LOOP)
    assert r["status"] == UNKNOWN and r["d_v6"] is None


def test_jsd_properties():
    from collections import Counter
    p, q = Counter({"a": 3, "b": 1}), Counter({"a": 1, "b": 3})
    assert F.jsd(p, p) == 0 and F.jsd(p, q) == pytest.approx(F.jsd(q, p))
    assert 0 < F.jsd(p, q) < 1 and F.jsd(Counter({"a": 1}), Counter({"b": 1})) == pytest.approx(1)
    assert F.jsd(Counter(), p) is None            # undefined, not zero


def test_absval():
    assert F.absval("[1, 2]") == ("list", None, 2) and F.absval("-3")[1] == -3
    assert F.absval("None")[0] == "NoneType" and F.absval("<obj at 0x1>")[0] == "obj"
