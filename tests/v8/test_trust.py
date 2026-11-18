import json, os, shutil, pytest
from sbgv7 import records as R
from sbgv8 import trust, collect
from .test_collect import CFG, write


@pytest.fixture(scope="module")
def honest(tmp_path_factory):
    t = tmp_path_factory.mktemp("t"); b, v = write(t / "s", v="def f(x):\n    return x + 5\n")
    collect.compare(b, v, "f", [{"id": "a", "args": [1]}], CFG, str(t / "ev"))
    return t / "ev", b, v


def cp(src, tmp_path):
    d = tmp_path / "c"; shutil.copytree(src, d); return d


def test_honest_report_separates_questions(honest):
    rep = trust.check(str(honest[0]))
    assert rep.integrity["chain"] == "ok" and rep.integrity["verify"] == "verified" and rep.integrity["sidecar"] == "ok" and not rep.issues
    assert any("harness" in x for x in rep.authenticity["not_established"]) and rep.authenticity["shadow"] == "not run"
    assert rep.isolation["validated_on_linux"] is False and "sandbox-exec" in rep.isolation["mechanism"]
    assert rep.inference["verdict"] == "DIVERGENT_OBSERVABLE" and rep.inference["recomputable"]


def test_shadow_match_and_mismatch(honest, tmp_path):
    assert trust.check(str(honest[0]), shadow=True).authenticity["shadow"]["status"] == "match"
    d = cp(honest[0], tmp_path); s = open(d / "evidence.jsonl").read()
    # re-chain after changing the recorded return value: chain and verify may pass later checks, the shadow must still disagree
    def f(recs):
        for r in recs:
            if r["kind"] == "Observation" and r["body"].get("ret") == ["int", "0x6"]: r["body"]["ret"] = ["int", "0x2"]
    R_head = trust._rewrite(str(d / "evidence.jsonl"), f)
    assert trust.check(str(d), shadow=True).authenticity["shadow"]["status"] == "mismatch"


def test_shadow_run_independent_of_harness(tmp_path):
    p = tmp_path / "p.py"; p.write_text("def g(x, y=1):\n    print('noise')\n    return {x: [y, (1.5, None)]}\n")
    out = trust.shadow_run(str(p), "g", [3], {"y": 2})
    assert out == {"t": "returned", "ret": ["dict", [[["int", "0x3"], ["list", [["int", "0x2"], ["tuple", [["float", "1.5"], ["none"]]]]]]]]}
    p.write_text("def g(x):\n    raise KeyError(x)\n")
    assert trust.shadow_run(str(p), "g", [1], {})["t"] == "raised"


def test_chain_break_and_missing_verdict_json_and_pins(honest, tmp_path):
    d = cp(honest[0], tmp_path)
    os.unlink(d / "verdict.json")
    assert any("verdict.json absent" in i for i in trust.check(str(d)).issues)
    assert trust.check(str(honest[0]), pinned_head="0" * 64).provenance["pinned_head"] is False
    head = trust.check(str(honest[0])).provenance["log_head"]
    r = trust.check(str(honest[0]), pinned_head=head, expected_sources={"base": honest[1], "variant": honest[2]})
    assert r.provenance["pinned_head"] and r.provenance["sources_match_expected"]
    lines = open(d / "evidence.jsonl").read().splitlines(); lines[3] = lines[3].replace("Run", "Rux", 1)
    open(d / "evidence.jsonl", "w").write("\n".join(lines) + "\n")
    assert trust.check(str(d)).integrity["chain"].startswith("broken")


def test_sidecar_states(honest, tmp_path):
    assert trust.check_sidecar(str(honest[0]))["status"] == "ok"
    d = cp(honest[0], tmp_path); os.unlink(d / "v8_parts.json")
    assert trust.check_sidecar(str(d))["status"] == "missing"


@pytest.fixture(scope="module")
def suite():
    return {r["attack"]: r for r in trust.forgery_suite()["results"]}


def test_forgery_suite_shape(suite):
    attacks = [k for k in suite if not k.startswith("H00")]
    assert len(attacks) >= 8 and suite["H00_honest_control"]["outcome"].startswith("NO EFFECT")
    assert all(r["outcome"].split()[0] in ("DETECTED", "BLOCKED", "NO", "SUCCEEDS") for r in suite.values())


def test_forgery_known_results(suite):
    det = lambda k: suite[k]["outcome"].startswith("DETECTED")
    assert det("A01_patch_canonicaliser_via___main__") and "shadow" in suite["A01_patch_canonicaliser_via___main__"]["outcome"]
    assert all(suite[k]["outcome"].startswith("BLOCKED") for k in ("A03_os__exit_before_result", "A05_close_result_fd"))
    assert suite["A04_write_garbage_to_result_fd"]["verdict"] != "NO_DIVERGENCE_OBSERVED"  # blocked or no effect, never a false clean
    assert det("P01_edit_observation_no_rechain") and det("P02_edit_verdict_and_rechain") and det("P03_drop_verdict_json") and det("P06_substitute_evidence_of_another_program")
    # documented OPEN issues must stay visible: if one starts being detected, the report must be updated
    assert suite["A08_hide_stdout_divergence_by_patching_Cap"]["outcome"].startswith("SUCCEEDS")
    assert suite["P04_edit_unverified_field_and_rechain"]["outcome"].startswith("SUCCEEDS")
