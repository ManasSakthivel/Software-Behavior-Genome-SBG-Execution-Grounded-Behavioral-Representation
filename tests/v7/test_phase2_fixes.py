"""Phase 2 fixes: lossy SAME (A-L1), non-executable changed lines (D-05), input binding (D-06), evidence package + verifier (D-09)."""
import json, subprocess, sys

import pytest

from sbgv7 import records as R
from sbgv7.decide import Evidence, InputEv, decide
from sbgv7.verify import Unverifiable, VerifyError, verify
from .test_core import BASE, EQV, capabilities, go

pytestmark = pytest.mark.skipif(capabilities()["network_denial"]["state"] != "ACTIVE", reason="isolation not enforced here")
LOG = lambda tp, n="out": str(tp / n / "evidence.jsonl")


def ev(*inputs):
    return Evidence(inputs=list(inputs), changed_units=frozenset({("base", 1)}), hit_units=frozenset({("base", 1)}),
                    branch_cov={"base": 1.0, "variant": 1.0}, tampered=False)


# ---------------------------------------------------------------- (1) lossy / unobservable
def test_decide_lossy_same_is_not_evidence():
    assert decide(ev(InputEv("a", "SAME", None, False, True, False, True)))[:3] == ("INSUFFICIENT", None, "unobservable_outcome")
    d = decide(ev(InputEv("a", "SAME", None, False, True, False, True), InputEv("b", "SAME", None, False, False, False, True)))
    assert d[:2] == ("NO_DIVERGENCE_OBSERVED", "S1")  # a clean SAME input remains; the lossy one still caps the level below S2
    assert decide(ev(InputEv("a", "SAME", None, False, None, False, True)))[2] == "unobservable_outcome"  # unknown lossiness is not clean


@pytest.mark.parametrize("ret", ["(lambda: 1)", "list(range(6000))", "N(N(N(N(N()))))"], ids=["opaque", "over_size_cap", "over_depth"])
def test_lossy_s1_is_insufficient(tmp_path, ret):
    src = "class N:\n    def __init__(self, n=None): self.n = n\ndef f(x):\n    if x > 1:\n        return " + ret + "\n    return " + ret + "\n"
    o = go(tmp_path, src, src.replace("x > 1", "x >= 2"), [[5], [0]])
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "unobservable_outcome"), o


def test_lossy_input_does_not_activate_changed_units(tmp_path):
    src = "def f(x):\n    if x > 1:\n        return (lambda: 1)\n    return 2\n"
    o = go(tmp_path, src, src.replace("x > 1", "x >= 2"), [[5]])  # only a lossy input reaches the changed line
    assert o["verdict"] == "INSUFFICIENT" and o["primary"] == "unobservable_outcome" and "changed_region_not_activated" in o["secondary"]


# ---------------------------------------------------------------- (2) D-05 non-executable changed lines
DOC = 'def f(x):\n    """doc A"""\n    return x\n'


def test_docstring_only_is_vacuous_not_a_difference(tmp_path):
    o = go(tmp_path, DOC, DOC.replace("doc A", "doc B"), [[3]])
    assert o["verdict"] == "NO_DIVERGENCE_OBSERVED" and o["witness_id"] is None and o["r_empty"] is True
    s = [r for r in R.read_log(LOG(tmp_path)) if r["kind"] == "SufficiencyRecord"][0]["body"]
    assert s["units_total"] == 0 and s["doc_only_lines"]["base"] == [2]


@pytest.mark.parametrize("var", ["def f(x):\n    # note\n    return x\n", "def f(x):\n\n    return x   \n"], ids=["comment", "whitespace"])
def test_comment_or_whitespace_only(tmp_path, var):
    o = go(tmp_path, "def f(x):\n    return x\n", var, [[3]])
    assert o["verdict"] == "NO_DIVERGENCE_OBSERVED" and o["r_empty"] is True


def test_docstring_observed_through_doc_is_a_real_witness(tmp_path):
    src = 'def f(x):\n    """doc A"""\n    return f.__doc__\n'
    o = go(tmp_path, src, src.replace("doc A", "doc B"), [[3]])  # the difference is observed on a channel, not fabricated from the text
    assert o["verdict"] == "DIVERGENT_OBSERVABLE"


