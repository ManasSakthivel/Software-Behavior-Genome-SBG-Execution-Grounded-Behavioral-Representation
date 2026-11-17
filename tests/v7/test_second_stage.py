"""Second-stage review of MB-01..MB-16: child environment control (MB-07), output flush (MB-02), determinism table, evidence-integrity wording.
Local environment control only; none of this is validated OS isolation."""
import json, os, subprocess, sys, textwrap

import pytest

from sbgv7 import isolation, runner
from sbgv7 import records as R
from .test_core import BASE, EQV, FAST, go
from .test_backlog_mb import LOG, verified

try:
    SANDBOX = isolation.capabilities()["network_denial"]["state"] == "ACTIVE"
except Exception:  # pragma: no cover
    SANDBOX = False
NEEDS_SANDBOX = pytest.mark.skipif(not SANDBOX, reason="isolation not enforced here")

PROBE = r'''
import json, locale, os, sys, time
mods = {n: getattr(sys.modules.get(n), "__file__", None) for n in ("json", "os", "sitecustomize", "usercustomize", "site")}
print(json.dumps({
    "env": dict(os.environ), "path": sys.path, "cwd": os.getcwd(), "orig_argv": sys.orig_argv,
    "flags": {k: getattr(sys.flags, k) for k in ("isolated", "ignore_environment", "no_user_site", "safe_path", "dont_write_bytecode",
                                                  "utf8_mode", "dev_mode", "inspect", "interactive", "hash_randomization")},
    "hash": hash("a"), "tz": list(time.tzname), "enc": [sys.stdout.encoding, sys.getfilesystemencoding(), locale.getpreferredencoding(False)],
    "warnoptions": sys.warnoptions, "xoptions": sys._xoptions, "bp": sys.breakpointhook is sys.__breakpointhook__, "mods": mods}))
'''
HOSTILE = ["PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT", "PYTHONBREAKPOINT", "LD_PRELOAD", "DYLD_INSERT_LIBRARIES",
           "DYLD_LIBRARY_PATH", "PYTHONUSERBASE", "PYTHONWARNINGS", "PYTHONHASHSEED", "PYTHONSAFEPATH", "PYTHONDONTWRITEBYTECODE",
           "PYTHONIOENCODING", "PYTHONUTF8", "PYTHONMALLOC", "PYTHONDEVMODE", "PYTHONOPTIMIZE", "PYTHONNOUSERSITE", "TZ", "LC_ALL", "LANG",
           "PYTHONPYCACHEPREFIX", "PYTHONPLATLIBDIR", "PYTHON_GIL", "PYTHONFAULTHANDLER", "PYTHONTRACEMALLOC", "PYTHONCOERCECLOCALE"]
STDLIB_SHADOW = "import os\nos._exit(66)\n"


def hostile_env(monkeypatch, evil):
    evil.mkdir(exist_ok=True)
    for m in ("sitecustomize", "usercustomize", "json", "os", "evil"):
        (evil / f"{m}.py").write_text(STDLIB_SHADOW)
    (evil / "site-packages").mkdir(exist_ok=True)
    for k, v in {"PYTHONPATH": str(evil), "PYTHONHOME": "/nonexistent", "PYTHONSTARTUP": str(evil / "os.py"), "PYTHONINSPECT": "1",
                 "PYTHONBREAKPOINT": "evil.bp", "LD_PRELOAD": "/nonexistent/x.so", "DYLD_INSERT_LIBRARIES": "/nonexistent/x.dylib",
                 "DYLD_LIBRARY_PATH": str(evil), "PYTHONUSERBASE": str(evil), "PYTHONWARNINGS": "error", "PYTHONHASHSEED": "random",
                 "PYTHONSAFEPATH": "", "PYTHONDONTWRITEBYTECODE": "", "PYTHONIOENCODING": "latin-1", "PYTHONUTF8": "0", "PYTHONMALLOC": "debug",
                 "PYTHONDEVMODE": "1", "PYTHONOPTIMIZE": "2", "PYTHONNOUSERSITE": "", "TZ": "Asia/Tokyo", "LC_ALL": "de_DE.ISO8859-1",
                 "LANG": "de_DE.ISO8859-1", "PYTHONPYCACHEPREFIX": str(evil), "PYTHONPLATLIBDIR": "evil", "PYTHON_GIL": "0",
                 "PYTHONFAULTHANDLER": "1", "PYTHONTRACEMALLOC": "5", "PYTHONCOERCECLOCALE": "0"}.items():
        monkeypatch.setenv(k, v)


def child_probe(tmp_path):
    p = tmp_path / "probe.py"; p.write_text(PROBE)
    r = isolation.run_script(str(p), sandbox=False, timeout_s=20)
    assert r.status == "OK", (r.status, r.detail, r.stderr[-400:])
    return json.loads(r.stdout), r


REF_HASH = int(subprocess.run([sys.executable, "-c", "print(hash('a'))"], env={"PYTHONHASHSEED": "0"}, capture_output=True, text=True).stdout)


