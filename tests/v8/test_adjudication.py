import json, pytest
from sbgv8 import adjudication as A

BOUND = {"channels": ["outcome"]}; BUD = {"generators": 3, "time_cap_s": 10}
def clk():
    n = iter(range(1, 10000)); return lambda: f"2000-01-01T00:00:{next(n):05d}"   # synthetic fixture clock

def wf(tmp_path, n=1):
    w = A.Workflow(str(tmp_path / "log.jsonl"), clock=clk())
    for i in range(n): w.register_case(A.AdjudicationCase(f"c{i}", BOUND, BUD, ("diff",)))
    return w

@pytest.mark.parametrize("key", ["model_score", "ers_P1_delta", "baseline_pred", "v7b_verdict", "risk", "predicted", "Verdict"])
def test_blinding_rejects_forbidden_keys(key):
    with pytest.raises(A.BlindingViolation): A.AdjudicationCase.from_dict({"pair_id": "x", "observation_boundary": {}, "budget": {}, key: 1})
    with pytest.raises(A.BlindingViolation): A.AdjudicationCase("x", {"nested": {key: 1}}, {})
    with pytest.raises(A.BlindingViolation): A.AdjudicationCase("x", {}, {"l": [{key: 1}]})

def test_allowed_keys_not_false_positive():
    A.AdjudicationCase("x", {"observers": 1, "users": 2}, {"generators": 5, "seeds": [1]})

def test_case_has_no_score_fields():
    import dataclasses
    assert {f.name for f in dataclasses.fields(A.AdjudicationCase)} == {"pair_id", "observation_boundary", "budget", "evidence_reviewed"}

def test_budget_freeze(tmp_path):
    w = wf(tmp_path); w.set_budget("c0", {"generators": 4})
    assert w.cases["c0"].budget == {"generators": 4}
    w.record_decision("c0", "adjA", A.CONFIRMED, "found x")
    with pytest.raises(A.BudgetFrozen): w.set_budget("c0", {"generators": 9})
    with pytest.raises(Exception): w.cases["c0"].budget_hash = 1       # frozen dataclass

def test_decision_rules_and_third_adjudicator(tmp_path):
    w = wf(tmp_path)
    with pytest.raises(ValueError): w.record_decision("c0", "a", A.CONFIRMED, " ")
    with pytest.raises(ValueError): w.record_decision("c0", "a", "maybe", "r")
    w.record_decision("c0", "a", A.CONFIRMED, "r1")
    assert w.final_outcome("c0") == (A.UNRESOLVED, "pending_primaries")
    with pytest.raises(ValueError): w.record_decision("c0", "a", A.CONFIRMED, "dup")
    with pytest.raises(ValueError): w.record_decision("c0", "t", A.CONFIRMED, "r", role="third")
    w.record_decision("c0", "b", A.NONE_FOUND, "r2")
    assert w.final_outcome("c0") == (A.UNRESOLVED, "pending_third")
    w.record_decision("c0", "t", A.NONE_FOUND, "r3", role="third")
    assert w.final_outcome("c0") == (A.NONE_FOUND, "third_resolved")
    assert all(d["budget_hash"] == w.cases["c0"].budget_hash() and d["decided_at"] for d in w.decisions["c0"])

def test_audit_chain_and_replay_and_tamper(tmp_path):
    w = wf(tmp_path); w.record_decision("c0", "a", A.CONFIRMED, "r"); w.record_decision("c0", "b", A.CONFIRMED, "r")
    assert A.verify_chain(w.path) == (True, "3 events")
    w2 = A.Workflow(w.path); assert w2.final_outcome("c0") == (A.CONFIRMED, "agreed")
    lines = open(w.path).read().splitlines(); e = json.loads(lines[1]); e["payload"]["outcome"] = A.NONE_FOUND
    lines[1] = json.dumps(e, sort_keys=True); open(w.path, "w").write("\n".join(lines) + "\n")
    assert not A.verify_chain(w.path)[0]
    with pytest.raises(ValueError): A.Workflow(w.path)

