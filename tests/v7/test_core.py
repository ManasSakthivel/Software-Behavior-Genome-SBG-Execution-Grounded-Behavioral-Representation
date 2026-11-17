"""V7-B core tests: every verdict, S1/S2, nondeterminism, crash, timeout, missing evidence, signature change,
invalid input, reproducibility, evidence chain, and a property test on decide()."""
import json, random, subprocess, sys, textwrap
import pytest

from sbgv7 import records as R
from sbgv7.compare import compare
from sbgv7.config import ConfigError, load_config, load_inputs
from sbgv7.decide import Evidence, InputEv, decide, RANK
from sbgv7.isolation import capabilities
from sbgv7.runner import Ineligible, compare_versions, process_input

pytestmark = pytest.mark.skipif(capabilities()["network_denial"]["state"] != "ACTIVE", reason="isolation not enforced here")
FAST = {"repeat": {"r_det": 2, "r_replay": 2, "k_alt": 1}, "budget": {"per_run": {"wall_s": 3, "cpu_s": 3}}}


def cfg(**over):
    import copy
    c = copy.deepcopy(FAST)
    for k, v in over.items():
        c.setdefault(k, {}).update(v)
    p = c
    return p


def _load(tmp, c):
    f = tmp / "c.json"; f.write_text(json.dumps(c)); return load_config(str(f))


def go(tmp_path, base, var, inputs, entry="f", config=None, name="out"):
    (tmp_path / "base.py").write_text(textwrap.dedent(base)); (tmp_path / "var.py").write_text(textwrap.dedent(var))
    inp = [{"args": a} if isinstance(a, list) else a for a in inputs]
    (tmp_path / "i.json").write_text(json.dumps(inp))
    return compare_versions(str(tmp_path / "base.py"), str(tmp_path / "var.py"), entry, load_inputs(str(tmp_path / "i.json")),
                            _load(tmp_path, config or FAST), str(tmp_path / name))


BASE = "def f(x):\n    if x > 1:\n        return x\n    return -x\n"
EQV = "def f(x):\n    if x >= 2:\n        return x\n    return -x\n"  # same behaviour on ints, different changed line


# ---------------------------------------------------------------- verdicts
def test_divergent_return_with_trace(tmp_path):
    o = go(tmp_path, BASE, BASE.replace("return x\n", "return x + 1\n"), [[0], [5]])
    assert o["verdict"] == "DIVERGENT_OBSERVABLE" and o["witness_id"]
    log = str(tmp_path / "out" / "evidence.jsonl")
    t = R.trace(log, o["verdict_id"])
    kinds = {r["kind"] for r in t.values()}
    assert {"Verdict", "Witness", "Run", "Observation", "ProgramVersion"} <= kinds
    w = t[o["witness_id"]]
    assert w["body"]["kinds"] == ["outcome"] and w["body"]["replay_set"] and all(r["run_id"] in t for r in w["body"]["replay_set"])
    assert all(r["kind"] == "Run" for i, r in t.items() if i in {x["run_id"] for x in w["body"]["replay_set"]})


def test_divergent_exception_stdout_and_global(tmp_path):
    assert go(tmp_path, "def f(x):\n    return 1\n", "def f(x):\n    raise ValueError('a')\n", [[1]])["verdict"] == "DIVERGENT_OBSERVABLE"
    o = go(tmp_path, "def f(x):\n    print('a')\n    return 1\n", "def f(x):\n    print('b')\n    return 1\n", [[1]], name="o2")
    assert o["verdict"] == "DIVERGENT_OBSERVABLE"
    o = go(tmp_path, "G=0\ndef f(x):\n    global G\n    G = 1\n    return 1\n", "G=0\ndef f(x):\n    global G\n    G = 2\n    return 1\n", [[1]], name="o3")
    assert o["verdict"] == "DIVERGENT_OBSERVABLE"
    w = R.read_log(str(tmp_path / "o3" / "evidence.jsonl"))
    assert [r for r in w if r["kind"] == "Witness"][0]["body"]["kinds"] == ["side_effect"]


def test_s1_and_s2(tmp_path):
    o = go(tmp_path, BASE, EQV, [[5]])  # only one direction of the changed branch
    assert (o["verdict"], o["level"]) == ("NO_DIVERGENCE_OBSERVED", "S1")
    o = go(tmp_path, BASE, EQV, [[5], [0]], name="o2")  # both directions
    assert (o["verdict"], o["level"]) == ("NO_DIVERGENCE_OBSERVED", "S2")
    suff = R.read_log(str(tmp_path / "o2" / "evidence.jsonl"))
    s = [r for r in suff if r["kind"] == "SufficiencyRecord"][0]
    assert s["status"] == "uncertain" and s["evidence_class"] == "derived" and s["body"]["policy_below_minimum"] in (True, False)
    assert s["body"]["units_hit"] == s["body"]["units_total"] > 0