@pytest.mark.parametrize("hostile", [False, True])
def test_child_env_is_exactly_the_allowlist_and_path_is_clean(tmp_path, monkeypatch, hostile):
    evil = tmp_path / "evil"
    if hostile: hostile_env(monkeypatch, evil)
    else:
        for k in HOSTILE: monkeypatch.delenv(k, raising=False)
    o, r = child_probe(tmp_path)
    wd = o["cwd"]
    assert os.path.realpath(o["env"]["HOME"]) == os.path.realpath(o["env"]["TMPDIR"]) == wd  # cwd is the private workdir (symlink-resolved)
    want = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0", "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8:strict", "PYTHONNOUSERSITE": "1", "PYTHONSAFEPATH": "1", "TZ": "UTC", "LC_ALL": "C.UTF-8",
            "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    extra = {k: v for k, v in o["env"].items() if k not in want and k not in ("HOME", "TMPDIR")}
    assert {k: o["env"].get(k) for k in want} == want
    assert set(extra) <= {"__CF_USER_TEXT_ENCODING", "LC_CTYPE"}, extra  # injected by macOS / CPython locale handling, not by us
    assert not any(str(evil) in p or p in ("", ".") or os.path.realpath(p) == wd for p in o["path"]), o["path"]
    f = o["flags"]
    assert (f["no_user_site"], f["safe_path"], f["dont_write_bytecode"], f["utf8_mode"], f["dev_mode"], f["inspect"], f["interactive"]) == (1, True, 1, 1, False, 0, 0)
    assert o["hash"] == REF_HASH and o["tz"] == ["UTC", "UTC"] and o["enc"] == ["utf-8"] * 3
    assert o["warnoptions"] == [] and o["xoptions"] == {} and o["bp"] is True
    assert "-s" in o["orig_argv"] and "-P" in o["orig_argv"] and "-B" in o["orig_argv"] and "-I" not in o["orig_argv"]
    assert not o["mods"]["sitecustomize"] and not o["mods"]["usercustomize"]  # none exists on the clean path
    assert str(evil) not in json.dumps(o["mods"]) and o["mods"]["json"].endswith("json/__init__.py")
    assert r.stderr == ""


def test_child_env_is_built_from_scratch_not_inherited():
    env = isolation.child_env("/w")
    assert set(env) == {"PATH", "HOME", "TMPDIR", "PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED", "PYTHONUTF8", "PYTHONIOENCODING", "PYTHONNOUSERSITE",
                        "PYTHONSAFEPATH", "TZ", "LC_ALL", "OMP_NUM_THREADS", "MKL_NUM_THREADS"}
    assert env["HOME"] == env["TMPDIR"] == "/w"


@NEEDS_SANDBOX
def test_hostile_parent_env_does_not_change_verdict_or_ids(tmp_path, monkeypatch):
    for k in HOSTILE: monkeypatch.delenv(k, raising=False)
    a = go(tmp_path, BASE, BASE.replace("return x\n", "return x + 1\n"), [[0], [5]], name="clean")
    hostile_env(monkeypatch, tmp_path / "evil")
    b = go(tmp_path, BASE, BASE.replace("return x\n", "return x + 1\n"), [[0], [5]], name="hostile")
    drop = lambda d: {k: v for k, v in d.items() if k not in ("cpu_seconds_spent", "log_head")}
    assert drop(a) == drop(b) and a["verdict"] == "DIVERGENT_OBSERVABLE"
    ids = lambda n: sorted(r["id"] for r in R.read_log(LOG(tmp_path, n)) if r["kind"] == "Observation")
    assert ids("clean") == ids("hostile")
    verified(tmp_path, "hostile")


@NEEDS_SANDBOX
def test_program_directory_cannot_shadow_trusted_modules(tmp_path):
    """The untrusted program's directory is put first on the child's sys.path by the harness (sibling imports must work), so every trusted
    import must already be done by then. Every stdlib module name is shadowed by a file that kills the process; the harness must not hit one."""
    for n in sys.stdlib_module_names:
        if n not in ("sys", "builtins") and not n.startswith("_"): (tmp_path / f"{n}.py").write_text(STDLIB_SHADOW)
    src = ("class C:\n    def __init__(s):\n        s.a = 1\n"
           "def f(x):\n    print('hi')\n    return [1, 2.5, 'a', {'k': {1, 2}}, C(), 10 ** 50, (1,), b'x', float('nan')]\n")
    mods_before = {n: getattr(m, "__file__", None) for n, m in sys.modules.items() if n in ("json", "os", "hashlib", "hmac", "random")}
    path_before = list(sys.path)
    o = go(tmp_path, src, src + "# c\n", [[1]])
    assert o["verdict"] != "DIVERGENT_OBSERVABLE" and o["primary"] not in ("tool_error", "unsafe_program"), o
    row = body(tmp_path)["rows"][0]
    assert row["outcome"] == "SAME", row
    assert {n: getattr(sys.modules[n], "__file__", None) for n in mods_before} == mods_before and sys.path == path_before  # parent untouched
    verified(tmp_path)


