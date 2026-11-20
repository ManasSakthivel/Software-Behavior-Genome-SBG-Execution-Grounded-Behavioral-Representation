"""Attack A (parent-owned independent stdout/stderr capture): every scenario goes through the real engine + sandboxed child."""
import json, os, types, pytest
import sbgv7.isolation as ISO
from sbgv7.config import SCHEMA, _fill
from sbgv8 import collect, procsep, evidence_schema as ES
from .test_collect import CFG

BASE = "def f(x):\n    return x + 1\n"
KEY = bytes(range(32))


def go(tmp_path, var, base=BASE, cfg=CFG, key=KEY, name="ev"):
    d = tmp_path / name; os.makedirs(tmp_path / "s", exist_ok=True)
    (tmp_path / "s/b.py").write_text(base); (tmp_path / "s/v.py").write_text(var)
    out = collect.run_capture(str(tmp_path / "s/b.py"), str(tmp_path / "s/v.py"), "f", [{"id": "i0", "args": [1], "kwargs": {}}], _fill(SCHEMA, cfg, ""), str(d), anchor_key=key)
    return out, d, json.load(open(d / "v8_capture.json"))


def calls(cap, side="variant"): return [r for r in cap["runs"] if r["mode"] == "call" and r["side"] == side]


@pytest.mark.parametrize("name,body,expect_trusted", [
    ("normal", "    print('hi', x)\n    return x + 1\n", True),
    ("empty", "    return x + 1\n", True),
    ("partial_no_newline", "    print('abc', end='')\n    return x + 1\n", True),
    ("unicode_and_emoji", "    print('h\\u00e9llo \\U0001f600')\n    return x + 1\n", True),
    ("large_over_harness_cap", "    print('y' * 100000)\n    return x + 1\n", True),
    ("huge_over_tee_cap", "    print('z' * 300000)\n    return x + 1\n", True),
    ("binary_non_utf8_fd1", "    import os\n    os.write(1, b'\\xff\\xfe\\x00bin')\n    return x + 1\n", True),
    ("own_stderr_text", "    import sys\n    sys.stderr.write('warn line\\n')\n    return x + 1\n", True),
])
def test_honest_output_shapes_are_trusted(tmp_path, name, body, expect_trusted):
    out, d, cap = go(tmp_path, "def f(x):\n" + body + "# v\n", base="def f(x):\n" + body)
    assert cap["trusted"] is expect_trusted and cap["reasons"] == [] and "v8_untrusted" not in out
    assert all(r["verdict"] == "match" for r in cap["runs"] if r["harness"]["frame"])
    if name == "huge_over_tee_cap": assert calls(cap)[0]["tee"]["overflow"] and calls(cap)[0]["harness"]["stdout_trunc"]
    if name == "binary_non_utf8_fd1": assert calls(cap)[0]["fd1"]["len"] > 0  # parent saw the real fd 1 (decoded form, see procsep docstring)
    if name == "own_stderr_text": assert calls(cap)[0]["fd2"]["len"] == len("warn line\n")  # tee records are stripped, genuine stderr kept


def test_different_output_is_a_trusted_divergence(tmp_path):
    out, d, cap = go(tmp_path, "def f(x):\n    print('b')\n    return x + 1\n", base="def f(x):\n    print('a')\n    return x + 1\n")
    assert cap["trusted"] and out["verdict"] == "DIVERGENT_OBSERVABLE"


def test_A08_regression_cap_patch_is_untrusted_and_verdict_not_clean(tmp_path):
    import sbgv8.trust as T
    out, d, cap = go(tmp_path, T.ATTACKS["A08_hide_stdout_divergence_by_patching_Cap"])
    assert cap["trusted"] is False and any(r["verdict"] == "mismatch" for r in calls(cap))
    assert out["verdict"] == "INSUFFICIENT" and out["v7b_verdict"] == "NO_DIVERGENCE_OBSERVED" and out["v8_untrusted"]  # the engine alone said clean
    from sbgv8.adapter import load_record
    rec = load_record(str(d), anchor_key=KEY)
    assert rec.integrity_ok is False and rec.meta["untrusted"] and rec.meta["effective_verdict"] == "INSUFFICIENT" and rec.meta["capture"] == "untrusted"