def test_kappa_hand_computed():
    # 50 pairs: both confirmed 20, both none 15, A=conf/B=none 5, A=none/B=conf 10.
    a = [A.CONFIRMED] * 20 + [A.NONE_FOUND] * 15 + [A.CONFIRMED] * 5 + [A.NONE_FOUND] * 10
    b = [A.CONFIRMED] * 20 + [A.NONE_FOUND] * 15 + [A.NONE_FOUND] * 5 + [A.CONFIRMED] * 10
    k = A.cohen_kappa(a, b)   # po=.7 ; pA(conf)=.5,pB(conf)=.6 -> pe=.5*.6+.5*.4=.5 ; kappa=.4
    assert k["po"] == pytest.approx(.7) and k["pe"] == pytest.approx(.5) and k["kappa"] == pytest.approx(.4)
    m = A.confusion_matrix(a, b)
    assert m[A.CONFIRMED][A.CONFIRMED] == 20 and m[A.CONFIRMED][A.NONE_FOUND] == 5 and m[A.NONE_FOUND][A.CONFIRMED] == 10
    p = [A.CONFIRMED, A.NONE_FOUND] * 5
    assert A.cohen_kappa(p, p)["kappa"] == pytest.approx(1.0)
    assert A.cohen_kappa(p, [A.NONE_FOUND, A.CONFIRMED] * 5)["kappa"] == pytest.approx(-1.0)

def test_kappa_degenerate_marginals():
    c = [A.CONFIRMED] * 6
    k = A.cohen_kappa(c, c); assert k["kappa"] is None and k["po"] == 1.0 and "degenerate" in k["note"]
    assert A.cohen_kappa([], [])["kappa"] is None
    assert A.cohen_kappa(c, [A.NONE_FOUND] * 6)["kappa"] == pytest.approx(0.0)   # po=0, pe=0 -> 0, not undefined

def test_agreement_report(tmp_path):
    w = wf(tmp_path, 4)
    for i, (x, y) in enumerate([(A.CONFIRMED, A.CONFIRMED), (A.NONE_FOUND, A.NONE_FOUND), (A.CONFIRMED, A.NONE_FOUND)]):
        w.record_decision(f"c{i}", "a", x, "r"); w.record_decision(f"c{i}", "b", y, "r")
    w.record_decision("c2", "t", A.UNRESOLVED, "r", role="third")
    r = A.agreement_report(w)
    assert (r["n_cases"], r["n_double_labelled"], r["n_disagreements"], r["n_third_resolved"], r["n_pending"], r["n_final_unresolved"]) == (4, 3, 1, 1, 1, 2)
    assert r["double_labelled_fraction"] == .75 and r["meets_double_coverage"]

def test_unresolved_variants_and_estimands():
    assert [A.y_from_adjudication(o) for o in A.OUTCOMES] == [1, 0, None]
    assert A.y_from_adjudication(A.UNRESOLVED, "worst_case_divergence") == 1 and A.y_from_adjudication(A.UNRESOLVED, "non_divergence") == 0
    with pytest.raises(ValueError): A.y_from_adjudication(A.UNRESOLVED, "bogus")
    with pytest.raises(ValueError): A.y_from_adjudication("junk")
    out = {"a": A.CONFIRMED, "b": A.NONE_FOUND, "c": A.UNRESOLVED, "d": A.NONE_FOUND}
    v = A.estimand_variants(out, issued={"a", "c", "d"})
    assert v["drop"]["risk"] == .5 and v["drop"]["n_issued"] == 2 and "c" not in v["drop"]["y"]
    assert v["worst_case_divergence"]["risk"] == pytest.approx(2 / 3)
    assert v["non_divergence"]["risk"] == pytest.approx(1 / 3) and v["drop"]["n_unresolved"] == 1
    assert A.estimand_variants(out, issued=set())["drop"]["risk"] is None

def test_determinism_of_variants():
    out = {"b": A.UNRESOLVED, "a": A.CONFIRMED}
    assert json.dumps(A.estimand_variants(out), sort_keys=True) == json.dumps(A.estimand_variants(dict(reversed(list(out.items())))), sort_keys=True)