def body(tp, kind="EvidencePackage", n="out"):
    return [r for r in R.read_log(LOG(tp, n)) if r["kind"] == kind][0]["body"]


# ---------------------------------------------------------------- MB-02: buffered sys.__stdout__ output must not be lost at os._exit(0)
def _buf(t, how):
    return {"write": f"import sys\ndef f(x):\n    sys.__stdout__.write({t!r})\n    return 1\n",
            "print": f"import sys\ndef f(x):\n    print({t!r}, file=sys.__stdout__, end='')\n    return 1\n",
            "import": f"import sys\nsys.__stdout__.write({t!r})\ndef f(x):\n    return 1\n"}[how]


@NEEDS_SANDBOX
@pytest.mark.parametrize("how", ["write", "print", "import"])
def test_buffered_real_stdout_difference_is_observed(tmp_path, how):
    o = go(tmp_path, _buf("A", how), _buf("B", how), [[1]])
    assert o["verdict"] == "DIVERGENT_OBSERVABLE"
    verified(tmp_path)


@NEEDS_SANDBOX
def test_identical_buffered_real_stdout_is_not_divergent(tmp_path):
    o = go(tmp_path, _buf("A", "write"), _buf("A", "write") + "# c\n", [[1]])
    assert o["verdict"] != "DIVERGENT_OBSERVABLE"


@NEEDS_SANDBOX
def test_closed_real_stdout_does_not_break_the_harness(tmp_path):
    src = "import sys\ndef f(x):\n    sys.__stdout__.write('x')\n    sys.__stdout__.close()\n    return 1\n"
    o = go(tmp_path, src, src + "# c\n", [[1]])
    assert o["primary"] != "tool_error" and o["verdict"] != "DIVERGENT_OBSERVABLE"


@NEEDS_SANDBOX
def test_print_then_os_exit_is_a_protocol_violation_not_an_observation(tmp_path):
    """os._exit skips the result frame by design (SD-11): the run is unsafe_program, the buffered print is not an observation, and the pair is never SAME."""
    ex = lambda t: f"import os\ndef f(x):\n    print({t!r})\n    os._exit(0)\n"
    o = go(tmp_path, ex("A"), ex("B"), [[1]])
    assert (o["verdict"], o["primary"]) == ("INSUFFICIENT", "unsafe_program")
    assert body(tmp_path)["rows"][0]["outcome"] == "NO_RUN"


# ---------------------------------------------------------------- determinism: alt-control virtualisation of secrets (SD-09 extension) and the datetime limit
def _alt(tmp_path, prog, ctls):
    from .test_backlog_mb import _alt_runs
    return _alt_runs(tmp_path, prog, ctls)


@NEEDS_SANDBOX
def test_alt_virtualises_secrets_and_systemrandom(tmp_path):
    prog = "import secrets, random\ndef f(x):\n    return [secrets.token_hex(8), secrets.randbelow(10**9), random.SystemRandom().getrandbits(32)]\n"
    a1, a2, b = _alt(tmp_path, prog, [1, 1, 2])
    assert a1 == a2 and a1 != b


@NEEDS_SANDBOX
def test_primary_runs_keep_real_entropy(tmp_path):
    prog = "import secrets, os\ndef f(x):\n    return [secrets.token_hex(8), os.urandom(4).hex()]\n"
    a, b = _alt(tmp_path, prog, [None, None])
    assert a != b


@NEEDS_SANDBOX
def test_datetime_now_is_NOT_virtualised_documented_limit(tmp_path):
    """Characterisation (SD-09: datetime.now is documented as not virtualised). If this ever fails, the limit was lifted: update the docs table."""
    prog = "import datetime, time\ndef f(x):\n    return abs(datetime.datetime.now().timestamp() - time.time()) > 500\n"
    r1, r0 = _alt(tmp_path, prog, [1, None])
    assert r1[1] is True and r0[1] is False  # alt shifted time.time() only; datetime.now() still reads the real clock


# ---------------------------------------------------------------- evidence-integrity wording (V7-B docs only)
def test_v7b_docs_do_not_claim_tamper_proof():
    import re
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bad = re.compile(r"tamper[- ]?proof|tamper[- ]resistant|cannot be (forged|altered|modified)|unforgeable|immutable", re.I)
    files = [os.path.join(root, "docs", "architecture", n) for n in os.listdir(os.path.join(root, "docs", "architecture"))]
    files += [os.path.join(root, "sbgv7", n) for n in os.listdir(os.path.join(root, "sbgv7")) if n.endswith(".py")]
    neg = re.compile(r"\b(not|never|no)\b", re.I)  # a negated mention ("is not tamper-proof") is the honest wording
    hits = [(f, l.strip()[:80]) for f in files if f.endswith((".md", ".py")) for l in open(f).read().splitlines() if bad.search(l) and not neg.search(l)]
    assert not hits, hits
    impl = open(os.path.join(root, "docs", "architecture", "V7B_IMPLEMENTATION.md")).read()
    assert "not tamper-evident" in impl and "trust anchor" in impl.lower()