def test_mixed_executable_and_docstring(tmp_path):
    o = go(tmp_path, DOC, DOC.replace("doc A", "doc B").replace("return x", "return x + 0"), [[3]])
    assert o["verdict"] == "NO_DIVERGENCE_OBSERVED" and o["r_empty"] is False
    s = [r for r in R.read_log(LOG(tmp_path)) if r["kind"] == "SufficiencyRecord"][0]["body"]
    assert s["units_total"] == 2 and s["units_hit"] == 2 and s["doc_only_lines"]["base"] == [2]
    o = go(tmp_path, DOC, DOC.replace("doc A", "doc B").replace("return x", "return x + 1"), [[3]], name="o2")
    assert o["verdict"] == "DIVERGENT_OBSERVABLE"
    w = [r for r in R.read_log(LOG(tmp_path, "o2")) if r["kind"] == "Witness"][0]["body"]
    assert w["kinds"] == ["outcome"]


def test_non_executable_non_doc_change_is_unmodelled(tmp_path):
    base = "def f(x):\n    y = (\n        x\n    )\n    return y\n"  # the closing-paren line carries no instruction in base
    o = go(tmp_path, base, base.replace("    )\n", "    ) + 0\n"), [[1]])
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "unmodelled_change")
    o = go(tmp_path, base, base.replace("    )\n", "    ) + 1\n"), [[1]], name="o2")  # a real observed difference still wins
    assert o["verdict"] == "DIVERGENT_OBSERVABLE"


def test_empty_region_no_inputs_still_insufficient(tmp_path):
    o = go(tmp_path, DOC, DOC.replace("doc A", "doc B"), [])
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "no_inputs")


# ---------------------------------------------------------------- (3) D-06 binding
def test_symmetric_binding_failure_is_not_a_same(tmp_path):
    o = go(tmp_path, BASE, EQV, [[1, 2]])  # arity-wrong on both versions
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "no_inputs")
    row = [r for r in R.read_log(LOG(tmp_path)) if r["kind"] == "EvidencePackage"][0]["body"]["rows"][0]
    assert (row["outcome"], row["reason"]) == ("NO_RUN", "invalid_input")
    # a module-level-only change with an invalid input must not reach NDO either
    o = go(tmp_path, "X = 1\ndef f(x):\n    return x\n", "X = 2\ndef f(x):\n    return x\n", [[1, 2]], name="o2")
    assert o["verdict"] == "INSUFFICIENT"
    # a valid input next to it still decides; the invalid one is excluded from the SAME set
    o = go(tmp_path, BASE, EQV, [[1, 2], [5], [0]], name="o3")
    assert o["verdict"] == "NO_DIVERGENCE_OBSERVED"
    assert [r["outcome"] for r in [r for r in R.read_log(LOG(tmp_path, "o3")) if r["kind"] == "EvidencePackage"][0]["body"]["rows"]] == ["NO_RUN", "SAME", "SAME"]


def test_asymmetric_binding_failure_is_api_witness(tmp_path):
    o = go(tmp_path, "def f(x):\n    return x\n", "def f(x, y):\n    return x\n", [[1]])
    assert o["verdict"] == "DIVERGENT_OBSERVABLE"
    assert [r for r in R.read_log(LOG(tmp_path)) if r["kind"] == "Witness"][0]["body"]["kinds"] == ["api"]


def test_decide_invalid_input_never_positive():
    assert decide(ev(InputEv("a", "NO_RUN", None, None, None, False, True, reason="invalid_input")))[2] == "no_inputs"


# ---------------------------------------------------------------- (4) D-09 evidence package + verifier
PAIRS = {"divergent": (BASE, BASE.replace("return x\n", "return x + 1\n"), [[0], [5]]), "s2": (BASE, EQV, [[5], [0]]),
         "s1": (BASE, EQV, [[5]]), "no_inputs": (BASE, EQV, []), "unhit": ("def f(x):\n    if x > 100:\n        return 7\n    return 1\n",
                                                               "def f(x):\n    if x > 100:\n        return 8\n    return 1\n", [[1]]),
         "bind": (BASE, EQV, [[1, 2]]), "doc": (DOC, DOC.replace("doc A", "doc B"), [[3]])}


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    out = {}
    for k, (b, v, i) in PAIRS.items():
        tp = tmp_path_factory.mktemp(k)
        out[k] = (go(tp, b, v, i), tp / "out")
    return out


@pytest.mark.parametrize("k", list(PAIRS))
def test_verify_recomputes_every_pair(runs, k):
    o, d = runs[k]
    r = verify(str(d))
    assert r["verified"] and r["verdict"] == o["verdict"] and r["primary"] == o["primary"]


