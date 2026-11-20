"""Phase 2 mandatory backlog (MB-01..MB-15) tests. Written failing-first; see docs/architecture/V7B_BACKLOG_STATUS.md."""
import json, subprocess, sys

import pytest

from sbgv7 import records as R
from sbgv7.verify import verify
from .test_core import BASE, EQV, FAST, capabilities, cfg, go

pytestmark = pytest.mark.skipif(capabilities()["network_denial"]["state"] != "ACTIVE", reason="isolation not enforced here")
LOG = lambda tp, n="out": str(tp / n / "evidence.jsonl")


def verified(tp, n="out"):
    assert verify(str(tp / n))["verified"]


# ---------------------------------------------------------------- MB-01
def test_mb01_huge_ints_differ(tmp_path):
    o = go(tmp_path, "def f(x):\n    return 10**5000\n", "def f(x):\n    return 10**5001\n", [[1]])
    assert o["verdict"] == "DIVERGENT_OBSERVABLE"
    verified(tmp_path)


def test_mb01_equal_huge_ints_clean(tmp_path):
    o = go(tmp_path, "def f(x):\n    return 10**5000\n", "def f(x):\n    return 10**5000 + 0\n", [[1]])
    assert o["verdict"] == "NO_DIVERGENCE_OBSERVED"
    s = [r for r in R.read_log(LOG(tmp_path)) if r["kind"] == "SufficiencyRecord"][0]["body"]
    assert s["inputs_same"] == 1
    verified(tmp_path)


CANON_BOMB = ("class F:\n    @property\n    def __module__(self):\n        raise RuntimeError('boom')\n    def __call__(self):\n        return 1\n"
              "from collections import defaultdict\ndef f(x):\n    return defaultdict(F())  # V\n")


def test_mb01_canon_failure_is_tool_error_not_outcome(tmp_path):
    o = go(tmp_path, CANON_BOMB, CANON_BOMB.replace("# V", "# W"), [[1]])
    assert o["verdict"] == "INSUFFICIENT" and "tool_error" in [o["primary"], *o["secondary"]]  # primary tightened in MB-10 (spurious resource_limit)
    verified(tmp_path)


# ---------------------------------------------------------------- MB-02 (UD-3 option A: fd-level output folded into side:stdout)
def _fdw(b):
    return f"import os\ndef f(x):\n    os.write(1, {b!r})\n    return 1\n"


def test_mb02_os_write_differs(tmp_path):
    o = go(tmp_path, _fdw(b"A"), _fdw(b"B"), [[1]])
    assert o["verdict"] == "DIVERGENT_OBSERVABLE"
    w = [r for r in R.read_log(LOG(tmp_path)) if r["kind"] == "Witness"][0]
    assert w["body"]["kinds"] == ["side_effect"]
    verified(tmp_path)


def test_mb02_identical_os_write_is_not_divergent(tmp_path):
    o = go(tmp_path, _fdw(b"A"), _fdw(b"A").replace("return 1", "return 1  # c"), [[1]])
    assert o["verdict"] != "DIVERGENT_OBSERVABLE"
    verified(tmp_path)


def test_mb02_subprocess_output_differs(tmp_path):
    sp = lambda t: f"import subprocess\ndef f(x):\n    subprocess.run(['/bin/echo', {t!r}])\n    return 1\n"
    o = go(tmp_path, sp("x"), sp("y"), [[1]])
    assert o["verdict"] == "DIVERGENT_OBSERVABLE"
    verified(tmp_path)


def test_mb02_no_fd1_output_leaves_observation_unchanged(tmp_path):
    go(tmp_path, BASE, EQV, [[5]])
    obs = [r for r in R.read_log(LOG(tmp_path)) if r["kind"] == "Observation"]
    assert obs and all("fd1" not in r["body"] for r in obs)