def test_s1_not_s2_when_lossy(tmp_path):
    src = "class N: pass\ndef f(x):\n    a = N(); a.n = N(); a.n.n = N(); a.n.n.n = N()\n    return a\n"
    o = go(tmp_path, src, src.replace("N(); a.n =", "N();  a.n ="), [[1]])
    # spec amendment A-L1: equality on a lossy canonical form is no evidence of no divergence (was NDO S1, now no usable SAME input)
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "unobservable_outcome")


def test_s0_never_with_no_divergence(tmp_path):
    o = go(tmp_path, BASE, EQV, [[0]])  # changed line `if x > 1` runs; fine. Make an unhit change instead:
    src = "def f(x):\n    if x > 100:\n        return 7\n    return 1\n"
    o = go(tmp_path, src, src.replace("return 7", "return 8"), [[1]], name="o2")
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "changed_region_not_activated")
    s = [r for r in R.read_log(str(tmp_path / "o2" / "evidence.jsonl")) if r["kind"] == "SufficiencyRecord"][0]
    assert s["body"]["level"] == "S0" and o["level"] is None


# ---------------------------------------------------------------- insufficient reasons
def test_import_error_and_entry_missing_and_no_inputs(tmp_path):
    assert go(tmp_path, BASE, "def f(x:\n", [[1]])["primary"] == "import_error"
    o = go(tmp_path, BASE, "def g(x):\n    return 1\n", [[1]], name="o2")
    assert o["primary"] == "unsupported_signature"
    o = go(tmp_path, BASE, EQV, [], name="o3")
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "no_inputs")


def test_signature_change(tmp_path):
    o = go(tmp_path, "def f(x):\n    return x\n", "def f(x, y):\n    return x\n", [[1]])  # api break probe: bind fails on variant only
    assert o["verdict"] == "DIVERGENT_OBSERVABLE"
    w = [r for r in R.read_log(str(tmp_path / "out" / "evidence.jsonl")) if r["kind"] == "Witness"][0]
    assert w["body"]["kinds"] == ["api"]
    c = {"harness": {"api_break_probe": False}}
    o = go(tmp_path, "def f(x):\n    return x\n", "def f(x, y):\n    return x\n", [[1]], config=cfg(**c), name="o2")
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "unsupported_signature")
    # compatible: default added, proceeds to execution
    o = go(tmp_path, "def f(x):\n    return x\n", "def f(x, y=0):\n    return x\n", [[1]], name="o3")
    assert o["verdict"] == "NO_DIVERGENCE_OBSERVED"


def test_nondeterministic_quarantined(tmp_path):
    src = "import os\ndef f(x):\n    return os.urandom(8).hex()\n"
    o = go(tmp_path, src, src.replace("(8)", "(9)"), [[1]], config=cfg(repeat={"r_det": 3}))
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "nondeterministic")


def test_crash_reproduced_is_witness(tmp_path):
    crash = "import os\ndef f(x):\n    os.kill(os.getpid(), 11)\n"
    o = go(tmp_path, "def f(x):\n    return 1\n", crash, [[1]])
    assert o["verdict"] == "DIVERGENT_OBSERVABLE"
    o = go(tmp_path, crash, crash.replace("11", "11 "), [[1]], name="o2")  # both crash identically
    assert o["verdict"] != "DIVERGENT_OBSERVABLE"


def test_timeout_asymmetric_and_both(tmp_path):
    c = cfg(budget={"per_run": {"wall_s": 1, "cpu_s": 1}})
    c["budget"]["cpu_seconds"] = 60
    hang = "def f(x):\n    while True:\n        pass\n"
    o = go(tmp_path, "def f(x):\n    return 1\n", hang, [[1]], config=c)
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "resource_limit")
    o = go(tmp_path, hang, hang.replace("pass", "x = 1"), [[1]], config=c, name="o2")
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "resource_limit")  # both limit => NO_RUN is a resource_limit blocker, never a witness


def test_budget_exhausted(tmp_path):
    c = cfg(); c["budget"]["cpu_seconds"] = 0.001
    o = go(tmp_path, BASE, EQV, [[5], [0]], config=c)
    assert o["verdict"] == "INSUFFICIENT" and "budget_exhausted_s0" in [o["primary"], *o["secondary"]]