def test_collector_manipulation_attempts(tmp_path):
    hdr = "import sys, os\nm = sys.modules['__main__']\n"
    cases = {  # all try to hide the print from the parent; each leaves the record incomplete/mismatched, never a clean trusted run
        "patch_os_write": hdr + "def f(x):\n    os.write = lambda fd, b: len(b)\n    m.Cap.write = lambda self, s: len(s)\n    print('extra')\n    return x + 1\n",
        "dup2_stderr_to_devnull": hdr + "def f(x):\n    fd = os.open(os.devnull, os.O_WRONLY); os.dup2(fd, 2)\n    m.Cap.write = lambda self, s: len(s)\n    print('extra')\n    return x + 1\n",
        "close_stderr": hdr + "def f(x):\n    os.close(2)\n    m.Cap.write = lambda self, s: len(s)\n    print('extra')\n    return x + 1\n",
        "forged_foreign_record": "import os\ndef f(x):\n    os.write(2, b'@@SBGV8T@@' + b'a' * 32 + b' 1 W 41@@\\n')\n    return x + 1\n",
        "forged_own_marker_partial": "import os\ndef f(x):\n    os.write(2, b'@@SBGV8T@@ junk')\n    return x + 1\n",
    }
    for n, src in cases.items():
        out, d, cap = go(tmp_path, src, name=n)
        assert out["verdict"] == "INSUFFICIENT" and (cap["trusted"] is False or n == "patch_os_write"), n  # patch_os_write also kills the result frame: blocked by the engine instead


def test_known_limit_program_that_swallows_its_own_sys_stdout_is_not_visible(tmp_path):
    """HONEST BOUNDARY: replacing sys.stdout inside the evaluated process hides the output from harness AND tee; nothing reaches fd 1 either, so there is no
    independent record to disagree. Documented in procsep.py / V8_MAC_ATTACK_RETEST.md; this test pins it so nobody claims otherwise."""
    out, d, cap = go(tmp_path, "import sys, io\ndef f(x):\n    sys.stdout = io.StringIO()\n    print('hidden')\n    return x + 1\n")
    assert cap["trusted"] is True


def test_process_termination_is_recorded_explicitly(tmp_path):
    out, d, cap = go(tmp_path, "import os, signal\ndef f(x):\n    os.kill(os.getpid(), signal.SIGKILL)\n")
    r = calls(cap)[0]
    assert r["signal"] == 9 and r["verdict"] == "no_frame" and any("terminated" in w for w in r["reasons"]) and out["verdict"] != "NO_DIVERGENCE_OBSERVED"


def test_timeout_is_recorded_not_silent(tmp_path):
    cfg = {"repeat": {"r_det": 2, "r_replay": 2, "k_alt": 1}, "budget": {"cpu_seconds": 30, "per_run": {"cpu_s": 2, "wall_s": 1}}}
    out, d, cap = go(tmp_path, "import time\ndef f(x):\n    time.sleep(30)\n", cfg=cfg)
    r = calls(cap)[0]
    assert r["status"] == "TIMEOUT" and r["verdict"] == "no_frame" and any("TIMEOUT" in w for w in r["reasons"]) and out["verdict"] != "NO_DIVERGENCE_OBSERVED"


def test_output_flooding_is_recorded_and_fails_safe(tmp_path):
    out, d, cap = go(tmp_path, "import os\ndef f(x):\n    for _ in range(100): os.write(1, b'x' * 65536)\n    return x + 1\n")
    r = calls(cap)[0]
    assert r["flooded"] and r["status"] in ("RESOURCE", "OK")  # killed at the cap, or finished first with truncated=True (race)
    assert any("flooding" in w for w in r["reasons"]) and out["verdict"] != "NO_DIVERGENCE_OBSERVED"


def test_stderr_flood_over_cap_fails_safe(tmp_path):
    out, d, cap = go(tmp_path, "import sys\ndef f(x):\n    sys.stderr.write('e\\n' * (3 << 20))\n    return x + 1\n")
    assert calls(cap)[0]["flooded"] and out["verdict"] != "NO_DIVERGENCE_OBSERVED"


def test_key_and_nonce_not_in_child_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("SBGV8_ANCHOR_KEY", KEY.hex())
    out, d, cap = go(tmp_path, "import os\ndef f(x):\n    print(sorted(os.environ))\n    return x + 1\n", key=None)
    ev = (d / "evidence.jsonl").read_text()
    assert KEY.hex() not in ev and "SBGV8" not in ev and (d / "v8_anchor.json").exists()  # key came from the env, anchored, and never reached the child


# ---- unit level: forged output metadata, parser, supervisor plumbing
def fake(stdout="", stderr="", **kw):
    return types.SimpleNamespace(stderr=stderr, stderr_truncated=kw.get("stderr_truncated", False), workdir="/nonexistent-wd", protocol_error="", status="OK", **{k: v for k, v in kw.items() if k != "stderr_truncated"})