# ---------------------------------------------------------------- MB-03
def test_mb03_source_path_in_message_and_output_is_normalised(tmp_path):
    src = "import os\ndef f(x):\n    print(__file__)\n    os.write(1, __file__.encode())\n    raise ValueError(__file__)\n"
    (tmp_path / "sub").mkdir()
    (tmp_path / "base.py").write_text(src); (tmp_path / "sub" / "var.py").write_text(src + "# c\n")
    (tmp_path / "i.json").write_text('[{"args":[1]}]')
    from sbgv7.config import load_inputs
    from sbgv7.runner import compare_versions
    from .test_core import _load
    o = compare_versions(str(tmp_path / "base.py"), str(tmp_path / "sub" / "var.py"), "f", load_inputs(str(tmp_path / "i.json")), _load(tmp_path, FAST), str(tmp_path / "out"))
    assert o["verdict"] != "DIVERGENT_OBSERVABLE" and o["r_empty"] is True
    verified(tmp_path)


def test_mb03_real_message_change_still_differs(tmp_path):
    src = "def f(x):\n    raise ValueError(__file__ + 'a')\n"
    assert go(tmp_path, src, src.replace("'a'", "'b'"), [[1]])["verdict"] == "DIVERGENT_OBSERVABLE"


# ---------------------------------------------------------------- MB-04
def _py(code, *flags):
    return subprocess.run([sys.executable, *flags, "-c", code], capture_output=True, text=True, cwd=str(__import__("pathlib").Path(__file__).parents[2]))


@pytest.mark.parametrize("flags", [(), ("-O",)])
@pytest.mark.parametrize("call", ['R.Verdict("EQUIVALENT", None, None, [], [], "p")', 'R.Verdict("INSUFFICIENT", None, "bogus_code", [], [], "p")',
                                  'R.Verdict("NO_DIVERGENCE_OBSERVED", "S3", None, [], [], "p")', 'R.Verdict("INSUFFICIENT", None, "tool_error", ["bogus"], [], "p")',
                                  'R.Rec("X", evidence_class="bogus")'])
def test_mb04_invariants_hold_under_python_O(call, flags):
    r = _py(f"from sbgv7 import records as R\ntry:\n    {call}\nexcept ValueError:\n    print('RAISED')\n", *flags)
    assert r.stdout.strip() == "RAISED", r.stderr


def test_mb04_unknown_blocker_code_is_insufficient_tool_error():
    from sbgv7.decide import Evidence, InputEv, decide
    e = Evidence(inputs=[InputEv("a", "SAME", None, False, False, False, True)], blockers=[("not_a_code", "x")], changed_units=frozenset(),
                 hit_units=frozenset(), branch_cov={"base": 1.0, "variant": 1.0}, tampered=False)
    d = decide(e)
    assert (d[0], d[2]) == ("INSUFFICIENT", "tool_error")


def test_mb04_verify_names_unknown_code(tmp_path):
    from sbgv7.verify import VerifyError
    go(tmp_path, "def f(x):\n    pass\n", "def f(x):\n    y = 1\n", [[1]])  # INSUFFICIENT(unobservable_outcome)
    p = tmp_path / "out" / "evidence.jsonl"
    recs = R.read_log(str(p))
    for r in recs:
        if r["kind"] == "Verdict": r["body"]["primary"] = "bogus_code"
    prev, lines = "0" * 64, []
    for i, r in enumerate(recs):  # re-chain so only the code (not the chain) is wrong
        h = R.sha(prev + R.canon_json(r)); lines.append(R.canon_json({"seq": i, "prev": prev, "rec": r, "hash": h})); prev = h
    p.write_text("\n".join(lines) + "\n")
    with pytest.raises(VerifyError, match="bogus_code"):
        verify(str(tmp_path / "out"))


# ---------------------------------------------------------------- MB-01 extended (user review req. 1): precision, containers, types
_W = "class O:\n    def __init__(self, v): self.v = v\n"


@pytest.mark.parametrize("a,b", [
    ("2**53", "2**53 + 1"), ("2**64", "2**64 + 1"), ("10**17", "10**17 + 1"), ("10**4299", "10**4299 + 1"), ("10**4300", "10**4300 + 1"),
    ("-10**5000", "-10**5001"), ("-(2**64)", "-(2**64) - 1"),
    ("[1, 10**5000]", "[1, 10**5000 + 1]"), ("{'k': 2**64}", "{'k': 2**64 + 1}"), ("(1, {2**70})", "(1, {2**70 + 1})"), ("O(10**5000)", "O(10**5000 + 1)"),
    ("1", "1.0"), ("True", "1"), ("2**53", "float(2**53)"),
], ids=lambda s: s[:18])
def test_mb01_int_precision_and_type_differences_diverge(tmp_path, a, b):
    o = go(tmp_path, f"{_W}def f(x):\n    return {a}\n", f"{_W}def f(x):\n    return {b}\n", [[1]])
    assert o["verdict"] == "DIVERGENT_OBSERVABLE", (a, b)
    verified(tmp_path)


