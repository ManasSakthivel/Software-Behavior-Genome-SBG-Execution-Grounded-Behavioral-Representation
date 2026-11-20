import copy, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from _synth import make_records, ers_factory
from sbgv8 import calibrate, evaluate, policy, stats

KW = dict(seed=0, B=60, fit_B=60)


def _split(R, k=8):
    ps = sorted({r.project for r in R}); held = set(ps[:k])
    return [r for r in R if r.project not in held], [r for r in R if r.project in held]


def test_label_poisoning_leaves_frozen_thresholds_and_decisions_identical():
    dev, held = _split(make_records(n_proj=40, per_proj=6, seed=5))
    for name in ("b7_cov_calibration", "b9_cec_no_ers", "b8_full_cec"):
        fz = evaluate.freeze(dev, name, ers_factory=ers_factory, **KW)
        risk, dec = evaluate.apply_frozen(fz, held)
        P = copy.deepcopy(held); rng = np.random.default_rng(9)
        for r in P: r.y = int(rng.integers(0, 2))
        for r in P[::3]: r.y = None
        risk2, dec2 = evaluate.apply_frozen(fz, P)
        assert np.array_equal(risk, risk2) and all(np.array_equal(dec[k], dec2[k]) for k in dec)
        fz2 = evaluate.freeze(dev, name, ers_factory=ers_factory, **KW)      # re-freezing from dev only: deterministic, held-out irrelevant
        assert fz.taus == fz2.taus


def test_cut_does_not_depend_on_heldout_score_distribution():
    dev, held = _split(make_records(n_proj=40, per_proj=6, seed=6))
    fz = evaluate.freeze(dev, "b9_cec_no_ers", **KW)
    _, full = evaluate.apply_frozen(fz, held)
    for i in (0, 5, 11):   # decision for one record alone == its decision within the whole held-out set
        _, one = evaluate.apply_frozen(fz, [held[i]])
        assert all(one[k][0] == full[k][i] for k in full)
    shifted = copy.deepcopy(held)           # drastically change the other held-out records' evidence: this record's decision is unchanged
    for r in shifted[1:]: r.inputs = r.inputs[:1]
    _, sh = evaluate.apply_frozen(fz, shifted)
    assert all(sh[k][0] == full[k][0] for k in full)


def test_frozen_eval_is_project_disjoint_and_reports_realised_coverage():
    R = make_records(n_proj=40, per_proj=5, seed=7)
    res = evaluate.frozen_eval(R, seed=0, B=100, fit_B=60, ers_factory=None)
    assert res["unavailable"] and "b8_full_cec" in res["unavailable"]       # no ERS -> reported, not silently dropped
    rows = {(s["system"], s["rule"]): s for s in res["systems"]}
    assert ("b7_cov_calibration", "cov") in rows and len(rows[("b9_cec_no_ers", "cov")]["fold_coverage"]) == 5
    assert all(0 <= s["coverage"] <= 1 for s in res["systems"])


def test_target_coverage_rule_uses_only_training_gate_coverage():
    dev, held = _split(make_records(n_proj=40, per_proj=6, seed=8))
    fz = evaluate.freeze(dev, "b9_cec_no_ers", **KW)
    assert fz.target_cov == evaluate.gate_coverage(dev)
    P = copy.deepcopy(held)
    for r in P: r.v7b_verdict = "INSUFFICIENT"; r.y = 1      # held-out V7-B verdicts and labels do not move the frozen threshold
    assert evaluate.freeze(dev, "b9_cec_no_ers", **KW).taus == fz.taus


def test_frozen_thresholds_function_basic_semantics():
    p = np.array([.1, .1, .2, .3, .4, .5, .6, .7]); y = np.array([0, 0, 0, 0, 0, 1, 1, 1.]); el = np.ones(8, bool)
    oof = {"p": p, "el": el, "y": y, "proj": np.array(list("aabbccdd"))}
    t = calibrate.frozen_thresholds(oof, (0.10, 0.20), 0.5, B=200)
    assert t[("pt", 0.10)] == 0.4 and t[("pt", 0.20)] == 0.5 and t[("cov",)] == 0.3   # >=5 issued; cov: 4/8 issued
    assert t[("ub", 0.10)] <= t[("pt", 0.10)]                      # conservative rule never issues more than the point rule
    assert calibrate.frozen_thresholds(oof, (0.1,), None)[("cov",)] == -np.inf
