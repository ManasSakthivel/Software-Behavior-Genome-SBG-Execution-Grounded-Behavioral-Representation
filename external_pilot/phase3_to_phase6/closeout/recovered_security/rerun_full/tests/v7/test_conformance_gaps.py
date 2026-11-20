"""MB-16: conformance test-gap closure (tests only). Each test names the matrix row it closes."""
import sys

import pytest

from sbgv7 import records as R
from sbgv7.config import load_config
from sbgv7.isolation import capabilities
from sbgv7.runner import RunOut, static_phase
from .test_core import BASE, EQV, FAST, cfg, go

NEEDS_SANDBOX = pytest.mark.skipif(capabilities()["network_denial"]["state"] != "ACTIVE",
                                   reason=f"isolation not enforced here: {capabilities()['network_denial']['detail']}")
LOG = lambda tp, n="out": str(tp / n / "evidence.jsonl")
body = lambda tp, kind, n="out": [r for r in R.read_log(LOG(tp, n)) if r["kind"] == kind][0]["body"]


@pytest.mark.skipif(sys.platform != "darwin", reason="darwin-only expectation")
def test_loud_not_skipped_sandbox_must_be_active_on_darwin():  # item 12: this one is never skipped
    assert capabilities()["network_denial"]["state"] == "ACTIVE", capabilities()["network_denial"]


@NEEDS_SANDBOX
def test_capture_truncated_end_to_end(tmp_path):  # B2a / item 1
    src = "def f(x):\n    print('a' * 40000)\n    return 1\n"
    o = go(tmp_path, src, src.replace("40000", "40001"), [[1]])
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "capture_truncated")


def test_alignment_failed_via_static_phase(monkeypatch):  # B2a / item 2
    from sbgv7 import runner
    monkeypatch.setattr(runner, "_regions", lambda b, v: (_ for _ in ()).throw(SyntaxError("stub")))
    ok = RunOut("r", None, sig=[["x", "POSITIONAL_OR_KEYWORD", False]])
    st, _, _ = static_phase(load_config_default(), {"base": b"a", "variant": b"b"}, {"base": ok, "variant": ok})
    assert [c for c, _ in st] == ["alignment_failed"]


def load_config_default():
    from .test_core import load_config_default as d
    return d(None)


@NEEDS_SANDBOX
def test_systemexit_code_is_compared(tmp_path):  # B7a / item 3 (SD-11)
    ex = lambda n: f"def f(x):\n    raise SystemExit({n})\n"
    assert go(tmp_path, ex(3), ex(4), [[1]])["verdict"] == "DIVERGENT_OBSERVABLE"
    o = go(tmp_path, ex(3), ex(3) + "# c\n", [[1]], name="eq")
    assert o["verdict"] != "DIVERGENT_OBSERVABLE"
    rows = body(tmp_path, "EvidencePackage", "eq")["rows"]
    assert rows[0]["outcome"] == "SAME"


@NEEDS_SANDBOX
def test_stderr_only_difference_is_not_observed(tmp_path):  # O3 / item 4 (stderr excluded)
    # newline matters: sys.stderr is line-buffered and the harness ends with os._exit, so an unterminated write never reaches the pipe
    # (the second-stage review found the original 'a'/'b' version passed vacuously: stderr was empty). scripts/mutation_check_mb.py proves stderr is now emitted.
    e = lambda t: f"import sys\ndef f(x):\n    sys.stderr.write({t!r} + '\\n')\n    return 1\n"
    o = go(tmp_path, e("a"), e("b"), [[1]])
    assert o["verdict"] != "DIVERGENT_OBSERVABLE"
    assert body(tmp_path, "EvidencePackage")["rows"][0]["outcome"] == "SAME"


@NEEDS_SANDBOX
def test_witness_locus_unlocalised(tmp_path):  # W5 / item 5
    go(tmp_path, BASE, BASE.replace("return x\n", "return x + 1\n"), [[5]])
    assert body(tmp_path, "Witness")["locus"] == "unlocalised"


def test_defaults_table_item6():  # F1/F9 / item 6
    import json, tempfile, os
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "c.json"); open(p, "w").write("{}")
        c = load_config(p)
    assert c == {"harness": {"c_obs": ["ret", "exc", "side:stdout", "side:file", "side:argmut", "side:global"], "float_tol": {"rel": 0.0, "abs": 0.0},
                             "ordered_mapping": False, "exc_message": "exact_normalised", "api_break_probe": True,
                             "normaliser_id": "N1", "stderr": "excluded", "capture_tier": "L0"},
                 "repeat": {"r_det": 3, "r_replay": 5, "k_alt": 3}, "suff": {"s2_branch_floor": 0.8, "s3_enabled": False},
                 "budget": {"cpu_seconds": 60, "per_run": {"cpu_s": 10, "wall_s": 20, "rss_mib": 2048}}}