def rec(nonce, seq, kind, payload=b""): return f"@@SBGV8T@@{nonce} {seq} {kind} {payload.hex()}@@\n"


N = "ab" * 16


def tee_of(text, close=True, total=None):
    s = rec(N, 0, "O") + "".join(rec(N, i + 1, "W", c.encode()) for i, c in enumerate(text))
    if close: s += rec(N, len(text) + 1, "C", str(len("".join(text)) if total is None else total).encode())
    return procsep.parse_tee(s, N)


def test_parser_and_judge_unit():
    clean, tee, text = tee_of(["ab", "c"])
    assert text == "abc" and tee["open"] and tee["close"] and tee["gaps"] == 0 and clean == ""
    v = lambda claim, tee_=tee, t=text: procsep.judge(fake(), N, "/p.py", t, tee_, {"stdout": claim, "stdout_trunc": False})[0]
    assert v("abc") == "match" and v("ab") == "mismatch" and v("abcd") == "mismatch" and v("") == "mismatch"
    assert procsep.judge(fake(), N, "/p.py", text, tee, {"stdout": "abc", "stdout_trunc": True})[0] == "mismatch"  # forged truncation flag
    for bad in ({"stdout": 5, "stdout_trunc": False}, {"stdout": "abc"}, {"stdout": "abc", "stdout_trunc": 1}):  # forged metadata types
        assert procsep.judge(fake(), N, "/p.py", text, tee, bad)[0] == "mismatch"
    assert procsep.judge(fake(), N, "/p.py", "", tee, None)[0] == "no_frame"
    _, t_noclose, tx = tee_of(["abc"], close=False)
    assert procsep.judge(fake(), N, "/p.py", tx, t_noclose, {"stdout": "abc", "stdout_trunc": False})[0] == "incomplete"
    _, t_lie, tx = tee_of(["abc"], total=99)  # closing record claims more than was received
    assert procsep.judge(fake(), N, "/p.py", tx, t_lie, {"stdout": "abc", "stdout_trunc": False})[0] == "incomplete"
    assert procsep.judge(fake(stderr_truncated=True), N, "/p.py", text, tee, {"stdout": "abc", "stdout_trunc": False})[0] == "incomplete"


def test_parser_gap_reorder_duplicate_foreign():
    s = rec(N, 0, "O") + rec(N, 2, "W", b"x") + rec(N, 3, "C", b"1")
    assert procsep.parse_tee(s, N)[1]["gaps"] == 1
    assert procsep.parse_tee(rec(N, 0, "O") + rec(N, 1, "C", b"0") + rec(N, 2, "C", b"0"), N)[1]["malformed"] == 1  # duplicate close
    assert procsep.parse_tee(rec(N, 0, "O") + rec(N, 1, "O"), N)[1]["malformed"] == 1
    assert procsep.parse_tee(rec("cd" * 16, 0, "O"), N)[1]["foreign"] == 1
    assert procsep.parse_tee("junk " + rec(N, 0, "O") + "tail", N)[0] == "junk tail"  # genuine stderr survives, records removed


def test_supervisor_restores_spawn_and_flags_unsupervised(tmp_path):
    orig = ISO.run_script
    with procsep.Supervisor(str(tmp_path / "a.py"), str(tmp_path / "b.py")) as sup:
        assert ISO.run_script != orig
        (tmp_path / "x.py").write_text("print(1)")
        sup._spawn(str(tmp_path / "x.py"), [], timeout_s=5)
    assert ISO.run_script is orig and sup.extra and not sup.document.__self__.runs
    with pytest.raises(RuntimeError):
        with procsep.Supervisor("a", "b"): raise RuntimeError
    assert ISO.run_script is orig


def test_decide_is_fail_safe():
    ok, bad = {"trusted": True, "reasons": []}, {"trusted": False, "reasons": ["x"]}
    for v in ("DIVERGENT_OBSERVABLE", "NO_DIVERGENCE_OBSERVED", "INSUFFICIENT"):
        assert procsep.decide(v, bad)["verdict"] == "INSUFFICIENT" and procsep.decide(v, ok)["verdict"] == v
    assert procsep.decide("NO_DIVERGENCE_OBSERVED", {"trusted": None, "reasons": []})["verdict"] == "NO_DIVERGENCE_OBSERVED"  # legacy dir: nothing to contradict