@pytest.mark.parametrize("a", ["2**64", "-10**5000", "[10**5000, 2**53 + 1]", "{'k': 10**4301}", "O(10**5000)"])
def test_mb01_equal_ints_stay_same_and_non_lossy(tmp_path, a):
    o = go(tmp_path, f"{_W}def f(x):\n    return {a}\n", f"{_W}def f(x):\n    return {a}  # c\n", [[1]])
    assert o["verdict"] != "DIVERGENT_OBSERVABLE"
    rows = [r for r in R.read_log(LOG(tmp_path)) if r["kind"] == "EvidencePackage"][0]["body"]["rows"]
    assert rows[0]["outcome"] == "SAME" and rows[0]["lossy"] is False
    verified(tmp_path)


def test_mb01_default_digit_limit_is_the_trigger():
    assert sys.get_int_max_str_digits() == 4300  # the limit that made str(10**5000) raise inside the program try


# ---------------------------------------------------------------- MB-05 (SD-10, A-14, NF-04): a witness needs verified, untampered replay and alt runs
def _scripted(kind_bad, **flags):
    from sbgv7.runner import RunOut
    from .test_core import Fake

    class F(Fake):
        def run(self, side, inp, kind, idx, mode="call", ctl=None):
            r = super().run(side, inp, kind, idx, mode, ctl)
            if kind == kind_bad and (idx == 0 or flags.get("all")):
                for k, v in flags.items():
                    if k != "all": setattr(r, k, v)
            return r
    return F(lambda side, kind, idx: 1 if side == "base" else 2)


def _verdict_of(fake):
    from sbgv7.decide import Evidence, decide
    ev, hits, br, _, stat = process_input(fake, {"id": "a", "args": [], "kwargs": {}})
    return ev, decide(Evidence(inputs=[ev], blockers=stat, changed_units=frozenset(), hit_units=frozenset(), tampered=False))


from sbgv7.runner import process_input  # noqa: E402


def test_mb05_all_replays_tampered_gives_no_witness():
    ev, d = _verdict_of(_scripted("replay", tampered=True, all=True))
    assert ev.outcome == "NO_RUN" and ev.witness_id is None and (d[0], d[2]) == ("INSUFFICIENT", "unsafe_program")


def test_mb05_alt_run_not_sandbox_ok_gives_sandbox_failure():
    ev, d = _verdict_of(_scripted("alt", sandbox_ok=False))
    assert ev.outcome == "NO_RUN" and (d[0], d[2]) == ("INSUFFICIENT", "sandbox_failure")


def test_mb05_replay_harness_error_is_tool_error():
    ev, d = _verdict_of(_scripted("replay", phase="harness_error"))
    assert ev.outcome == "NO_RUN" and "tool_error" in [d[2], *d[3]]


def test_mb05_clean_replays_still_confirm():
    ev, d = _verdict_of(_scripted("none"))
    assert ev.outcome == "CONFIRMED_DIFF"


# ---------------------------------------------------------------- MB-06 (SD-07, A-01): required vs advisory isolation properties
def _with_caps(monkeypatch, **states):
    import copy
    from sbgv7 import isolation
    real = copy.deepcopy(isolation.capabilities())
    for k, v in states.items(): real[k]["state"] = v
    monkeypatch.setattr(isolation, "capabilities", lambda refresh=False: real)


@pytest.mark.parametrize("cap", ["rlimit_cpu", "rlimit_fsize", "rlimit_nofile", "process_group_kill", "write_confinement"])
def test_mb06_required_property_unverified_is_sandbox_failure(tmp_path, monkeypatch, cap):
    _with_caps(monkeypatch, **{cap: "UNAVAILABLE"})
    o = go(tmp_path, BASE, EQV, [[5]])
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "sandbox_failure")
    verified(tmp_path)