def test_degenerate_unobservable(tmp_path):
    o = go(tmp_path, "def f(x):\n    pass\n", "def f(x):\n    y = 1\n", [[1]])
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "unobservable_outcome")


def test_identical_is_ineligible(tmp_path):
    with pytest.raises(Ineligible):
        go(tmp_path, BASE, BASE, [[1]])


# ---------------------------------------------------------------- replay classification (scripted runs)
class Fake:
    def __init__(self, script, rep=None):
        self.cfg = load_config_default(rep); self.entry = "f"; self.n = 0; self.script = script
        self.h_id = "H"; self.env_id = "E"; self.policy_id = "P"; self.pair_id = "PAIR"; self.vers = {"base": "vb", "variant": "vv"}

        class L:
            def append(s, rec): return rec.id
        self.log = L()

    def run(self, side, inp, kind, idx, mode="call", ctl=None):
        from sbgv7.runner import RunOut
        ret = self.script(side, kind, idx)
        o = {"t": "returned", "ret": ["int", str(ret)], "stdout": "x", "files": {}, "argmut": ["list", []], "globals": {}, "args_changed": False}
        return RunOut(f"{side}{kind}{idx}", o, hits={1})


def load_config_default(rep):
    from sbgv7.config import _fill, SCHEMA
    return _fill(SCHEMA, {"repeat": rep or {"r_det": 2, "r_replay": 3, "k_alt": 2}}, "")


def test_replay_classes():
    base = lambda side, kind, idx: 1 if side == "base" else 2
    ev = process_input(Fake(base), {"id": "a", "args": [], "kwargs": {}})[0]
    assert ev.outcome == "CONFIRMED_DIFF"
    # primary differs but replays disagree with the primary -> intermittent / failed_reproduction
    inter = lambda side, kind, idx: (1 if side == "base" else 2) if (kind != "replay" or idx == 0) else 9
    ev = process_input(Fake(inter), {"id": "a", "args": [], "kwargs": {}})[0]
    assert (ev.outcome, ev.repro) == ("UNCONFIRMED_DIFF", "intermittent")
    fail = lambda side, kind, idx: (1 if side == "base" else 2) if kind != "replay" else 7
    ev = process_input(Fake(fail), {"id": "a", "args": [], "kwargs": {}})[0]
    assert (ev.outcome, ev.repro) == ("UNCONFIRMED_DIFF", "failed_reproduction")
    env = lambda side, kind, idx: (1 if side == "base" else 2) if kind != "alt" else 5
    ev = process_input(Fake(env), {"id": "a", "args": [], "kwargs": {}})[0]
    assert ev.outcome == "ENV_SENSITIVE_DIFF"
    nd = lambda side, kind, idx: idx
    assert process_input(Fake(nd), {"id": "a", "args": [], "kwargs": {}})[0].outcome == "QUARANTINED"
    d = decide(Evidence(inputs=[process_input(Fake(env), {"id": "a", "args": [], "kwargs": {}})[0]], changed_units=frozenset(),
                        hit_units=frozenset(), tampered=False))
    assert (d[0], d[2]) == ("INSUFFICIENT", "env_sensitive")


# ---------------------------------------------------------------- comparator
H = {"c_obs": ["ret", "exc", "side:stdout", "side:file", "side:argmut", "side:global"], "float_tol": {"rel": 0, "abs": 0},
     "ordered_mapping": False, "exc_message": "exact_normalised"}


def ob(ret, **kw):
    return {"t": "returned", "ret": ret, "stdout": "", "files": {}, "argmut": ["list", []], "globals": {}, **kw}


@pytest.mark.parametrize("a,b,eq", [
    (["int", "1"], ["float", "1.0"], False), (["list", []], ["tuple", []], False), (["float", "nan"], ["float", "nan"], True),
    (["float", "0.0"], ["float", "-0.0"], False), (["set", [["int", "1"], ["int", "2"]]], ["set", [["int", "1"], ["int", "2"]]], True),
    (["dict", [[["str", "a"], ["int", "1"]], [["str", "b"], ["int", "2"]]]], ["dict", [[["str", "b"], ["int", "2"]], [["str", "a"], ["int", "1"]]]], True),
])
def test_comparator_types(a, b, eq):
    assert compare(ob(a), ob(b), H).equal is eq