def _rewrite(d, mutate):
    """Tamper and then RECOMPUTE the hash chain, so only the recomputation can catch it."""
    recs = [dict(r) for r in R.read_log(str(d / "evidence.jsonl"))]
    mutate(recs)
    (d / "verdict.json").unlink(missing_ok=True)  # its log_head would also catch this; test the recomputation itself
    prev = "0" * 64
    with open(d / "evidence.jsonl", "w") as f:
        for i, r in enumerate(recs):
            h = R.sha(prev + R.canon_json(r)); f.write(R.canon_json({"seq": i, "prev": prev, "rec": r, "hash": h}) + "\n"); prev = h


def _copy(runs, k, tmp_path):
    import shutil
    shutil.copytree(runs[k][1], tmp_path / "c"); return tmp_path / "c"


def test_verify_detects_plain_edit_and_truncation(runs, tmp_path):
    d = _copy(runs, "s2", tmp_path)
    t = (d / "evidence.jsonl").read_text()
    (d / "evidence.jsonl").write_text(t.replace('"NO_DIVERGENCE_OBSERVED"', '"INSUFFICIENT"', 1))
    with pytest.raises(VerifyError): verify(str(d))
    (d / "evidence.jsonl").write_text("".join(t.splitlines(True)[:-1]))  # drop the verdict
    with pytest.raises(VerifyError): verify(str(d))


def test_verify_detects_rehashed_forgeries(runs, tmp_path):
    def flip_verdict(recs):
        v = recs[-1]; v["body"] = dict(v["body"], value="INSUFFICIENT", level=None, primary="no_inputs")
    def change_input(recs):
        p = [r for r in recs if r["kind"] == "EvidencePackage"][0]; p["body"]["inputs"][0]["args"] = [99]
    def change_source(recs):
        pv = [r for r in recs if r["kind"] == "ProgramVersion"][0]; pv["meta"] = {"src": "def f(x):\n    return 0\n"}
    def change_obs(recs):
        o = [r for r in recs if r["kind"] == "Observation"][0]; o["body"] = dict(o["body"], stdout="forged")
    def change_row(recs):
        p = [r for r in recs if r["kind"] == "EvidencePackage"][0]; p["body"]["rows"][0]["outcome"] = "CONFIRMED_DIFF"
    for name, m in dict(v=flip_verdict, i=change_input, s=change_source, o=change_obs, r=change_row).items():
        d = tmp_path / name; import shutil; shutil.copytree(runs["s2"][1], d); _rewrite(d, m)
        with pytest.raises(VerifyError): verify(str(d))


def test_verify_divergent_forged_to_same(runs, tmp_path):
    d = _copy(runs, "divergent", tmp_path)
    def m(recs):
        for r in recs:
            if r["kind"] == "Observation" and r["body"].get("ret") == ["int", "6"]:
                r["body"] = dict(r["body"], ret=["int", "-5"])  # make the variant's recorded return equal the base's
    _rewrite(d, m)
    with pytest.raises(VerifyError): verify(str(d))


def test_verify_size_cap_is_unverifiable_not_silently_ok(runs, tmp_path):
    d = _copy(runs, "s2", tmp_path)
    def m(recs):
        for r in recs:
            if r["kind"] == "ProgramVersion": r["meta"] = {"src_omitted": 2 << 20}
    _rewrite(d, m)
    with pytest.raises(Unverifiable): verify(str(d))


def test_verify_cli_exit_codes(runs, tmp_path):
    run = lambda d: subprocess.run([sys.executable, "-m", "sbgv7", "verify", str(d)], capture_output=True, text=True)
    r = run(runs["s2"][1])
    assert r.returncode == 0 and json.loads(r.stdout)["verified"]
    d = _copy(runs, "s2", tmp_path)
    (d / "evidence.jsonl").write_text((d / "evidence.jsonl").read_text().replace("NO_DIVERGENCE", "XX", 1))
    r = run(d)
    assert r.returncode == 1 and "VERIFY FAILED" in r.stderr
    assert run(tmp_path / "missing").returncode == 2


def test_package_holds_evidence_not_just_hashes(runs):
    recs = R.read_log(str(runs["s2"][1] / "evidence.jsonl"))
    p = [r for r in recs if r["kind"] == "EvidencePackage"][0]["body"]
    assert p["inputs"][0]["args"] == [5] and p["config"]["repeat"] and p["env"] and p["policy"] and p["harness_sha"]
    assert all("src" in r["meta"] for r in recs if r["kind"] == "ProgramVersion")
