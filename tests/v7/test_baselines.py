import json, random
import pytest
from sbgv7.baselines import baselines as B

BASE = "def f(x):\n    if x > 10:\n        return x\n    return 0\n"
VAR = "def f(x):\n    if x > 10:\n        return x + 1\n    return 0\n"  # differs only for x > 10
ID = lambda n: [{"id": f"i{k}", "args": [v], "kwargs": {}} for k, v in enumerate(n)]


@pytest.fixture
def pair(tmp_path):
    (tmp_path / "a.py").write_text(BASE); (tmp_path / "b.py").write_text(VAR)
    mk = lambda tag: B.make_ctx(str(tmp_path / "a.py"), str(tmp_path / "b.py"), "f", {"budget": {"cpu_seconds": 30, "per_run": {"cpu_s": 2, "wall_s": 5}}}, str(tmp_path / tag))[0]
    return mk


def test_b1_diverge_and_nodiff(pair):
    assert B.b1(pair("x"), ID([1, 50]), 30)["verdict"] == B.DIVERGE
    r = B.b1(pair("y"), ID([1, 2]), 30)  # abstention-free: unactivated change is NO_DIFF, never INSUFFICIENT
    assert r["verdict"] == B.NO_DIFF and r["n_runs"] == 4


def test_b1_rep_replays_only_candidates(pair):
    assert B.b1_rep(pair("x"), ID([50]), 30)["verdict"] == B.DIVERGE
    r = B.b1_rep(pair("y"), ID([1]), 30)
    assert r["verdict"] == B.NO_DIFF and r["n_runs"] == 6  # r_det=3 per side, no replay


def test_b2_pass_fail(pair):
    assert B.b2(pair("x"), ID([50]), [50], 30)["verdict"] == B.DIVERGE  # base passes, variant fails
    assert B.b2(pair("y"), ID([1]), [0], 30)["verdict"] == B.NO_DIFF


def test_b3_finds_what_seeds_miss_and_is_seeded(pair):
    r1 = B.b3(pair("x"), ID([1]), 30, seed=7, max_execs=40)
    r2 = B.b3(pair("y"), ID([1]), 30, seed=7, max_execs=40)
    assert r1["verdict"] == B.DIVERGE and r1["input"].startswith("m")  # seed 1 is unactivated; mutant is
    assert (r1["input"], r1["witness_args"]) == (r2["input"], r2["witness_args"])


def test_b3_budget_respected(pair):
    r = B.b3(pair("x"), ID([1]), 0.0, seed=1)
    assert r["n_runs"] == 0 and r["verdict"] == B.NO_DIFF


def test_mutator_deterministic_and_json():
    a = [B._mut([1, "ab", {"k": 2.5}, None, True], random.Random(3)) for _ in range(1)]
    b = [B._mut([1, "ab", {"k": 2.5}, None, True], random.Random(3)) for _ in range(1)]
    assert a == b and json.dumps(a)


def test_plain():
    assert B.plain(["tuple", [["int", "1"], ["str", "a"]]]) == [1, "a"]


def test_threshold_dev_only_rule():
    t, ba = B.tune_threshold([1, 2, 8, 9], [False, False, True, True])
    assert 3 <= t <= 8 and ba == 1.0 and B.b4(9, t) == B.DIVERGE and B.b4(1, t) == B.NO_DIFF


def test_edit_size(tmp_path):
    (tmp_path / "a.py").write_text(BASE); (tmp_path / "b.py").write_text(VAR)
    assert B.edit_size(str(tmp_path / "a.py"), str(tmp_path / "b.py")) == 2