def test_comparator_options():
    d1 = ["dict", [[["str", "a"], ["int", "1"]], [["str", "b"], ["int", "2"]]]]
    d2 = ["dict", [[["str", "b"], ["int", "2"]], [["str", "a"], ["int", "1"]]]]
    assert not compare(ob(d1), ob(d2), {**H, "ordered_mapping": True}).equal
    assert compare(ob(["float", "1.0"]), ob(["float", "1.0000001"]), {**H, "float_tol": {"rel": 1e-3, "abs": 0}}).equal
    e = lambda m, t="builtins.ValueError": {"t": "raised", "type": t, "msg": m}
    assert not compare(e("a"), e("b"), H).equal and compare(e("a"), e("b"), {**H, "exc_message": "ignore"}).equal
    assert compare(e("a"), e("a", "builtins.KeyError"), H).kinds == ["exception"]  # no subclass coalescing
    assert compare(ob(["int", "1"], lossy=True), ob(["int", "1"]), H).lossy


# ---------------------------------------------------------------- strict config / CLI
@pytest.mark.parametrize("bad", [{"nope": 1}, {"repeat": {"r_det": 0}}, {"repeat": {"r_det": True}}, {"suff": {"s3_enabled": True}},
                                 {"harness": {"c_obs": []}}, {"harness": {"c_obs": ["stderr"]}}, {"budget": {"cpu_seconds": -1}},
                                 {"suff": {"s2_branch_floor": 2}}, {"harness": {"exc_message": "x"}}, [1]])
def test_bad_config(tmp_path, bad):
    (tmp_path / "c.json").write_text(json.dumps(bad))
    with pytest.raises(ConfigError):
        load_config(str(tmp_path / "c.json"))


@pytest.mark.parametrize("bad", ['{"a":1}', '[1]', '[{"args":1}]', '[{"args":[],"x":1}]', '[{"args":[],"id":"a"},{"args":[],"id":"a"}]', "not json"])
def test_bad_inputs(tmp_path, bad):
    (tmp_path / "i.json").write_text(bad)
    with pytest.raises(ConfigError):
        load_inputs(str(tmp_path / "i.json"))


def test_cli(tmp_path):
    (tmp_path / "a.py").write_text(BASE); (tmp_path / "b.py").write_text(EQV)
    (tmp_path / "i.json").write_text('[{"args":[5]},{"args":[0]}]'); (tmp_path / "c.json").write_text(json.dumps(FAST))
    run = lambda *a, out="o": subprocess.run([sys.executable, "-m", "sbgv7", "compare", str(tmp_path / "a.py"), str(tmp_path / "b.py"), "--entry", "f",
                                              "--inputs", str(tmp_path / "i.json"), "--config", str(tmp_path / "c.json"), "--out", str(tmp_path / out), *a],
                                             capture_output=True, text=True)
    r = run()
    assert r.returncode == 0 and json.loads(r.stdout)["level"] == "S2"
    r = run()  # refuses to overwrite evidence
    assert r.returncode == 2 and "refusing" in r.stderr
    (tmp_path / "c.json").write_text('{"suff":{"s3_enabled":true}}')
    r = run(out="o2")
    assert r.returncode == 2 and "S3" in r.stderr and "Traceback" not in r.stderr


# ---------------------------------------------------------------- reproducibility and chain
def test_repeated_runs_reproduce_ids_and_chain(tmp_path):
    var = BASE.replace("return x\n", "return x + 1\n")
    a = go(tmp_path, BASE, var, [[5]], name="r1"); b = go(tmp_path, BASE, var, [[5]], name="r2")
    assert (a["verdict"], a["witness_id"], a["pair_id"], a["verdict_id"]) == (b["verdict"], b["witness_id"], b["pair_id"], b["verdict_id"])
    p = tmp_path / "r1" / "evidence.jsonl"
    R.read_log(str(p))
    lines = p.read_text().splitlines()
    e = json.loads(lines[3]); e["rec"]["body"] = {"tampered": 1}; lines[3] = json.dumps(e)
    p.write_text("\n".join(lines) + "\n")
    with pytest.raises(R.ChainError):
        R.read_log(str(p))


def test_verdict_record_rejects_prohibited_values():
    for bad in ("EQUIVALENT", "SAME", "PASS", "VERIFIED", "SAFE"):
        with pytest.raises(AssertionError):
            R.Verdict(bad, None, None, [], [], "p")
    with pytest.raises(AssertionError):
        R.Verdict("NO_DIVERGENCE_OBSERVED", "S3", None, [], [], "p")
    with pytest.raises(AssertionError):
        R.Verdict("NO_DIVERGENCE_OBSERVED", "S0", None, [], [], "p")
    with pytest.raises(AssertionError):
        R.Verdict("INSUFFICIENT", None, "made_up_code", [], [], "p")


