import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from _synth import make_records, ers_factory
from sbgv8 import evaluate, stats


def test_slope_cluster_ci_covers_a_calibrated_predictor_and_is_wide_for_few_projects():
    rng = np.random.default_rng(0); n = 600; proj = np.repeat(np.arange(60), 10)
    p = rng.uniform(.1, .9, n); y = (rng.random(n) < p).astype(float)
    ci = stats.slope_cluster_ci(p, y, proj, B=300, seed=1)
    assert ci["slope_ci95"][0] < 1 < ci["slope_ci95"][1] and ci["n_valid"] > 250
    few = stats.slope_cluster_ci(p[:60], y[:60], proj[:60], B=300, seed=1)["slope_ci95"]
    assert few[1] - few[0] > ci["slope_ci95"][1] - ci["slope_ci95"][0]


def test_paired_logloss_detects_planted_difference_and_not_null():
    rng = np.random.default_rng(1); proj = np.repeat(np.arange(50), 8); true = rng.uniform(.1, .9, 400); y = (rng.random(400) < true).astype(float)
    good = stats.paired_logloss(true, np.full(400, y.mean()), y, proj, 500)
    assert good["ci95"][0] > 0
    a_, b_ = (np.clip(true + rng.normal(0, .03, 400), .01, .99) for _ in range(2))   # two equally noisy copies: no real difference
    r = stats.paired_logloss(a_, b_, y, proj, 500)
    assert abs(r["point"]) < 0.03 < good["point"] and r["ci95"][1] - r["ci95"][0] > 0


def test_permutation_p_bounds():
    assert stats.permutation_p(10, np.zeros(99)) == 1 / 100 and stats.permutation_p(-1, np.zeros(99)) == 1.0


def test_ers_placebo_flags_planted_signal_not_noise():
    sig = evaluate.ers_placebo(make_records(n_proj=70, per_proj=6, mode="ers", seed=3), 0, n_perm=15, fit_B=30, ers_factory=ers_factory)
    assert sig["observed_gain_b9_minus_b8"] > 0 and sig["placebo_p"] <= 0.2 and sig["paired_cluster_bootstrap"]["ci95"][1] > 0
    nul = evaluate.ers_placebo(make_records(n_proj=70, per_proj=6, mode="mult", seed=3), 0, n_perm=15, fit_B=30, ers_factory=ers_factory)
    assert nul["placebo_p"] > sig["placebo_p"] - 1e-9 and nul["observed_gain_b9_minus_b8"] < sig["observed_gain_b9_minus_b8"]
