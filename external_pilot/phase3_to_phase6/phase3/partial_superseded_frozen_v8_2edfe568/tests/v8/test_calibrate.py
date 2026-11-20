import copy, math, os, sys, zlib
import numpy as np, pytest
sys.path.insert(0, os.path.dirname(__file__))
from _synth import make_records, ers_factory
from sbgv8 import calibrate, schema

FULL = schema.FEATURE_SETS["full_profile"]


def test_signs_enforced_even_when_data_disagree():
    R = make_records(mode="mult", seed=1)
    for r in R: r.y = int(np.random.default_rng(zlib.crc32(r.pair_id.encode())).random() < .4)   # y independent of everything
    m = calibrate.fit(R, FULL, lam=0.01)
    for row in m.coef_report()["coefficients"]:
        if row["declared_sign"] < 0: assert row["std_coef"] <= 1e-9
        if row["declared_sign"] > 0: assert row["std_coef"] >= -1e-9
    # planted POSITIVE relation between multiplicity and risk: constrained model must not use it
    for r in R: r.y = int(len(r.inputs) >= 4)
    m2 = calibrate.fit(R, schema.FEATURE_SETS["cov_mult"], lam=0.01)
    assert all(c["std_coef"] <= 1e-9 for c in m2.coef_report()["coefficients"])


def test_recovers_planted_multiplicity_effect():
    R = make_records(mode="mult", seed=2, n_proj=100)
    m = calibrate.fit(R, schema.FEATURE_SETS["cov_mult"])
    byf = {c["feature"]: c["std_coef"] for c in m.coef_report()["coefficients"]}
    assert byf["mu_min"] + byf["mu_mean"] + byf["n_same"] < -0.3
    lo = [r for r in R if r.y is not None and len(r.inputs) == 1 and calibrate.is_eligible(r)][0]
    hi = [r for r in R if len(r.inputs) == 6 and calibrate.is_eligible(r)][0]
    assert m.predict_risk(lo) > m.predict_risk(hi)
    cov = calibrate.fit(R, schema.FEATURE_SETS["cov_only"])
    assert abs(cov.predict_risk(lo) - cov.predict_risk(hi)) < 0.1     # coverage-only cannot see it


def test_fit_uses_eligible_only_and_counts_unlabelled():
    R = make_records(n_proj=20, seed=3)
    for r in R[:7]: r.y = None
    m = calibrate.fit(R, FULL)
    exp = sum(1 for r in R if r.y is not None and calibrate.is_eligible(r))
    assert m.info["n_train_eligible_labelled"] == exp and m.info["n_skipped_y_none"] == 7
    assert m.info["n_ineligible_excluded"] == sum(not calibrate.is_eligible(r) for r in R)


def test_y_never_used_at_prediction_and_decide_semantics():
    R = make_records(n_proj=30, seed=4); m = calibrate.fit(R, FULL); m.tau = 0.4
    R2 = copy.deepcopy(R)
    for r in R2: r.y = None if r.y is None else 1 - r.y
    assert [m.predict_risk(r) for r in R] == [m.predict_risk(r) for r in R2]
    for r in R:
        v, risk = m.decide(r)
        if calibrate.is_div(r): assert v == "DIVERGENT_OBSERVABLE"
        elif calibrate.is_eligible(r) and risk <= 0.4: assert v == "NO_DIVERGENCE_OBSERVED"
        else: assert v == "INSUFFICIENT"
    m.tau = -math.inf
    assert all(m.decide(r)[0] != "NO_DIVERGENCE_OBSERVED" for r in R)
    blocked = copy.deepcopy(R[0]); blocked.blockers = [("flaky_witness", "x")]; m.tau = 1.0
    assert m.decide(blocked)[0] == "INSUFFICIENT" or calibrate.is_div(blocked)


def test_threshold_for_risk_monotone_in_alpha_and_bound():
    R = make_records(mode="mult", seed=5, n_proj=120); m = calibrate.fit(R, schema.FEATURE_SETS["cov_mult"])
    t10, i10 = calibrate.threshold_for_risk(R, 0.10, m, B=300); t30, i30 = calibrate.threshold_for_risk(R, 0.30, m, B=300)
    assert i30["coverage"] >= i10["coverage"] and (i30["ub"] <= 0.30)
    assert i10["coverage"] == 0 or i10["ub"] <= 0.10


def test_recalibration_monotone():
    R = make_records(seed=6, n_proj=60); m = calibrate.fit(R[:200], schema.FEATURE_SETS["cov_mult"])
    for meth in ("platt", "iso"):
        m.recal = None; m.recalibrate(R[200:], meth)
        ps = [m.predict_risk(r) for r in sorted(R, key=m.raw_logit)]
        assert all(b >= a - 1e-9 for a, b in zip(ps, ps[1:])) and m.recal[0] == meth


def test_crc_joint_risk_bound_on_calibration_set():
    R = make_records(seed=7, n_proj=100); m = calibrate.fit(R[:300], schema.FEATURE_SETS["cov_mult"])
    cal = R[300:]; t = calibrate.crc_threshold(cal, m, 0.2, by_project=True)
    if t > -math.inf:
        s, e = calibrate.scores(m, cal); y = np.array([r.y for r in cal])
        J = np.mean((s <= t) & e & (y == 1)); assert J <= 0.2
    assert calibrate.crc_threshold(cal[:3], m, 0.01) == -math.inf     # too few units: refuses


def test_deterministic_fit():
    R = make_records(seed=8, n_proj=30)
    a = calibrate.fit(R, FULL); b = calibrate.fit(R, FULL)
    assert (a.coef == b.coef).all() and a.intercept == b.intercept


def test_soft_blocker_is_eligible_hard_is_not():
    r = make_records(n_proj=1, per_proj=1, seed=9, p_witness=0)[0]
    r.blockers = [["changed_region_not_activated", "x"]]; assert calibrate.is_eligible(r)
    r.blockers = [["unmodelled_change", "x"]]; assert not calibrate.is_eligible(r)
    r.blockers = [["changed_region_not_activated", "x"]]; calibrate.STRICT_BLOCKERS = True
    try: assert not calibrate.is_eligible(r)
    finally: calibrate.STRICT_BLOCKERS = False
