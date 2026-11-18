"""Executed validation of the ERS properties (duplicates, irrelevant evidence, integrity, observation loss, divergence responsiveness) and of P1b.
Recorded-evidence (class a) checks; the trust tests corrupt COPIES of real evidence directories (needs results/repro/v8_dev_20261118_195446)."""
import copy, json, os, shutil
import numpy as np
import pytest
from sbgv8 import calibrate, ers, perturb, schema
from sbgv8.adapter import load_record
from sbgv8.ers import ActivationStubPredictor, compute_ers
from sbgv8.profile import build_profile
from sbgv8.schema import EvidenceRecord, InputEvidence as I, PERTURBATIONS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "datasets/v8/dev_records.jsonl")
needs_data = pytest.mark.skipif(not os.path.exists(DATA), reason="dev_records.jsonl missing")
STUB = ActivationStubPredictor()


def inp(i, hits, **kw):
    return I(i, "SAME", obs_fingerprint=f"f{i}", channels_present=["outcome", "exception"], n_repeat_runs=4, hits={"base": hits, "variant": hits}, **kw)

def rec(**kw):
    return EvidenceRecord("p", "proj", changed_units={"base": [10, 11], "variant": [10, 11]}, inputs=[inp("a", [10, 11, 5]), inp("b", [11, 5]), inp("c", [5])], **kw)

def witness(r):
    r = copy.deepcopy(r); r.inputs.append(I("w", "CONFIRMED_DIFF", obs_fingerprint="w", channels_present=["outcome"], hits={"base": [10, 11], "variant": [10, 11]})); return r

def all_feature_model(recs):
    """Unfitted calibrate.Model that READS every feature with its declared sign, so invariance checks are not vacuous (fitted models keep only mu_min)."""
    names = list(schema.FEATURES); X = calibrate._design(recs, names, None, None)
    return calibrate.Model(names, [], [0.4 * (calibrate.RISK_SIGN[n] or 1) for n in names], 0.0, X.mean(0), np.where(X.std(0) < 1e-12, 1.0, X.std(0)), 0.0, tau=0.9)

def devrecs():
    return [EvidenceRecord.from_json(l) for l in open(DATA) if l.strip()]


class Credulous:   # counts raw inputs
    def predict_risk(self, r): return 1.0 / (1 + len(r.inputs))
    def decide(self, r): return ("NO_DIVERGENCE_OBSERVED", self.predict_risk(r))

class ChannelCredulous(Credulous):   # more observed channels => HIGHER risk (wrong direction): masking lowers risk
    def predict_risk(self, r): return sum(len(i.channels_present) for i in r.inputs) / (4.0 * max(1, len(r.inputs)))

class WitnessBlind(Credulous):
    def decide(self, r): return ("NO_DIVERGENCE_OBSERVED", 0.0)


# ---- duplicates ----
def test_duplicate_counting_predictor_detected_failing_p3():
    assert compute_ers(rec(), Credulous(), "P3", k=4).passed is False

def test_real_model_invariant_to_flagged_duplicates():
    R = [rec(), witness(rec())]
    m = all_feature_model(R + [rec(env_consistent=False)])
    for r in R[:1]:
        for k in (1, 3, 8):
            e = compute_ers(r, m, "P3", k=k)
            assert e.passed and e.delta == 0.0 and build_profile(perturb.apply(r, "P3", k=k)[0]) == build_profile(r)

@needs_data
def test_fitted_model_and_stub_unchanged_by_duplicates_on_dev_records():
    R = devrecs(); m = calibrate.fit(R, schema.FEATURE_SETS["full_profile"])
    for r in R[::6]:
        for P in (m, STUB):
            e = compute_ers(r, P, "P3", k=4)
            assert e.passed is not False and e.delta == 0.0

def test_unflagged_duplicates_do_not_raise_confidence():
    r = rec(); m = all_feature_model([r]); r2 = copy.deepcopy(r)
    for i in list(r.inputs):
        c = copy.deepcopy(i); c.input_id += "#u"; r2.inputs.append(c)
    assert m.predict_risk(r2) >= m.predict_risk(r) - 0.02


# ---- irrelevant evidence ----
def test_credulous_predictor_detected_failing_p2():
    assert compute_ers(rec(), Credulous(), "P2", k=4).passed is False

@needs_data
def test_fitted_model_irrelevant_evidence_cannot_improve_risk():
    R = devrecs(); m = calibrate.fit(R, schema.FEATURE_SETS["full_profile"]); worst = 0.0
    for r in R:
        e = compute_ers(r, m, "P2", k=4)
        if e.applicable: worst = min(worst, e.delta)
    assert worst >= -0.02

def test_all_feature_model_irrelevant_evidence_cannot_improve_risk():
    e = compute_ers(rec(), all_feature_model([rec()]), "P2", k=4)
    assert e.delta >= -0.02