def test_mb06_advisory_unavailable_keeps_verdicts_and_flags_policy(tmp_path, monkeypatch):
    a = go(tmp_path, BASE, EQV, [[5], [0]], name="a")  # this host: rlimit_as/rlimit_nproc already UNAVAILABLE
    _with_caps(monkeypatch, rlimit_as="UNAVAILABLE")
    b = go(tmp_path, BASE, EQV, [[5], [0]], name="b")
    assert (a["verdict"], a["level"]) == (b["verdict"], b["level"]) == ("NO_DIVERGENCE_OBSERVED", "S2")
    assert b["policy_below_minimum"] is True
    verified(tmp_path, "b")


def test_mb06_policy_id_differs_between_capability_sets(tmp_path, monkeypatch):
    a = go(tmp_path, BASE, EQV, [[5]], name="a")
    _with_caps(monkeypatch, rlimit_cpu="UNAVAILABLE")
    b = go(tmp_path, BASE, EQV, [[5]], name="b")
    pol = lambda n: [r for r in R.read_log(LOG(tmp_path, n)) if r["kind"] == "EvidencePackage"][0]["body"]["policy"]
    assert pol("a") != pol("b")


# ---------------------------------------------------------------- MB-07 (SD-09, I1, X6): determinism control profile
def test_mb07_hash_seed_pinned_set_order_is_deterministic(tmp_path):
    src = "def f(x):\n    return list({'a', 'b', 'c', 'd', 'e'})\n"
    o = go(tmp_path, src, src + "# c\n", [[1]], config=cfg(repeat={"r_det": 3, "r_replay": 2, "k_alt": 1}))
    assert o["primary"] != "nondeterministic" and "nondeterministic" not in o["secondary"]


def test_mb07_pure_random_difference_is_not_a_witness(tmp_path):
    a = "import os\ndef f(x):\n    return os.urandom(4).hex()\n"
    o = go(tmp_path, a, a.replace("hex()", "hex()  # c"), [[1]], config=cfg(repeat={"r_det": 3}))
    assert o["verdict"] != "DIVERGENT_OBSERVABLE"


def test_mb07_real_env_sensitive_case(tmp_path):
    """alt runs shift time.time() by 1000 s * ctl but not the filesystem clock: |mtime(just-created file) - time.time()| is ~0 in primary
    and replay runs and ~1000+ s in alt runs, at ANY wall-clock moment (the former `time.time() // 1000` version was flaky at epoch boundaries)."""
    base = "def f(x):\n    return 0\n"
    var = "import os, time\ndef f(x):\n    open('t', 'w').close()\n    return 1 + (abs(os.path.getmtime('t') - time.time()) > 500)\n"
    o = go(tmp_path, base, var, [[1]])
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "env_sensitive")
    verified(tmp_path)


def _alt_runs(tmp_path, prog, ctls):
    from sbgv7.runner import Ctx
    from .test_core import load_config_default

    class L:
        def append(self, rec): return rec.id
    p = tmp_path / "p.py"; p.write_text(prog)
    c = Ctx(load_config_default(None), L(), "f", str(p), str(p))
    return [c.run("base", {"args": [1], "kwargs": {}}, "alt", 0, ctl=k).obs["ret"] for k in ctls]


def test_mb07_alt_virtualises_urandom_uuid_and_monotonic(tmp_path):
    prog = "import os, time, uuid\ndef f(x):\n    return [os.urandom(4).hex(), str(uuid.uuid4()), round(time.monotonic() / 100), round(time.perf_counter() / 100)]\n"
    r1a, r1b, r2, r0 = _alt_runs(tmp_path, prog, [1, 1, 2, None])
    assert r1a == r1b and r1a != r2  # seeded: same ctl reproduces, different ctl differs
    num = lambda r, i: int(r[1][i][1], 0)
    assert abs(num(r1a, 2) - num(r0, 2)) >= 9 and abs(num(r1a, 3) - num(r0, 3)) >= 9  # +1000 s shift


