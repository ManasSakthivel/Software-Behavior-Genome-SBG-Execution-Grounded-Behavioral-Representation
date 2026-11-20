import copy, json, os, sys
import numpy as np, pytest
sys.path.insert(0, os.path.dirname(__file__))
from _synth import make_records, ers_factory
from sbgv8 import evaluate, calibrate, stats, schema

B = 300; KW = dict(B=B, fit_B=100, plots=False)


def _run(tmp_path, R, name="o", seed=0, factory=ers_factory, **kw):
    return evaluate.run(R, str(tmp_path / name), seed, ers_factory=factory, **{**KW, **kw})


def _mr(res, system, cstar):
    return [m for m in res["matched_coverage"] if m["system"] == system and m["cstar"] == cstar][0]["risk"]


@pytest.fixture(scope="module")
def mult_res(tmp_path_factory):
    d = tmp_path_factory.mktemp("m")
    return evaluate.run(make_records(mode="mult", seed=11, n_proj=90, per_proj=6), str(d / "o"), 0, ers_factory=ers_factory, **KW), d


def test_outputs_and_banner(mult_res):
    res, d = mult_res
    assert res["banner"] == "DEVELOPMENT DATA, EXPLORATORY, NOT INDEPENDENT VALIDATION"
    for f in ("results.json", "BANNER.txt", "tables/systems.csv", "tables/primary.md", "tables/matched_coverage.csv"):
        assert (d / "o" / f).exists()
    names = {s["system"] for s in res["systems"]}
    assert {"b1_plain_dt", "b2_b1_repetition", "b3_v7b_gate", "b4_cov_gate", "b5_cov_gated_b1", "b7_cov_calibration", "b8_full_cec", "b9_cec_no_ers", "abl_mult_only"} <= names
    assert res["power"]["b3_v7b_gate"]["status"] in ("pilot/exploratory", "adequately-sized-by-count")


def test_multiplicity_recovered_by_cec_without_ers(mult_res):
    res, _ = mult_res
    c = "c=0.3"
    assert _mr(res, "b9_cec_no_ers", c) < _mr(res, "b7_cov_calibration", c) - 0.05
    assert _mr(res, "abl_mult_only", c) < _mr(res, "b7_cov_calibration", c) - 0.05
    # random abstention at the same coverage gives no gain over plain B1 (abstention is not improvement)
    assert abs(_mr(res, "b6_matched_abstention", c) - res["b1_risk_all_nonwitness"]) < 0.03


def test_no_ers_gain_reported_when_ers_is_noise(mult_res):
    res, _ = mult_res
    assert res["ers_added_value"].startswith("NO demonstrated ERS gain")


def test_ers_gain_detected_when_it_carries_information(tmp_path):
    res = _run(tmp_path, make_records(mode="ers", seed=12, n_proj=100, per_proj=6))
    assert res["ers_added_value"].startswith("ERS shows")
    assert _mr(res, "b8_full_cec", "c=0.3") < _mr(res, "b9_cec_no_ers", "c=0.3") - 0.05


def test_ers_unavailable_is_reported_not_faked(tmp_path):
    res = _run(tmp_path, make_records(seed=13, n_proj=40), factory=None)
    assert "b8_full_cec" in res["unavailable_systems"] and res["primary_system"] == "b9_cec_no_ers" and not res["primary_is_full_cec_with_ers"]


def test_no_project_in_two_folds_and_unresolved_counted(tmp_path):
    R = make_records(seed=14, n_proj=40)
    for r in R[:9]: r.y = None
    res = _run(tmp_path, R)
    assert res["n_unresolved_y_none"] == 9 and res["n_labelled"] == len(R) - 9
    proj = np.array([r.project for r in sorted([r for r in R if r.y is not None], key=lambda r: (r.project, r.pair_id))])
    f = stats.project_folds(proj, 5, 0)
    for k in set(f): assert not set(proj[f == k]) & set(proj[f != k])


def test_test_fold_labels_cannot_influence_its_predictions_or_thresholds():
    R = make_records(seed=15, n_proj=50); recs = sorted(R, key=lambda r: (r.project, r.pair_id))
    proj = np.array([r.project for r in recs]); fold = stats.project_folds(proj, 5, 0)
    names = schema.FEATURE_SETS["cov_mult"]; kw = dict(seed=0, B=100, profile_fn=None, ers_factory=None, cache={}, names=names)
    a = evaluate._cv_model(recs, "m", fold, [0, 1, 2, 3, 4], **{k: v for k, v in kw.items()}, with_ers=False)
    R2 = copy.deepcopy(recs)
    for r, g in zip(R2, fold):
        if g == 0: r.y = 1 - r.y                       # corrupt labels of the test fold 0 only
    kw["cache"] = {}
    b = evaluate._cv_model(R2, "m", fold, [0, 1, 2, 3, 4], **kw, with_ers=False)
    te = fold == 0
    assert np.array_equal(a[0][te], b[0][te]) and np.array_equal(a[2][0.15][te], b[2][0.15][te])   # fold-0 outputs identical


def test_deterministic_replay(tmp_path):
    R = make_records(seed=16, n_proj=40)
    a = _run(tmp_path, R, "a"); b = _run(tmp_path, R, "b")
    for r in (a, b): r.pop("runtime_seconds")
    assert json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


def test_no_banner_for_independent_splits(tmp_path):
    res = _run(tmp_path, make_records(seed=17, n_proj=30, split="evaluation"))
    assert "DEVELOPMENT" not in res["banner"]


def test_rank_scores_remove_fold_intercept_artifact():
    sc = np.array([.1, .2, .3, .6, .7, .8]); fold = np.array([0, 0, 0, 1, 1, 1]); el = np.ones(6, bool)
    r = evaluate.rank_scores(sc, el, fold)
    assert r[:3].tolist() == r[3:].tolist()                      # same within-fold ranks despite different offsets
    assert evaluate.rank_scores(np.array([.5, .5, .9]), np.ones(3, bool), np.zeros(3, int)).tolist()[:2] == [1.5 / 3, 1.5 / 3]   # ties stay tied
