"""Offline tests for experiments/v8/run_real_exec_perturbations.py (no engine runs): candidate derivation, selection declaration, judging, and the
stored real-execution manifest (skipped when results/v8_mac_perturb is absent)."""
import json, os
import pytest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
X = pytest.importorskip("experiments.v8.run_real_exec_perturbations")
from sbgv8.ers import ActivationStubPredictor
from sbgv8.schema import EvidenceRecord, InputEvidence as I

def inp(i, hits, **kw): return I(i, "SAME", obs_fingerprint=f"f{i}", channels_present=["outcome"], n_repeat_runs=4, hits={"base": hits, "variant": hits}, **kw)
def rec(): return EvidenceRecord("p", "proj", changed_units={"base": [10], "variant": [10]}, inputs=[inp("a", [10, 5]), inp("b", [5])])

def test_candidates_deterministic_distinct_output_blind():
    orig = [{"id": "i0", "args": [[3, 1, 2], "ab", 4]}, {"id": "i1", "args": [[], "", 0]}]
    a, b = X.candidates(orig, "x:y"), X.candidates(orig, "x:y")
    assert a == b and 0 < len(a) <= X.MAX_CAND and X.candidates(orig, "x:z") != a
    keys = [json.dumps(c["args"]) for c in a]; assert len(set(keys)) == len(keys) and not {json.dumps(i["args"]) for i in orig} & set(keys)
    assert all(set(c) == {"id", "args"} for c in a)           # no verdict/label/output information carried

def test_judge_p2_unchanged_passes_and_p5_budget_rule():
    P = ActivationStubPredictor(); r0 = rec(); extra = rec(); extra.inputs.append(inp("c", [5]))
    assert X.judge("P2", r0, extra, P)[0] is True
    weak = rec(); weak.inputs = [inp("b", [5])]                # less reproducibility/coverage evidence: risk up -> pass
    assert X.judge("P5_low", r0, weak, P)[0] is True
    assert X.judge("P5_low", weak, r0, P)[0] is False          # risk went DOWN with lower budget and no abstention -> fail

def test_judge_p6_requires_response():
    P = ActivationStubPredictor(); w = rec(); w.inputs.append(I("c0", "CONFIRMED_DIFF", obs_fingerprint="d", channels_present=["outcome"], hits={"base": [10], "variant": [10]}))
    assert X.judge("P6", rec(), w, P)[0] is True and X.judge("P6", rec(), rec(), P)[0] is False

def test_selection_declared_before_run_and_consistent():
    sel = os.path.join(ROOT, "results/v8_mac_perturb/realexec_selection.json")
    if not os.path.exists(sel): pytest.skip("no selection file")
    s = json.load(open(sel)); assert s["declared_before_running"] and s["seed"] == X.SEED and len(s["selected"]) <= 30 and "SELECTION" not in s["rule"][:5]
    assert s["records_sha256"] == X.sha(X.DATA)
    man = os.path.join(X.RUN, "manifest.json")
    if os.path.exists(man):
        m = json.load(open(man)); assert [o["pair"] for o in m["pairs"]] == s["selected"] and m["workers"] == 2 and m["git_head"] and m["seed"] == X.SEED
        for o in m["pairs"]:                                   # P2 inputs were verified (from recorded hit sets) to touch no changed unit
            r = o["records"].get("p2")
            if r:
                r = EvidenceRecord.from_json(r); U = X.uset(r)
                assert all(not (X.hset(i) & U) for i in r.inputs if i.input_id in o["p2_inputs"])