def test_mb07_profile_is_part_of_policy_id(tmp_path, monkeypatch):
    from sbgv7 import isolation
    a = go(tmp_path, BASE, EQV, [[5]], name="a")
    monkeypatch.setattr(isolation, "DET_ENV", {**isolation.DET_ENV, "TZ": "Asia/Tokyo"})
    b = go(tmp_path, BASE, EQV, [[5]], name="b")
    pid = lambda n: [r for r in R.read_log(LOG(tmp_path, n)) if r["kind"] == "EvidencePackage"][0]["body"]
    assert pid("a")["policy"] != pid("b")["policy"] and pid("a")["h_id"] == pid("b")["h_id"]


def test_mb07_python_minor_version_flags_policy(monkeypatch):
    from sbgv7 import runner
    monkeypatch.setattr(sys, "platform", "linux")
    ok = {k: "ACTIVE" for k in ("rlimit_as", "rlimit_nproc")}
    monkeypatch.setattr(sys, "version_info", (3, 13, 1))
    assert runner.below_minimum(ok) is False
    monkeypatch.setattr(sys, "version_info", (3, 12, 1))
    assert runner.below_minimum(ok) is True


# ---------------------------------------------------------------- MB-08 (V3, D-12): identity check before any side effect; one overwrite policy
def _cli(tp, base, var, out="o"):
    (tp / "a.py").write_text(base); (tp / "b.py").write_text(var)
    (tp / "i.json").write_text('[{"args":[5]}]'); (tp / "c.json").write_text(json.dumps(FAST))
    return subprocess.run([sys.executable, "-m", "sbgv7", "compare", str(tp / "a.py"), str(tp / "b.py"), "--entry", "f", "--inputs", str(tp / "i.json"),
                           "--config", str(tp / "c.json"), "--out", str(tp / out)], capture_output=True, text=True, cwd=str(__import__("pathlib").Path(__file__).parents[2]))


def test_mb08_identical_pair_leaves_nothing_and_is_stable(tmp_path):
    assert _cli(tmp_path, BASE, BASE).returncode == 3
    assert not (tmp_path / "o").exists()
    assert _cli(tmp_path, BASE, BASE).returncode == 3  # second identical invocation: still 3, not 2


def test_mb08_second_compare_into_same_dir_raises_instead_of_truncating(tmp_path):
    go(tmp_path, BASE, EQV, [[5]])
    before = (tmp_path / "out" / "evidence.jsonl").read_text()
    with pytest.raises(FileExistsError):
        go(tmp_path, BASE, EQV, [[5]])
    assert (tmp_path / "out" / "evidence.jsonl").read_text() == before


# ---------------------------------------------------------------- MB-09 (F18, D-10, SD-20): pair identity covers repeat, suff, policy; not budget
def test_mb09_pair_id_covers_repeat_and_suff_not_budget(tmp_path):
    ids = {}
    for name, over in {"base": {}, "rdet": {"repeat": {"r_det": 3, "r_replay": 2, "k_alt": 1}}, "suff": {"suff": {"s2_branch_floor": 0.5}},
                       "budget": {"budget": {"cpu_seconds": 30, "per_run": {"wall_s": 3, "cpu_s": 3}}}}.items():
        c = cfg(); c.update(over)
        ids[name] = go(tmp_path, BASE, EQV, [[5]], config=c, name=name)["pair_id"]
        verified(tmp_path, name)
    assert ids["base"] == ids["budget"]
    assert len({ids["base"], ids["rdet"], ids["suff"]}) == 3


def test_mb09_pair_id_covers_policy(tmp_path, monkeypatch):
    a = go(tmp_path, BASE, EQV, [[5]], name="a")
    _with_caps(monkeypatch, rlimit_as="ACTIVE")
    b = go(tmp_path, BASE, EQV, [[5]], name="b")
    assert a["pair_id"] != b["pair_id"]
    verified(tmp_path, "b")


# ---------------------------------------------------------------- MB-10 (B6, D-04, OI-09; UD-4 option A unchanged): NO_RUN names its real cause
def test_mb10_protocol_violation_is_unsafe_program_without_spurious_resource_limit(tmp_path):
    ex = lambda n: f"import os\ndef f(x):\n    os._exit({n})\n"
    o = go(tmp_path, ex(0), ex(1), [[1]])
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "unsafe_program") and "resource_limit" not in o["secondary"]
    verified(tmp_path)


