import os, sys
import numpy as np, pytest
sys.path.insert(0, os.path.dirname(__file__))
from _synth import make_records, ers_factory
from sbgv8 import baselines, schema, calibrate
from sbgv8.schema import EvidenceRecord, InputEvidence

DIV, INS, NDO = schema.VERDICTS


def rec(outcomes, act_hit=(10, 11), v7="NO_DIVERGENCE_OBSERVED", y=0, **kw):
    ins = [InputEvidence(f"i{k}", o, obs_fingerprint=f"f{k}", deterministic=(o != "QUARANTINED"), channels_present=list(schema.CHANNELS),
                         hits={"base": list(act_hit), "variant": list(act_hit)}) for k, o in enumerate(outcomes)]
    return EvidenceRecord("p", "P", y=y, inputs=ins, v7b_verdict=v7, changed_units={"base": [10, 11], "variant": [10, 11]}, **kw)


def test_registry_has_all_baselines_and_ablations():
    need = {"b1_plain_dt", "b2_b1_repetition", "b3_v7b_gate", "b4_cov_gate", "b5_cov_gated_b1", "b6_matched_abstention",
            "b7_cov_calibration", "b8_full_cec", "b9_cec_no_ers", "abl_mult_only", "abl_cov_rep", "abl_cov_mult", "abl_cov_infl", "abl_cov_prov", "abl_full_profile"}
    assert need <= set(baselines.REGISTRY)
    with pytest.raises(KeyError): baselines.make("nope", [])


def test_rule_verdicts_hand_cases():
    w = rec(["SAME", "CONFIRMED_DIFF"]); same = rec(["SAME", "SAME"]); q = rec(["SAME", "QUARANTINED"]); part = rec(["SAME"], act_hit=(10,))
    mk = lambda n, r: baselines.make(n, None).decide(r)[0]
    assert [mk("b1_plain_dt", r) for r in (w, same, q, part)] == [DIV, NDO, NDO, NDO]
    assert [mk("b2_b1_repetition", r) for r in (w, same, q, part)] == [DIV, NDO, INS, NDO]
    assert mk("b3_v7b_gate", rec(["SAME"], v7="INSUFFICIENT")) == INS
    assert [mk("b4_cov_gate", r) for r in (w, same, q, part)][0] == DIV
    assert mk("b4_cov_gate", same) == NDO and mk("b4_cov_gate", part) == INS
    assert mk("b5_cov_gated_b1", same) == NDO and mk("b5_cov_gated_b1", part) == INS and mk("b5_cov_gated_b1", w) == DIV
    pr = baselines.make("b1_plain_dt", None); assert pr.decide(same) == (NDO, 0.0) and pr.predict_risk(w) == 1.0


def test_matched_abstention_does_not_improve_risk():
    R = make_records(seed=1, n_proj=60)
    nonwit = [r for r in R if not calibrate.has_witness(r)]; base = np.mean([r.y for r in nonwit])
    r = baselines.matched_abstention_risk(R, 0.3, draws=1000, seed=0)
    assert abs(r - base) < 0.02
    assert baselines.matched_abstention_risk(R, 0.3, 200, 0) == baselines.matched_abstention_risk(R, 0.3, 200, 0)   # seeded


def test_model_baselines_fit_and_predict():
    R = make_records(seed=2, n_proj=40)
    for n in ("b7_cov_calibration", "b9_cec_no_ers", "abl_mult_only", "abl_cov_rep"):
        m = baselines.make(n, R, B=100)
        v, p = m.decide(R[0]); assert 0 <= p <= 1 and v in schema.VERDICTS
        assert hasattr(m, "taus") and set(m.taus) == {0.10, 0.15}
    with pytest.raises(ValueError): baselines.make("b8_full_cec", R)
    fn, names = ers_factory(None)
    m8 = baselines.make("b8_full_cec", R, extra_features_fn=fn, extra_names=names, B=100)
    assert "ers_hid" in m8.coef_report()["coefficients"][-1]["feature"]


def test_decision_uses_tau_never_labels():
    R = make_records(seed=3, n_proj=40); m = baselines.make("b9_cec_no_ers", R, B=100)
    v1 = [m.decide(r)[0] for r in R]
    for r in R: r.y = None
    assert v1 == [m.decide(r)[0] for r in R]