# ---- integrity: decision level ----
def test_integrity_violation_never_leaves_authoritative_verdict():
    for r in (rec(), witness(rec())):
        for P in (STUB, calibrate.fit([rec(y=0)], schema.FEATURE_SETS["full_profile"], tau=1.0)):
            e = compute_ers(r, P, "P8")
            assert e.passed is True and e.pert_decision == "INSUFFICIENT"
    assert compute_ers(rec(), WitnessBlind(), "P8").passed is False

def test_v7b_replica_keeps_witness_over_tamper_flag_known_behaviour():
    from sbgv8.profile import v7b_style_decision
    r = witness(rec()); r.integrity_ok = False
    assert v7b_style_decision(r)[0] == "DIVERGENT_OBSERVABLE"      # faithful to V7-B; V8 policy gate is in Model.decide / the stub


# ---- integrity: trust.check on corrupted evidence directories ----
SRC = os.path.join(ROOT, "results/repro/v8_dev_20261118_195446")

def _pick(verdict):
    for r in devrecs():
        d = os.path.join(ROOT, r.meta.get("src_dir", "-"))
        if r.v7b_verdict == verdict and r.meta.get("sidecar") == "ok" and os.path.isdir(d) and r.integrity_ok: return d
    pytest.skip("no recorded evidence directory")

def _flip_verdict(d):
    p = os.path.join(d, "evidence.jsonl"); s = open(p).read()
    a, b = ('"value":"DIVERGENT_OBSERVABLE"', '"value":"NO_DIVERGENCE_OBSERVED"') if '"value":"DIVERGENT_OBSERVABLE"' in s else ('"value":"NO_DIVERGENCE_OBSERVED"', '"value":"DIVERGENT_OBSERVABLE"')
    assert a in s; open(p, "w").write(s.replace(a, b, 1))

def _truncate(d):
    p = os.path.join(d, "evidence.jsonl"); L = open(p).read().splitlines(); open(p, "w").write("\n".join(L[:-1]) + "\n")

def _sidecar(d):
    p = os.path.join(d, "v8_parts.json"); j = json.load(open(p)); j["parts"][0]["hits"]["variant"] = [999999]; json.dump(j, open(p, "w"))

def _verdict_json(d):
    p = os.path.join(d, "verdict.json"); j = json.load(open(p)); j["log_head"] = "deadbeef"; json.dump(j, open(p, "w"))

@pytest.mark.parametrize("corrupt", [_flip_verdict, _truncate, _sidecar, _verdict_json])
@pytest.mark.parametrize("verdict", ["DIVERGENT_OBSERVABLE", "NO_DIVERGENCE_OBSERVED"])
def test_trust_check_rejects_corrupted_evidence_and_no_authoritative_verdict(tmp_path, corrupt, verdict):
    from sbgv8 import trust
    d = tmp_path / "ev"; shutil.copytree(_pick(verdict), d); d = str(d)
    base = set(trust.check(d).issues)                         # control (pre-capture-record evidence may carry a standing issue; only NEW issues count)
    corrupt(d)
    new = set(trust.check(d).issues) - base            # must report, never raise (truncated log: fixed, see test_truncated_log_*)
    assert new, "corruption not reported by trust.check"
    try: r = load_record(d)
    except Exception: return                                  # unreadable evidence yields no record, hence no verdict
    assert r.integrity_ok is False
    m = calibrate.fit([rec(y=0)], schema.FEATURE_SETS["full_profile"], tau=1.0)
    assert m.decide(r)[0] == "INSUFFICIENT" and STUB.decide(r)[0] == "INSUFFICIENT"


# ---- observation loss, divergence responsiveness ----
def test_observation_loss_cannot_lower_risk():
    r = rec(); assert compute_ers(r, ChannelCredulous(), "P4", channels=["outcome"]).passed is False
    for P in (STUB, all_feature_model([r])): assert compute_ers(r, P, "P4", channels=["outcome"]).delta >= -ers.EPS

@needs_data
def test_observation_loss_monotone_on_dev_records():
    R = devrecs(); m = all_feature_model(R)
    for r in R[::5]:
        for P in (STUB, m, calibrate.fit(R[:60], schema.FEATURE_SETS["full_profile"])):
            assert compute_ers(r, P, "P4").passed is not False

def test_divergence_responsiveness_p6():
    e = compute_ers(rec(), STUB, "P6"); assert e.pert_decision == "DIVERGENT_OBSERVABLE" and e.passed
    class Flat(Credulous):
        def predict_risk(self, r): return 0.3
    assert compute_ers(rec(), Flat(), "P6").passed is False   # NDO stays NDO, risk flat: unresponsive

def test_p6_na_when_already_divergent():
    assert compute_ers(witness(rec()), STUB, "P6").passed is None