def test_mb10_canon_failure_primary_is_tool_error(tmp_path):
    o = go(tmp_path, CANON_BOMB, CANON_BOMB.replace("# V", "# W"), [[1]])
    assert (o["primary"], o["secondary"]) == ("tool_error", [])


def test_mb10_both_limit_still_resource_limit(tmp_path):  # UD-4 option A (conservative) unchanged
    c = cfg(budget={"per_run": {"wall_s": 1, "cpu_s": 1}})
    hang = "def f(x):\n    while True:\n        pass\n"
    o = go(tmp_path, hang, hang.replace("pass", "x = 1"), [[1]], config=c)
    assert o["primary"] == "resource_limit"
    row = [r for r in R.read_log(LOG(tmp_path)) if r["kind"] == "EvidencePackage"][0]["body"]["rows"][0]
    assert row["reason"] == "both_limit"
    verified(tmp_path)


# ---------------------------------------------------------------- MB-11 (P7, B9, D-13, A-17, SD-19): budget charges parent CPU, checked between runs
def _child_cpu(tp, n="out"):
    return sum(r["meta"]["cpu_s"] for r in R.read_log(LOG(tp, n)) if r["kind"] == "Run")


def test_mb11_spent_includes_parent_cpu(tmp_path):
    o = go(tmp_path, BASE, EQV, [[5]])
    assert o["cpu_seconds_spent"] > _child_cpu(tmp_path) + 0.01


def test_mb11_budget_stops_between_runs_inside_an_input(tmp_path):
    full = go(tmp_path, BASE, EQV, [[5]], name="full")["cpu_seconds_spent"]
    c = cfg(); c["budget"]["cpu_seconds"] = full * 0.7  # after the two probe runs, before the input's four runs finish
    o = go(tmp_path, BASE, EQV, [[5]], config=c, name="cut")
    assert o["verdict"] == "INSUFFICIENT" and "budget_exhausted_s0" in [o["primary"], *o["secondary"]]
    pkg = [r for r in R.read_log(LOG(tmp_path, "cut")) if r["kind"] == "EvidencePackage"][0]["body"]
    assert pkg["stop"] == "budget_mid_input" and pkg["rows"] == []
    runs = [r for r in R.read_log(LOG(tmp_path, "cut")) if r["kind"] == "Run" and r["body"]["run_kind"] != "probe"]
    assert 0 < len(runs) < 4  # stopped at run granularity, the remaining runs of that input were not started
    verified(tmp_path, "cut")


def test_mb11_last_input_exhausting_budget_with_unhit_units_is_budget_exhausted(tmp_path, monkeypatch):
    from sbgv7 import runner
    monkeypatch.setattr(runner.Ctx, "over_budget", lambda self: False)  # no stop before/within the input; exhausted only when it finishes
    src = "def f(x):\n    if x > 100:\n        return 7\n    return 1\n"
    c = cfg(); c["budget"]["cpu_seconds"] = 0.001
    o = go(tmp_path, src, src.replace("return 7", "return 8"), [[1]], config=c)
    assert o["primary"] == "budget_exhausted_s0" and "changed_region_not_activated" not in o["secondary"]
    verified(tmp_path)


# ---------------------------------------------------------------- MB-12 (S1a, OI-04): Merkle run-set root and factor vector
def test_mb12_merkle_root_properties():
    ids = ["run_a", "run_b", "run_c", "run_d", "run_e"]
    root = R.merkle_root(ids)
    assert root == R.merkle_root(list(reversed(ids))) == R.merkle_root(ids + ids[:2])  # order-independent, set semantics
    assert root != R.merkle_root(ids[:-1]) and root != R.merkle_root(ids + ["run_f"])
    assert all(R.merkle_root([i]) != R.merkle_root([j]) for i in ids for j in ids if i != j)


def test_mb12_sufficiency_record_has_root_and_factors(tmp_path):
    go(tmp_path, BASE, EQV, [[5], [0]])
    s = [r for r in R.read_log(LOG(tmp_path)) if r["kind"] == "SufficiencyRecord"][0]["body"]
    assert {"run_set_root", "level", "units_hit", "inputs_same"} <= set(s)  # existing keys kept
    f = s["factors"]
    assert f["F1"] == {"quarantined": 0, "r_det": 2} and f["F3"] == {"units_hit": s["units_hit"], "units_total": s["units_total"]}
    assert set(f["F2"]) == {"truncated", "tampered", "lossy"} and f["F4"] == {"inputs_same": 2, "stop_reason": "inputs_exhausted"}
    verified(tmp_path)


