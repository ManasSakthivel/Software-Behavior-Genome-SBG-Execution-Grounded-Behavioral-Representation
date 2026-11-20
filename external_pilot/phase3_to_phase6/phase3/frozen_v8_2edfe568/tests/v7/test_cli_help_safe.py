"""Regression: --help / bad arguments on the spike and baselines scripts must not run work or touch results/ (Phase 1 incident)."""
import hashlib, os, pathlib, subprocess, sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CMDS = {"k1_spike": [sys.executable, str(ROOT / "experiments/v7b/k1_spike.py")],
        "baselines": [sys.executable, "-m", "sbgv7.baselines.run"]}


def _snapshot():
    """(path, size, mtime_ns) for every file under results/ plus a content hash of the small summary files that `summarize` writes."""
    out = []
    for p in sorted((ROOT / "results").rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            st = p.stat(); out.append((str(p), st.st_size, st.st_mtime_ns))
    return out


def _run(name, args, env_extra=None):
    env = dict(os.environ, OMP_NUM_THREADS="1")
    env.update(env_extra or {})
    return subprocess.run(CMDS[name] + args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)


@pytest.mark.parametrize("name", list(CMDS))
@pytest.mark.parametrize("args", [["--help"], ["-h"], ["run", "--help"], ["summarize", "--help"]])
def test_help_exits_0_prints_usage_and_writes_nothing(name, args):
    before = _snapshot()
    r = _run(name, args)
    assert r.returncode == 0, r.stderr
    assert "Usage" in r.stdout or "usage" in r.stdout
    assert _snapshot() == before, "--help changed files under results/"


@pytest.mark.parametrize("name", list(CMDS))
@pytest.mark.parametrize("args", [[], ["bogus"], ["--arms", "quixbugs"]])
def test_missing_or_unknown_command_exits_2_and_writes_nothing(name, args):
    before = _snapshot()
    r = _run(name, args)
    assert r.returncode == 2 and "usage" in r.stderr.lower()
    assert _snapshot() == before


@pytest.mark.parametrize("name", list(CMDS))
def test_help_runs_no_subprocess_engine(name):
    """--help must return quickly (no sandboxed child runs); a real run takes >> this."""
    import time
    t = time.monotonic(); r = _run(name, ["--help"]); assert r.returncode == 0
    assert time.monotonic() - t < 10
