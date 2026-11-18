import pytest
from sbgv8 import perturb
from sbgv8.schema import EvidenceRecord, InputEvidence as I, PERTURBATIONS
from sbgv8.profile import build_profile, v7b_style_decision

def inp(i, hits, **kw):
    return I(i, "SAME", obs_fingerprint=f"f{i}", channels_present=["outcome", "exception"], n_repeat_runs=4,
             hits={"base": hits, "variant": hits}, **kw)

def rec():
    return EvidenceRecord("p", "proj", y=0, meta={"m": 1}, changed_units={"base": [10, 11], "variant": [10, 11]},
                          inputs=[inp("a", [10, 11, 5]), inp("b", [11, 5]), inp("c", [5])])

def test_matrix_fields():
    need = {"id", "name", "purpose", "definition", "transformation", "execution", "post_hoc", "only_recorded_modified", "expected",
            "tolerance", "failure_condition", "confounds", "valid_for", "provenance_record"}
    assert tuple(perturb.PERTURBATION_MATRIX) == PERTURBATIONS
    for m in perturb.PERTURBATION_MATRIX.values(): assert need <= set(m) and m["valid_for"]

@pytest.mark.parametrize("pid", PERTURBATIONS)
def test_no_mutation_and_determinism(pid):
    r = rec(); before = r.to_json()
    r1, p1 = perturb.apply(r, pid, seed=3); r2, p2 = perturb.apply(r, pid, seed=3)
    assert r.to_json() == before and r1 is not r
    assert p1 == p2 and p1.output_digest == r2.digest() and p1.input_digest == r.digest() and p1.applicable

def test_y_meta_immunity():
    a, b = rec(), rec(); b.y, b.meta = 1, {"z": 2}
    for pid in PERTURBATIONS:
        assert perturb.apply(a, pid, seed=1)[1].output_digest == perturb.apply(b, pid, seed=1)[1].output_digest

def test_p1_deletes_sole_reacher_lowers_act():
    r = rec(); r2, pr = perturb.apply(r, "P1", seed=0, kind="unit")
    assert pr.params["deleted"] == ["a"] and build_profile(r2)["act_frac"] < build_profile(r)["act_frac"]

def test_p1_na():
    r = rec(); r.inputs = [inp("a", [10, 11]), inp("b", [10, 11])]
    _, pr = perturb.apply(r, "P1", kind="unit")
    assert not pr.applicable and pr.reason

def test_p2_p3_leave_activation_and_multiplicity():
    r = rec(); p0 = build_profile(r)
    for pid in ("P2", "P3"):
        p = build_profile(perturb.apply(r, pid)[0])
        for k in ("act_frac", "mu_min", "mu_mean", "obs_react", "branch_cov_min"): assert p[k] == p0[k], (pid, k)
    p3 = build_profile(perturb.apply(r, "P3")[0])
    assert p3 == p0   # full invariance under duplication

def test_p3_marks_duplicates():
    r2, _ = perturb.apply(rec(), "P3", k=3)
    d = [i for i in r2.inputs if i.duplicate_of]
    assert len(d) == 3 and all(i.obs_fingerprint == next(o for o in r2.inputs if o.input_id == i.duplicate_of).obs_fingerprint for i in d)

def test_p2_flags_execution_required():
    assert perturb.apply(rec(), "P2")[1].execution_required and perturb.PERTURBATION_MATRIX["P2"]["execution"]

def test_p4_mask_and_na():
    r = rec(); r2, pr = perturb.apply(r, "P4", channels=["outcome"])
    assert build_profile(r2)["chan_complete"] < build_profile(r)["chan_complete"]
    _, pr = perturb.apply(r, "P4", channels=["api"]); assert not pr.applicable

def test_p4_masks_witness():
    r = rec(); r.inputs.append(I("w", "CONFIRMED_DIFF", channels_present=["outcome"], hits={"base": [10, 11], "variant": [10, 11]}))
    assert v7b_style_decision(r)[0] == "DIVERGENT_OBSERVABLE"
    assert v7b_style_decision(perturb.apply(r, "P4", channels=["outcome"])[0])[0] != "DIVERGENT_OBSERVABLE"

def test_p5_p7_p8_p9_effects():
    r = rec()
    assert build_profile(perturb.apply(r, "P5", frac=1.0)[0])["repro_frac"] == 0
    assert build_profile(perturb.apply(r, "P7")[0])["prov_ok"] == 0
    assert build_profile(perturb.apply(r, "P7", mode="untrusted")[0])["prov_ok"] == 0
    assert build_profile(perturb.apply(r, "P8")[0])["integrity_ok"] == 0
    assert build_profile(perturb.apply(r, "P9")[0])["env_ok"] == 0
    assert not perturb.apply(perturb.apply(r, "P9")[0], "P9")[1].applicable

def test_p6_decision_from_decide():
    r2, _ = perturb.apply(rec(), "P6")
    assert v7b_style_decision(r2)[0] == "DIVERGENT_OBSERVABLE"

def test_boundary_empty():
    e = EvidenceRecord("e", "p")
    for pid in ("P1", "P3", "P4", "P5", "P7"): assert not perturb.apply(e, pid)[1].applicable
    assert not perturb.apply(e, "P2")[1].applicable
    for pid in ("P6", "P8", "P9"): perturb.apply(e, pid)
