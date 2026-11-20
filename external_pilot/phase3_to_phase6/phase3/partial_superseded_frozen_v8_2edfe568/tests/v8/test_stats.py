import numpy as np, pytest
from sbgv8 import stats


def test_matched_risk_hand_computed():
    s = [.1, .2, .3, .4]; y = [0, 1, 0, 1]; e = [True] * 4
    assert stats.matched_risk(s, e, y, 0.5) == 0.5          # lowest two: y=0,1
    assert stats.matched_risk(s, e, y, 0.25) == 0.0
    assert stats.matched_risk(s, e, y, 1.0) == 0.5
    # ties: three tied at .1 (y 0,0,1), k=2 -> fractional inclusion, expected risk 1/3
    assert stats.matched_risk([.1, .1, .1, .9], [True] * 4, [0, 0, 1, 1], 0.5) == pytest.approx(1 / 3)
    # ineligible never issued; unreachable coverage -> nan
    assert np.isnan(stats.matched_risk([.1, .2, .3, .4], [True, False, False, False], [0, 1, 1, 1], 0.5))
    assert stats.matched_risk([.1, .2, .3, .4], [True, False, True, False], [0, 1, 1, 1], 0.5) == 0.5


def test_matched_risk_bootstrap_weights_match_expansion():
    rng = np.random.default_rng(1); n = 40
    s = rng.random(n); y = (rng.random(n) < .3).astype(float); e = np.ones(n, bool)
    w = rng.integers(0, 3, n).astype(float)
    idx = np.repeat(np.arange(n), w.astype(int))
    assert stats.matched_risk(s, e, y, 0.4, w[None, :])[0] == pytest.approx(stats.matched_risk(s[idx], e[idx], y[idx], 0.4))


def test_random_abstention_gives_no_risk_gain():
    rng = np.random.default_rng(0); n = 4000; y = (rng.random(n) < .25).astype(float)
    base = y.mean(); r = np.mean([stats.matched_risk(rng.random(n), np.ones(n, bool), y, 0.3) for _ in range(50)])
    assert abs(r - base) < 0.02
    # an informative score does improve
    sc = y + rng.normal(0, .5, n)
    assert stats.matched_risk(sc, np.ones(n, bool), y, 0.3) < base - 0.1


def test_cluster_bootstrap_deterministic_and_project_level():
    proj = np.repeat(np.arange(10), 3)
    a = stats.cluster_counts(proj, 50, 7); b = stats.cluster_counts(proj, 50, 7)
    assert (a == b).all()
    assert (a.reshape(50, 10, 3).std(2) == 0).all()          # all pairs of a project share a weight
    assert (a.sum(1) == 30).all()


def test_bootstrap_ci_coverage_on_clustered_simulation():
    rng = np.random.default_rng(3); true_p = 0.3; hits = 0; sims = 80
    for s in range(sims):
        P = 40; m = 5
        pj = rng.beta(1.2, 2.8, P)                       # mean 0.3, strong between-project variation
        y = np.concatenate([(rng.random(m) < pj[k]).astype(float) for k in range(P)]); proj = np.repeat(np.arange(P), m)
        W = stats.cluster_counts(proj, 300, s)
        reps = (W * y).sum(1) / W.sum(1); lo, hi = stats.pct_ci(reps)
        hits += lo <= true_p <= hi
    assert hits / sims >= 0.85


def test_project_folds_no_leakage_and_balanced():
    proj = np.array([f"p{i%23}" for i in range(200)]); f = stats.project_folds(proj, 5, 1)
    for k in range(5): assert not set(proj[f == k]) & set(proj[f != k])
    assert (f == stats.project_folds(proj, 5, 1)).all()


def test_holm_and_p():
    assert stats.holm([0.01, 0.04, 0.03]).tolist() == pytest.approx([0.03, 0.06, 0.06])
    assert stats.boot_p_one_sided(np.array([1., 1, 1, -1])) == pytest.approx(2 / 5)


def test_metrics_calibrated_probabilities():
    rng = np.random.default_rng(0); p = rng.uniform(.05, .95, 20000); y = (rng.random(20000) < p).astype(float)
    ci, sl = stats.calibration_slope_intercept(p, y)
    assert abs(ci) < 0.08 and abs(sl - 1) < 0.08
    assert stats.ece(p, y) < 0.03 and set(stats.ece_sensitivity(p, y)) >= {"u5", "u10", "q10"}
    assert stats.brier(p, y) < stats.brier(np.full_like(p, y.mean()), y)
    assert stats.logloss([0.5, 0.5], [0, 1]) == pytest.approx(np.log(2))


def test_select_threshold_respects_alpha_and_nothing_if_impossible():
    rng = np.random.default_rng(2); n = 600; proj = np.repeat(np.arange(120), 5)
    sc = rng.random(n); y = (rng.random(n) < sc * 0.5).astype(float)    # risk = sc/2
    tau, info = stats.select_threshold(sc, np.ones(n, bool), y, proj, 0.15, B=300, seed=0)
    assert 0 < info["coverage"] < 1 and info["ub"] <= 0.15 and tau < 0.8
    t2, i2 = stats.select_threshold(sc, np.ones(n, bool), np.ones(n), proj, 0.1, B=100)
    assert t2 == -np.inf and i2["coverage"] == 0


def test_power_report_downgrades_to_pilot():
    proj = np.repeat(np.arange(30), 3); y = np.tile([0, 1, 0], 30)
    r = stats.power_report(proj, y, np.ones(90, bool)); assert r["status"] == "pilot/exploratory" and "design_effect" in r
    proj = np.repeat(np.arange(80), 3); y = np.random.default_rng(0).integers(0, 2, 240)
    assert stats.power_report(proj, y, np.ones(240, bool))["status"] != "pilot/exploratory"


def test_redundancy_flags_duplicate_feature():
    rng = np.random.default_rng(0); a = rng.normal(size=200); X = np.c_[a, a * 2 + 0.01 * rng.normal(size=200), rng.normal(size=200)]
    t = stats.redundancy_table(X, ["a", "b", "c"]); assert any({p[0], p[1]} == {"a", "b"} for p in t["redundant_pairs"]) and t["vif"]["a"] > 10


def test_paired_matched_detects_better_score():
    rng = np.random.default_rng(4); n = 800; proj = np.repeat(np.arange(160), 5); y = (rng.random(n) < .3).astype(float)
    good = y + rng.normal(0, .6, n); bad = rng.random(n); e = np.ones(n, bool)
    d = stats.paired_matched(good, e, bad, e, y, proj, 0.3, B=500, seed=0, jackknife=False)
    assert d["diff_b_minus_a"] > 0.1 and d["lower97.5_one_sided"] > 0 and d["p_one_sided"] < 0.01