@NEEDS_SANDBOX
def test_policy_below_minimum_true_on_darwin(tmp_path):  # I8 / item 7 (strengthens test_core.py:72)
    o = go(tmp_path, BASE, EQV, [[5], [0]])
    assert o["policy_below_minimum"] is (sys.platform == "darwin") is body(tmp_path, "SufficiencyRecord")["policy_below_minimum"]


TWO_BR = ("def f(x):\n    if x > 1:\n        a = 1\n    else:\n        a = 0\n    if x > 10:\n        return a + 1\n    return a\n")
TWO_BR_V = TWO_BR.replace("x > 1:", "x >= 2:").replace("x > 10:", "x >= 11:")
LOOP = "def f(x):\n    s = 0\n    for i in range(x):\n        s += i\n    return s\n"


@NEEDS_SANDBOX
def test_s2_coverage_two_branches(tmp_path):  # S2a / item 8
    o = go(tmp_path, TWO_BR, TWO_BR_V, [[5], [20]], name="a")  # 3 of 4 directions = 0.75 < 0.80
    assert (o["verdict"], o["level"]) == ("NO_DIVERGENCE_OBSERVED", "S1") and set(body(tmp_path, "SufficiencyRecord", "a")["branch_cov"].values()) == {0.75}
    o = go(tmp_path, TWO_BR, TWO_BR_V, [[5], [20], [0]], name="b")
    assert (o["verdict"], o["level"]) == ("NO_DIVERGENCE_OBSERVED", "S2")


@NEEDS_SANDBOX
def test_s2_coverage_loop_for_iter(tmp_path):  # S2a / item 8
    v = LOOP.replace("range(x)", "range(0, x)")
    o = go(tmp_path, LOOP, v, [[0]], name="a")  # loop never iterates: only the exhausted direction
    assert (o["verdict"], o["level"]) == ("NO_DIVERGENCE_OBSERVED", "S1") and body(tmp_path, "SufficiencyRecord", "a")["branch_cov"]["base"] == 0.5
    o = go(tmp_path, LOOP, v, [[3]], name="b")
    assert (o["verdict"], o["level"]) == ("NO_DIVERGENCE_OBSERVED", "S2")


@NEEDS_SANDBOX
def test_deleted_and_inserted_line_units(tmp_path):  # S2a / item 8
    two, one = "def f(x):\n    y = x\n    return x\n", "def f(x):\n    return x\n"
    go(tmp_path, two, one, [[1]], name="del")
    reg = body(tmp_path, "EvidencePackage", "del")["regions"]["units"]
    assert reg["base"] == [2] and reg["variant"] == [] and body(tmp_path, "SufficiencyRecord", "del")["unhit"] == []
    go(tmp_path, one, two, [[1]], name="ins")
    reg = body(tmp_path, "EvidencePackage", "ins")["regions"]["units"]
    assert reg["base"] == [] and reg["variant"] == [2] and body(tmp_path, "SufficiencyRecord", "ins")["unhit"] == []


@NEEDS_SANDBOX
def test_record_kinds_have_documented_evidence_class(tmp_path):  # C2 / item 9
    go(tmp_path, BASE, EQV, [[5]])
    want = {"ProgramVersion": "derived", "Run": "observation", "Observation": "observation", "SufficiencyRecord": "derived",
            "EvidencePackage": "derived", "Verdict": "derived"}
    got = {r["kind"]: r["evidence_class"] for r in R.read_log(LOG(tmp_path))}
    assert got == want
    go(tmp_path, BASE, BASE.replace("return x\n", "return x + 1\n"), [[5]], name="w")
    assert {r["kind"]: r["evidence_class"] for r in R.read_log(LOG(tmp_path, "w"))}["Witness"] == "derived"


def test_trace_raises_chain_error_on_dangling_ref(tmp_path):  # E1 / item 10
    log = R.EvidenceLog(str(tmp_path / "e.jsonl"))
    log.append(R.Rec("Run", refs=["missing_id"], body={"a": 1}))
    rid = R.Rec("Run", refs=["missing_id"], body={"a": 1}).id
    with pytest.raises(R.ChainError, match="dangling"):
        R.trace(str(tmp_path / "e.jsonl"), rid)
