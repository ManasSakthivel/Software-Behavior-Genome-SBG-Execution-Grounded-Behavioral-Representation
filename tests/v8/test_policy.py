import copy, os, sys
import numpy as np, pytest
sys.path.insert(0, os.path.dirname(__file__))
from _synth import make_records
from sbgv8 import calibrate, evaluate, policy, profile


def _el(R, name):
    with policy.use(name): return {r.pair_id for r in R if calibrate.is_eligible(r)}


def test_default_is_v80_and_use_restores():
    assert policy.current() == "v8.0"
    with policy.use("v8.1"): assert policy.current() == "v8.1"
    assert policy.current() == "v8.0"
    with pytest.raises(KeyError): policy.set_policy("v9.9")
    assert policy.current() == "v8.0"


def test_v80_soft_blockers_v81_hard():
    r = make_records(n_proj=3, per_proj=2, seed=0)[1]; r.inputs = [i for i in r.inputs if i.outcome == "SAME"]; r.y = 0
    r.blockers = [("changed_region_not_activated", "1 unit(s) unhit")]
    assert _el([r], "v8.0") == {r.pair_id} and _el([r], "v8.0s") == set() and _el([r], "v8.1") == set()
    r.blockers = [("budget_exhausted_s0", "x")]
    assert _el([r], "v8.0") == {r.pair_id} and _el([r], "v8.1") == set()
    r.blockers = [("unmodelled_change", "x")]
    assert _el([r], "v8.0") == set()           # hard in every version


def test_v81_rederives_unhit_units_even_without_recorded_blocker():
    R = make_records(n_proj=30, per_proj=4, seed=1)   # act 0.5 records: unit 11 never hit, NO recorded blocker
    part = [r for r in R if not r.blockers and profile.build_profile(r)["act_frac"] < 1 and not calibrate.has_witness(r)]
    assert part
    assert all(r.pair_id in _el(R, "v8.0") for r in part) and all(r.pair_id not in _el(R, "v8.1") for r in part)


def test_v81_equals_v7b_style_ndo_and_is_subset_of_v80():
    R = make_records(n_proj=30, per_proj=4, seed=2)
    a, b = _el(R, "v8.0"), _el(R, "v8.1")
    assert b <= a and b
    assert b == {r.pair_id for r in R if not calibrate.is_div(r) and profile.v7b_style_decision(r)[0] == "NO_DIVERGENCE_OBSERVED"}


def test_policies_never_read_y():
    R = make_records(n_proj=20, per_proj=4, seed=3); P = copy.deepcopy(R); rng = np.random.default_rng(0)
    for r in P: r.y = int(rng.integers(0, 2))
    for n in policy.POLICIES: assert _el(R, n) == _el(P, n)


def test_named_policy_is_reproducible_and_recorded(tmp_path):
    R = make_records(n_proj=12, per_proj=4, seed=4)
    r1 = evaluate.run(R, str(tmp_path / "a"), 0, B=50, fit_B=30, plots=False, ers_factory=None, policy_name="v8.1")
    r2 = evaluate.run(R, str(tmp_path / "b"), 0, B=50, fit_B=30, plots=False, ers_factory=None, policy_name="v8.1")
    assert r1["policy"] == "v8.1" and policy.current() == "v8.0"
    f = lambda r: [(s["system"], s["coverage"], s["n_issued_ndo"]) for s in r["systems"]]
    assert f(r1) == f(r2)
    # v8.1 can only restrict V7-B's NDO set: every model system has n eligible scored <= V7-B NDO count
    n_ndo = sum(r.v7b_verdict == "NO_DIVERGENCE_OBSERVED" and r.y is not None for r in R)
    assert all(s["n_eligible_scored"] <= max(n_ndo, 0) + 0 for s in r1["systems"] if "n_eligible_scored" in s)
