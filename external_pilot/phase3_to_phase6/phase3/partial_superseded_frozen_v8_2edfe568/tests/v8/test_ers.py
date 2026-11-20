import pytest
from sbgv8 import ers
from sbgv8.ers import ActivationStubPredictor, compute_ers, ers_vector, run_matrix
from sbgv8.schema import EvidenceRecord, InputEvidence as I, PERTURBATIONS
from sbgv8.profile import build_profile

def inp(i, hits, **kw):
    return I(i, "SAME", obs_fingerprint=f"f{i}", channels_present=["outcome", "exception"], n_repeat_runs=4,
             hits={"base": hits, "variant": hits}, **kw)

def rec(**kw):
    return EvidenceRecord("p", "proj", changed_units={"base": [10, 11], "variant": [10, 11]},
                          inputs=[inp("a", [10, 11, 5]), inp("b", [11, 5]), inp("c", [5])], **kw)

class Credulous:
    """Bad predictor: credits quantity (raw input count)."""
    def predict_risk(self, r): return 1.0 / (1 + len(r.inputs))
    def decide(self, r): return ("NO_DIVERGENCE_OBSERVED", self.predict_risk(r))

STUB = ActivationStubPredictor()

def test_stub_passes_all_applicable():
    e = {p: compute_ers(rec(), STUB, p) for p in PERTURBATIONS}
    assert all(x.passed is True for x in e.values()), {p: (x.passed, x.observed) for p, x in e.items()}

def test_stub_p1_delta_positive():
    e = compute_ers(rec(), STUB, "P1", kind="unit")
    assert e.delta > 0 and e.passed is True and e.pert_decision == "INSUFFICIENT"

def test_bad_predictor_fails_p3():
    e = compute_ers(rec(), Credulous(), "P3", k=4)
    assert e.passed is False and abs(e.delta) > e.tolerance
    assert run_matrix([rec()], Credulous(), pids=["P3"])["counts"]["P3"]["fail"] == 1

def test_bad_predictor_fails_p2():
    assert compute_ers(rec(), Credulous(), "P2", k=4).passed is False

def test_na_cases():
    e = compute_ers(EvidenceRecord("e", "p"), STUB, "P1")
    assert e.passed is None and e.reason
    d = rec(); d.inputs.append(I("w", "CONFIRMED_DIFF", hits={"base": [10, 11], "variant": [10, 11]}))
    assert compute_ers(d, STUB, "P7").passed is None
    assert compute_ers(rec(env_consistent=False), STUB, "P9").passed is None

def test_p6_divergent_passes():
    e = compute_ers(rec(), STUB, "P6")
    assert e.pert_decision == "DIVERGENT_OBSERVABLE" and e.passed

def test_p8_requires_rejection():
    class Blind(Credulous):
        def decide(self, r): return ("NO_DIVERGENCE_OBSERVED", 0.0)
    assert compute_ers(rec(), Blind(), "P8").passed is False
    assert compute_ers(rec(), STUB, "P8").passed is True

def test_vector_and_matrix():
    v = ers_vector(rec(), STUB)
    assert set(v) == {f"ers_{p}_delta" for p in PERTURBATIONS}
    m = run_matrix([rec(), EvidenceRecord("e", "p")], STUB)
    assert all(sum(c.values()) == 2 for c in m["counts"].values()) and not m["failures"] and "| P1 |" in m["markdown"]

def test_deterministic_replay():
    a, b = compute_ers(rec(), STUB, "P5", seed=7), compute_ers(rec(), STUB, "P5", seed=7)
    assert a == b and a.perturbation["output_digest"] == b.perturbation["output_digest"]

def test_y_meta_immunity_no_mutation():
    a, b = rec(), rec(y=1, meta={"q": 1}); j = a.to_json()
    assert ers_vector(a, STUB) == ers_vector(b, STUB) and a.to_json() == j

def test_cli_register():
    import argparse
    p = argparse.ArgumentParser(); ers.cli_register(p.add_subparsers())
    assert p.parse_args(["ers", "x.jsonl"]).records == "x.jsonl" and p.parse_args(["perturb", "x.jsonl", "P3"]).pid == "P3"
