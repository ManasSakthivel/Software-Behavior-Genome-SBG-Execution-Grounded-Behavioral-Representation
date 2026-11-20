import pytest
from sbgv8.schema import EvidenceRecord, InputEvidence as I, FEATURES
from sbgv8.profile import build_profile, v7b_style_decision

def mk(inputs, units=None, **kw):
    cu = units or {"base": [10, 11], "variant": [10, 11]}
    return EvidenceRecord("p", "proj", inputs=inputs, changed_units=cu, **kw)

def inp(i, hits, fp=None, **kw):
    return I(i, kw.pop("outcome", "SAME"), obs_fingerprint=fp or f"f{i}", channels_present=["outcome"], n_repeat_runs=3,
             hits={"base": hits, "variant": hits}, **kw)

GOOD = lambda: mk([inp("a", [10, 11]), inp("b", [10]) ], y=0)

def test_keys_exact_and_values():
    p = build_profile(GOOD())
    assert list(p) == FEATURES
    assert p["act_frac"] == 1.0 and p["n_same"] == 2 and p["n_rep"] == 6 and p["mu_min"] == 1 and p["mu_mean"] == 1.5
    assert p["n_eff"] == 2 and p["prov_ok"] == 1 and p["chan_complete"] == 0.25

def test_boundaries():
    p = build_profile(mk([]))
    assert p["act_frac"] == 0 and p["n_same"] == 0 and p["repro_frac"] == 0
    assert build_profile(mk([inp("a", [10])]))["act_frac"] == 0.5          # single input
    assert build_profile(mk([inp("a", [10])], units={"base": [], "variant": []}))["act_frac"] == 1.0

def test_lossy_not_activating():
    r = mk([inp("a", [10, 11], lossy=True)])
    assert build_profile(r)["act_frac"] == 0 and build_profile(r)["lossy_frac"] == 1

def test_duplicates_counted_once():
    r = mk([inp("a", [10, 11]), inp("b", [10, 11], fp="fa", provenance="declared"), inp("c", [10, 11], fp="fa"),
            inp("d", [10, 11], duplicate_of="a")])
    r.inputs[0].obs_fingerprint = "fa"
    p = build_profile(r)
    assert p["mu_min"] == 1 and p["n_eff"] == 1 and p["n_eff_prov"] == 1 and p["n_same"] == 3

def test_label_derived_prov():
    r = GOOD(); r.inputs[0].provenance = "label_derived"
    p = build_profile(r)
    assert p["prov_ok"] == 0 and p["n_eff_prov"] == 1 and p["n_eff"] == 2

def test_metamorphic_deleting_cannot_raise_act_frac():
    r = GOOD(); a = build_profile(r)["act_frac"]
    r.inputs.pop(0)
    assert build_profile(r)["act_frac"] <= a

def test_masking_cannot_raise_chan_complete():
    r = GOOD(); c = build_profile(r)["chan_complete"]
    for i in r.inputs: i.channels_present = []
    assert build_profile(r)["chan_complete"] <= c

def test_branch_cov():
    r = mk([inp("a", [10, 11])], static_branches={"base": 1, "variant": 1})
    r.inputs[0].branches = {"base": {"k": [True, False]}, "variant": {"k": [True]}}
    assert build_profile(r)["branch_cov_min"] == 0.5

def test_immune_to_y_and_meta():
    r = GOOD(); a = build_profile(r), v7b_style_decision(r)
    r.y, r.meta = 1, {"x": 1}
    assert (build_profile(r), v7b_style_decision(r)) == a

def test_no_mutation():
    r = GOOD(); d = r.to_json(); build_profile(r); v7b_style_decision(r)
    assert r.to_json() == d

# ---- v7b_style_decision ----
def test_decision_cases():
    assert v7b_style_decision(GOOD()) == ("NO_DIVERGENCE_OBSERVED", "S2")
    assert v7b_style_decision(mk([inp("a", [10, 11])], static_branches={"base": 1, "variant": 1})) == ("NO_DIVERGENCE_OBSERVED", "S1")
    r = GOOD(); r.inputs.append(inp("w", [10], outcome="CONFIRMED_DIFF"))
    assert v7b_style_decision(r) == ("DIVERGENT_OBSERVABLE", None)
    assert v7b_style_decision(mk([inp("a", [10])]))[0] == "INSUFFICIENT"                  # unactivated unit
    assert v7b_style_decision(mk([]))[0] == "INSUFFICIENT"                                # no inputs
    assert v7b_style_decision(mk([inp("a", [10, 11], lossy=True)]))[0] == "INSUFFICIENT"  # lossy-only
    assert v7b_style_decision(mk([inp("a", [10, 11], degenerate=True)]))[0] == "INSUFFICIENT"
    assert v7b_style_decision(mk([inp("a", [10, 11], deterministic=False)]))[0] == "INSUFFICIENT"
    r = GOOD(); r.blockers = ["import_error"]; assert v7b_style_decision(r)[0] == "INSUFFICIENT"
    r = GOOD(); r.integrity_ok = False; assert v7b_style_decision(r)[0] == "INSUFFICIENT"
    r = GOOD(); r.env_consistent = False; assert v7b_style_decision(r)[0] == "INSUFFICIENT"

def test_decision_s2():
    r = mk([inp("a", [10, 11])], static_branches={"base": 1, "variant": 1})
    r.inputs[0].branches = {s: {"k": [True, False]} for s in ("base", "variant")}
    assert v7b_style_decision(r) == ("NO_DIVERGENCE_OBSERVED", "S2")