# ---------------------------------------------------------------- decision logic: missing evidence + property test
def good():
    return Evidence(inputs=[InputEv("a", "SAME", None, False, False, False, True, ("r",))], changed_units=frozenset({("base", 1)}),
                    hit_units=frozenset({("base", 1)}), branch_cov={"base": 1.0, "variant": 1.0}, tampered=False)


def test_decide_baseline_and_missing_evidence():
    assert decide(good())[:2] == ("NO_DIVERGENCE_OBSERVED", "S2")
    for field_ in ("inputs", "changed_units", "hit_units", "tampered"):
        e = good(); setattr(e, field_, None)
        d = decide(e)
        assert d[0] == "INSUFFICIENT" and d[2] == "tool_error", field_
    for attr in ("outcome", "truncated", "sandbox_ok"):
        e = good(); setattr(e.inputs[0], attr, None)
        assert decide(e)[0] == "INSUFFICIENT"
    e = good(); e.branch_cov = None
    assert decide(e)[:2] == ("NO_DIVERGENCE_OBSERVED", "S1")  # missing branch data can only cap the level, never raise it


def test_precedence_divergent_over_insufficient():
    e = good(); e.inputs += [InputEv("b", "CONFIRMED_DIFF", "wit_x", None, None, False, True), InputEv("c", "QUARANTINED", None, None, None, False, True)]
    e.blockers = [("import_error", "x")]
    assert decide(e)[0] == "DIVERGENT_OBSERVABLE"
    e.inputs[1].witness_id = None  # confirmed diff without a witness record is missing evidence, not a verdict
    assert decide(e)[0] == "INSUFFICIENT"


def test_property_incomplete_evidence_never_positive():
    rnd = random.Random(7)
    outs = ["SAME", "SAME", "QUARANTINED", "UNCONFIRMED_DIFF", "ENV_SENSITIVE_DIFF", "LIMIT_ASYMMETRIC", "NO_RUN", "CONFIRMED_DIFF", None, "bogus"]
    opt = lambda v, p=0.15: None if rnd.random() < p else v
    seen = set()
    for _ in range(3000):
        ins = [InputEv(f"i{k}", rnd.choice(outs), opt("w") if rnd.random() < .7 else None, opt(rnd.random() < .2), opt(rnd.random() < .2),
                       opt(rnd.random() < .1), opt(rnd.random() < .9)) for k in range(rnd.randint(0, 4))]
        units = frozenset(("base", n) for n in range(rnd.randint(0, 3)))
        ev = Evidence(inputs=opt(ins), blockers=[("import_error", "x")] if rnd.random() < .1 else [], changed_units=opt(units),
                      hit_units=opt(frozenset(u for u in units if rnd.random() < .8)), branch_cov=opt({"base": rnd.random(), "variant": rnd.random()}),
                      budget_exhausted=rnd.random() < .2, tampered=opt(rnd.random() < .05), s2_floor=0.8)
        value, level, primary, sec, wid, blockers, floors = decide(ev)
        seen.add(value)
        assert value in R.VERDICTS and "EQUIV" not in json.dumps([value, level, primary, sec])
        if value == "DIVERGENT_OBSERVABLE":
            assert any(i.outcome == "CONFIRMED_DIFF" and i.witness_id for i in ev.inputs)
        if value == "NO_DIVERGENCE_OBSERVED":
            # only complete, blocker-free evidence reaches here, and never above its sufficiency
            assert None not in (ev.inputs, ev.changed_units, ev.hit_units, ev.tampered) and not ev.blockers and not ev.tampered
            assert ev.changed_units <= ev.hit_units
            assert all(i.outcome in ("SAME", "NO_RUN") and i.sandbox_ok and not i.truncated for i in ev.inputs)
            assert any(i.outcome == "SAME" and i.degenerate is False for i in ev.inputs)
            assert level in ("S1", "S2") and (level != "S2" or (ev.branch_cov and min(ev.branch_cov.values()) >= 0.8
                                                                 and all(i.lossy is False for i in ev.inputs)))
            assert primary is None
        else:
            assert level is None
            if value == "INSUFFICIENT":
                assert primary in RANK and all(RANK[primary] <= RANK[c] for c in sec)
    assert seen == set(R.VERDICTS)


def test_no_run_input_blocks_no_divergence():
    """Regression (red-team B-1): [SAME, NO_RUN] must not yield NO_DIVERGENCE_OBSERVED."""
    e = good()
    e.inputs += [InputEv("n", "NO_RUN", None, None, None, False, True)]
    d = decide(e)
    assert d[0] == "INSUFFICIENT" and d[2] == "resource_limit"