# ---------------------------------------------------------------- MB-13 (F2, F6, F7, SD-18): constant-valued config fields
CONST = {"normaliser_id": "N1", "stderr": "excluded", "capture_tier": "L0"}


def test_mb13_constants_accepted_and_equal_to_defaults(tmp_path):
    from sbgv7.config import load_config
    (tmp_path / "a.json").write_text(json.dumps({"harness": CONST})); (tmp_path / "b.json").write_text("{}")
    a, b = load_config(str(tmp_path / "a.json")), load_config(str(tmp_path / "b.json"))
    assert a == b and a["harness"]["normaliser_id"] == "N1"
    c = cfg(harness=CONST)
    x = go(tmp_path, BASE, EQV, [[5]], config=c, name="x"); y = go(tmp_path, BASE, EQV, [[5]], name="y")
    assert (x["verdict"], x["level"], x["pair_id"]) == (y["verdict"], y["level"], y["pair_id"])


@pytest.mark.parametrize("k,v", [("normaliser_id", "N2"), ("stderr", "included"), ("capture_tier", "L1"), ("stderr", True)])
def test_mb13_other_values_rejected_not_built(tmp_path, k, v):
    from sbgv7.config import ConfigError, load_config
    (tmp_path / "c.json").write_text(json.dumps({"harness": {k: v}}))
    with pytest.raises(ConfigError, match="not built"):
        load_config(str(tmp_path / "c.json"))


# ---------------------------------------------------------------- MB-14 (X2, A-11, SD-13): CLI failure handling
def test_mb14_out_is_a_file_exits_2_no_traceback(tmp_path):
    (tmp_path / "o").write_text("x")
    r = _cli(tmp_path, BASE, EQV)
    assert r.returncode == 2 and "Traceback" not in r.stderr and r.stderr.strip().count("\n") == 0


def test_mb14_unwritable_out_exits_2(tmp_path):
    import os
    ro = tmp_path / "ro"; ro.mkdir(); os.chmod(ro, 0o500)
    try:
        r = _cli(tmp_path, BASE, EQV, out="ro/o")
    finally:
        os.chmod(ro, 0o700)
    assert r.returncode == 2 and "Traceback" not in r.stderr


def test_mb14_unexpected_exception_exits_1_one_line(tmp_path, monkeypatch, capsys):
    from sbgv7 import __main__ as M
    monkeypatch.setattr(M, "compare_versions", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    (tmp_path / "a.py").write_text(BASE); (tmp_path / "b.py").write_text(EQV)
    (tmp_path / "i.json").write_text('[{"args":[5]}]'); (tmp_path / "c.json").write_text("{}")
    rc = M.main(["compare", str(tmp_path / "a.py"), str(tmp_path / "b.py"), "--entry", "f", "--inputs", str(tmp_path / "i.json"),
                 "--config", str(tmp_path / "c.json"), "--out", str(tmp_path / "o")])
    err = capsys.readouterr().err
    assert rc == 1 and "boom" in err and "Traceback" not in err and err.strip().count("\n") == 0


def test_mb14_help_exits_0():
    assert _py("import sys; sys.argv=['sbgv7','--help']; from sbgv7.__main__ import main; main()").returncode == 0


# ---------------------------------------------------------------- MB-15 (D-23): digest of the V6 changed_lines module
def test_mb15_package_records_digest_and_verify_checks_it(tmp_path, monkeypatch):
    import hashlib
    from sbgv6 import features
    from sbgv7 import verify as V
    go(tmp_path, BASE, EQV, [[5]])
    pkg = [r for r in R.read_log(LOG(tmp_path)) if r["kind"] == "EvidencePackage"][0]["body"]
    assert pkg["v6_features_sha256"] == hashlib.sha256(open(features.__file__, "rb").read()).hexdigest()
    verified(tmp_path)
    monkeypatch.setattr(V, "v6_digest", lambda: "0" * 64)
    with pytest.raises(V.VerifyError, match="changed_lines"):
        verify(str(tmp_path / "out"))