# ---- P1b ----
def test_p1b_deletes_least_multiplicity_unit_and_preserves_p1():
    r = rec(); r2, pr = perturb.apply(r, "P1b")
    assert pr.applicable and pr.params["target"] == ["unit", ["base", 10]] and pr.params["deleted"] == ["a"] and pr.params["multiplicity"] == 1
    assert [i.input_id for i in r2.inputs] == ["b", "c"] and build_profile(r2)["act_frac"] < build_profile(r)["act_frac"]
    assert perturb.apply(r, "P1", kind="unit")[1].params["deleted"] == ["a"]          # P1 untouched
    assert tuple(perturb.PERTURBATION_MATRIX) == PERTURBATIONS and "P1b" not in perturb.PERTURBATION_MATRIX

def test_p1b_determinism_no_mutation_y_meta_immunity():
    a, b = rec(y=0, meta={"m": 1}), rec(y=1, meta={"z": 2}); j = a.to_json()
    assert perturb.apply(a, "P1b", seed=1)[1].output_digest == perturb.apply(b, "P1b", seed=1)[1].output_digest and a.to_json() == j

def test_p1b_na_when_deletion_is_total_or_nothing_covered():
    r = rec(); r.inputs = [inp("a", [10, 11]), inp("b", [10, 11])]      # every clean input covers every unit: deletion would be total
    assert not perturb.apply(r, "P1b")[1].applicable
    r.inputs = [inp("a", [5])]; assert not perturb.apply(r, "P1b")[1].applicable
    assert not perturb.apply(EvidenceRecord("e", "p"), "P1b")[1].applicable

def test_p1b_ers_stub_passes_and_credulous_fails():
    assert compute_ers(rec(), STUB, "P1b").passed is True
    class Up(Credulous):
        def predict_risk(self, r): return 0.1 * len(r.inputs)     # risk falls when inputs are deleted
    assert compute_ers(rec(), Up(), "P1b").passed is False

def test_evidence_class_declared_for_all():
    for p in PERTURBATIONS: assert perturb.PERTURBATION_MATRIX[p]["evidence_class"]["posthoc"].startswith("a")
    assert perturb.PERTURBATION_VARIANTS["P1b"]["evidence_class"]["posthoc"] == "a"


# ---- truncated / partial logs: safe validation failure, not a crash ----
@pytest.mark.parametrize("keep", [0, 1, 2])
def test_truncated_log_gives_safe_failure_not_crash(tmp_path, keep):
    from sbgv8 import trust
    d = tmp_path / "ev"; shutil.copytree(_pick("NO_DIVERGENCE_OBSERVED"), d); p = d / "evidence.jsonl"
    L = p.read_text().splitlines(); p.write_text("\n".join(L[:keep]) + ("\n" if keep else ""))
    rep = trust.check(str(d))                              # must not raise
    assert rep.issues and rep.inference.get("effective_verdict", "INSUFFICIENT") == "INSUFFICIENT"
    assert not rep.inference.get("recomputable", False)
    with pytest.raises((ValueError, OSError, KeyError)):   # no record, hence no verdict, can be built from it
        load_record(str(d))


# ---- profile: irrelevant evidence and copies cannot move any feature (defect fixed 2026-11-18) ----
def test_irrelevant_and_unflagged_copies_leave_profile_unchanged():
    from sbgv8.profile import build_profile
    r = rec(); base = build_profile(r); r2 = copy.deepcopy(r)
    for i in list(r.inputs):                                # unflagged exact copies
        c = copy.deepcopy(i); c.input_id += "#u"; r2.inputs.append(c)
    r2.inputs.append(I("irr", "SAME", obs_fingerprint="irr", channels_present=["outcome"], hits={"base": [5], "variant": [5]}))   # reaches no changed unit
    assert build_profile(r2) == base

def test_distinct_relevant_evidence_still_raises_confidence():
    from sbgv8.profile import build_profile
    r = rec(); r2 = copy.deepcopy(r)
    r2.inputs.append(I("new", "SAME", obs_fingerprint="new", channels_present=["outcome"], hits={"base": [10, 11], "variant": [10, 11]}))
    assert build_profile(r2)["n_eff"] == build_profile(r)["n_eff"] + 1 and build_profile(r2)["mu_min"] > build_profile(r)["mu_min"]

def test_no_located_change_means_no_relevant_evidence():
    from sbgv8.profile import build_profile
    r = EvidenceRecord("p", "proj", changed_units={"base": [], "variant": []}, inputs=[inp("a", [4, 5])]); base = build_profile(r)
    r2 = copy.deepcopy(r)
    for k in range(4): r2.inputs.append(I(f"x{k}", "SAME", obs_fingerprint=f"x{k}", channels_present=["outcome"], hits={"base": [7], "variant": [7]}))
    assert build_profile(r2) == base and base["n_same"] == 0.0

@needs_data
def test_all_feature_model_irrelevant_evidence_never_improves_risk_on_any_dev_record():
    R = devrecs(); m = all_feature_model(R); worst = 0.0
    for r in R:
        e = compute_ers(r, m, "P2", k=4)
        if e.applicable: worst = min(worst, e.delta)
    assert worst >= -1e-9, worst            # exact: irrelevant inputs must not move the profile at all
