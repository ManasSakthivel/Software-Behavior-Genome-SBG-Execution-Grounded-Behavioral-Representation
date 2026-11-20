"""Attack B (evidence schema + anchor) and the validator / decision roles. Mutations are applied to copies of one honest anchored run."""
import copy, json, os, shutil, sys, pytest
from sbgv7 import records as R
from sbgv8 import collect, trust, procsep, evidence_schema as ES
from sbgv8.adapter import load_record
from .test_collect import CFG, write

KEY = bytes(range(1, 33))


@pytest.fixture(scope="module")
def honest(tmp_path_factory):
    t = tmp_path_factory.mktemp("sch"); b, v = write(t / "s", v="def f(x):\n    return x + 5\n")
    collect.compare(b, v, "f", [{"id": "a", "args": [1]}, {"id": "b", "args": [2]}], CFG, str(t / "ev"), anchor_key=KEY)
    b2, v2 = write(t / "s2", b="def f(x):\n    return x * 2\n", v="def f(x):\n    return x * 3\n")
    collect.compare(b2, v2, "f", [{"id": "a", "args": [1]}], CFG, str(t / "ev2"), anchor_key=KEY)  # another run (replay source)
    return t


def cp(honest, tmp_path, src="ev"):
    d = tmp_path / "c"; shutil.copytree(honest / src, d); return d


def edit(d, name, fn, reanchor=False):
    p = d / name; j = json.load(open(p)); sess = json.load(open(d / "v8_capture.json"))["session"]; fn(j); json.dump(j, open(p, "w"), sort_keys=True)
    if reanchor: ES.write_anchor(str(d), KEY, sess)


def status(d, key=KEY): return ES.validate_dir(str(d), key)


def test_honest_everything_ok(honest):
    v = status(honest / "ev")
    assert v["trusted"] is True and v["capture"]["status"] == "ok" and v["anchor"]["status"] == "ok" and v["sidecar"]["status"] == "ok" and not v["reasons"]
    rec = load_record(str(honest / "ev"), anchor_key=KEY)
    assert rec.integrity_ok and rec.meta["anchor"] == "ok" and rec.meta["capture"] == "ok" and not rec.meta["untrusted"]
    assert not trust.check(str(honest / "ev"), anchor_key=KEY).issues


# ---------------- capture schema: version / missing / extra / duplicate / reordered / partial
@pytest.mark.parametrize("name,fn", [
    ("bad_version", lambda c: c.update(schema="v8.capture.2")),
    ("missing_field", lambda c: c.pop("session")),
    ("extra_field", lambda c: c.update(sneaky=1)),
    ("extra_run_field", lambda c: c["runs"][0].update(sneaky=1)),
    ("wrong_type_bool_as_int", lambda c: c["runs"][0]["tee"].update(open=1)),
    ("wrong_type_int_as_float", lambda c: c["runs"][0].update(seq=0.0)),
    ("bad_hex", lambda c: c.update(session="zz" * 16)),
    ("negative_count", lambda c: c["runs"][0]["fd1"].update(len=-1)),
    ("modified_run_id_nonce_dup", lambda c: c["runs"][1].update(nonce=c["runs"][0]["nonce"])),
    ("duplicate_run_record", lambda c: c["runs"].append(copy.deepcopy(c["runs"][-1]))),
    ("reordered_runs", lambda c: c["runs"].reverse()),
    ("partial_drop_last_run", lambda c: c["runs"].pop()),
    ("partial_drop_all_runs", lambda c: c.update(runs=[])),
    ("modified_config", lambda c: c.update(config_sha256="0" * 64)),
    ("modified_provenance_harness", lambda c: c.update(harness_sha256="1" * 64)),
    ("modified_status", lambda c: c["runs"][2].update(status="TIMEOUT")),
    ("modified_timing", lambda c: c["runs"][2].update(cpu_s=0.0)),
    ("modified_input_hash", lambda c: c["runs"][2].update(input_hash="2" * 64)),
    ("modified_side", lambda c: c["runs"][2].update(side="base" if c["runs"][2]["side"] == "variant" else "variant")),
    ("modified_harness_stdout_digest", lambda c: c["runs"][2]["harness"].update(stdout_sha256="3" * 64)),
    ("lying_trusted_flag", lambda c: c["runs"][2].update(verdict="mismatch")),
    ("modified_log_head", lambda c: c.update(log_head="4" * 64)),
])
def test_capture_mutations_are_invalid_even_when_reanchored(honest, tmp_path, name, fn):
    d = cp(honest, tmp_path); edit(d, "v8_capture.json", fn, reanchor=True)  # attacker holds the key here: the SCHEMA/binding checks alone must catch it
    v = status(d)
    assert v["capture"]["status"] in ("invalid", "untrusted") and v["trusted"] is False and not load_record(str(d), anchor_key=KEY).integrity_ok, name


def test_capture_unreadable_missing_and_replayed(honest, tmp_path):
    d = cp(honest, tmp_path); (d / "v8_capture.json").write_text('{"schema": "v8.capture.1", "ru')  # partial file
    assert status(d)["capture"]["status"] == "invalid"
    os.unlink(d / "v8_capture.json")
    assert status(d)["capture"]["status"] == "missing" and status(d)["trusted"] is False  # V8 sidecar without its independent record
    shutil.copy(honest / "ev2/v8_capture.json", d / "v8_capture.json")  # capture of ANOTHER run (replay)
    v = status(d)
    assert v["capture"]["status"] == "invalid" and "not bound to this evidence log" in v["capture"]["detail"]


def test_legacy_v7b_dir_is_not_collected_not_untrusted(honest, tmp_path):
    d = cp(honest, tmp_path)
    for n in ("v8_capture.json", "v8_parts.json", "v8_anchor.json"): os.unlink(d / n)
    v = ES.validate_dir(str(d))
    assert v["capture"]["status"] == "not_collected" and v["trusted"] is None
    rec = load_record(str(d)); assert rec.integrity_ok and rec.meta["capture"] == "not_collected" and rec.meta["no_hits"]


# ---------------- sidecar schema
@pytest.mark.parametrize("name,fn", [
    ("bad_version", lambda s: s.update(schema="v8.parts.2")),
    ("missing_part_field", lambda s: s["parts"][0].pop("hits")),
    ("extra_part_field", lambda s: s["parts"][0].update(x=1)),
    ("extra_top_field", lambda s: s.update(x=1)),
    ("duplicate_input", lambda s: s["parts"].append(copy.deepcopy(s["parts"][0]))),
    ("hits_wrong_type", lambda s: s["parts"][0]["hits"].update(base="1,2")),
    ("lossy_as_int", lambda s: s["parts"][0].update(lossy=0)),
    ("parts_not_list", lambda s: s.update(parts=5)),
    ("partial_one_part_dropped", lambda s: s["parts"].pop()),
    ("reordered_parts_values_changed", lambda s: s["parts"][0].update(outcome="SAME")),
])
def test_sidecar_strict_schema(honest, tmp_path, name, fn):
    d = cp(honest, tmp_path); edit(d, "v8_parts.json", fn)
    assert trust.check_sidecar(str(d))["status"] == "inconsistent" and not load_record(str(d)).integrity_ok, name


# ---------------- anchor: what it proves and what it does not
def test_anchor_detects_P04_but_only_with_the_key(honest, tmp_path):
    d = cp(honest, tmp_path)
    def f(recs):
        for r in recs:
            if r["kind"] == "Run": r["meta"]["cpu_s"] = 0.0; r["meta"]["wall_s"] = 0.0
    head = trust._rewrite(str(d / "evidence.jsonl"), f)
    edit(d, "verdict.json", lambda j: j.update(log_head=head))
    sc = lambda s: s.update(log_head=head, evidence_sha256=ES.sha_file(str(d / "evidence.jsonl"))); edit(d, "v8_parts.json", sc)  # attacker re-binds sidecar (the old P04)
    rep = trust.check(str(d), anchor_key=KEY)
    assert rep.integrity["anchor"] == "invalid" and rep.integrity["capture"] == "invalid" and rep.issues
    rep = trust.check(str(d))  # no key supplied: the anchor is present but NOT verified; the capture binding still notices
    assert rep.integrity["anchor"] == "unverified_no_key" and rep.integrity["capture"] == "invalid"


def test_anchor_alone_when_every_other_file_is_made_consistent(honest, tmp_path):
    """Writer WITHOUT the key who recomputes log+sidecar+capture: only the MAC remains."""
    d = cp(honest, tmp_path)
    def f(recs):
        for r in recs:
            if r["kind"] == "Run": r["meta"]["cpu_s"] = 0.0; r["meta"]["wall_s"] = 0.0
    head = trust._rewrite(str(d / "evidence.jsonl"), f); sha = ES.sha_file(str(d / "evidence.jsonl"))
    edit(d, "verdict.json", lambda j: j.update(log_head=head)); edit(d, "v8_parts.json", lambda s: s.update(log_head=head, evidence_sha256=sha))
    def cap(c):
        c.update(log_head=head, evidence_sha256=sha)
        for x in c["runs"]: x["cpu_s"] = x["wall_s"] = 0.0
    edit(d, "v8_capture.json", cap)
    assert status(d)["capture"]["status"] == "ok" and status(d)["sidecar"]["status"] == "ok"  # everything else is consistent...
    assert status(d)["anchor"]["status"] == "invalid" and status(d)["trusted"] is False  # ...and the MAC is what notices
    assert trust.check(str(d)).integrity["anchor"] == "unverified_no_key"  # without the key nothing notices: do not claim detection then


def test_anchor_boundary_writer_with_key_is_undetected_without_pinned_head(honest, tmp_path):
    d = cp(honest, tmp_path); pinned = trust.check(str(honest / "ev"), anchor_key=KEY).provenance["log_head"]
    def f(recs):
        for r in recs:
            if r["kind"] == "Run": r["meta"]["cpu_s"] = 0.0
    head = trust._rewrite(str(d / "evidence.jsonl"), f); sha = ES.sha_file(str(d / "evidence.jsonl"))
    edit(d, "verdict.json", lambda j: j.update(log_head=head)); edit(d, "v8_parts.json", lambda s: s.update(log_head=head, evidence_sha256=sha))
    def cap(c):
        c.update(log_head=head, evidence_sha256=sha)
        for x in c["runs"]: x["cpu_s"] = 0.0
    edit(d, "v8_capture.json", cap, reanchor=True)
    assert not trust.check(str(d), anchor_key=KEY).issues  # HONEST LIMIT: a same-filesystem anchor does not stop a writer who holds the key
    assert any("pinned" in i for i in trust.check(str(d), anchor_key=KEY, pinned_head=pinned).issues)  # an out-of-band pinned head does


@pytest.mark.parametrize("name,fn", [
    ("bad_version", lambda a: a.update(schema="v8.anchor.2")), ("missing_mac", lambda a: a.pop("mac")), ("extra", lambda a: a.update(x=1)),
    ("altered_mac", lambda a: a.update(mac="0" * 64)), ("altered_file_digest", lambda a: a["files"].update({"verdict.json": "0" * 64})),
    ("dropped_file_entry", lambda a: a["files"].pop("v8_capture.json")), ("other_key_id", lambda a: a.update(key_id="0" * 16)),
    ("session_swapped", lambda a: a.update(session="0" * 32)),
])
def test_anchor_mutations(honest, tmp_path, name, fn):
    d = cp(honest, tmp_path); edit(d, "v8_anchor.json", fn)
    assert ES.check_anchor(str(d), KEY)["status"] == "invalid", name


def test_anchor_wrong_key_stripped_and_required(honest, tmp_path):
    d = cp(honest, tmp_path)
    assert ES.check_anchor(str(d), b"x" * 32)["status"] == "invalid"
    assert ES.check_anchor(str(d))["status"] == "unverified_no_key" and ES.check_anchor(str(d), require=True)["status"] == "invalid"
    os.unlink(d / "v8_anchor.json")
    assert ES.check_anchor(str(d))["status"] == "absent" and ES.check_anchor(str(d), KEY)["status"] == "invalid"  # stripped anchor is noticed once a key/requirement exists
    assert any("anchor" in i for i in trust.check(str(d), require_anchor=True).issues)


def test_anchored_file_swap_between_runs(honest, tmp_path):
    d = cp(honest, tmp_path); shutil.copy(honest / "ev2/v8_parts.json", d / "v8_parts.json")
    assert status(d)["trusted"] is False


def test_key_handling():
    assert ES.load_key("00" * 16) == bytes(16) and ES.load_key(None) is None or os.environ.get("SBGV8_ANCHOR_KEY")
    for bad in ("00" * 8, "zz" * 16, b"short"):
        with pytest.raises(ValueError): ES.load_key(bad)


# ---------------- validator role in its own interpreter + authenticated reply
def test_validate_isolated_matches_in_process_and_detects(honest, tmp_path):
    ok = procsep.validate_isolated(str(honest / "ev"), KEY)
    assert ok["trusted"] is True and ok["anchor"]["status"] == "ok"
    d = cp(honest, tmp_path); edit(d, "v8_capture.json", lambda c: c.update(session="5" * 32))
    assert procsep.validate_isolated(str(d), KEY)["trusted"] is False


@pytest.mark.parametrize("name,code", [
    ("timeout", "import time; time.sleep(30)"),
    ("crash", "import sys; sys.exit(3)"),
    ("garbage", "print('not json')"),
    ("no_output", "pass"),
    ("forged_trusted_bad_mac", "import json,sys; r=json.loads(sys.stdin.readline()); print(json.dumps({'v':1,'nonce':r['nonce'],'result':{'trusted':True,'reasons':[],'capture':{},'anchor':{},'sidecar':{}},'mac':'0'*64}))"),
    ("replayed_old_reply_wrong_nonce", "import json,sys; sys.stdin.readline(); print(json.dumps({'v':1,'nonce':'0'*32,'result':{'trusted':True,'reasons':[],'capture':{},'anchor':{},'sidecar':{}},'mac':'0'*64}))"),
])
def test_validator_failures_fail_safe(honest, name, code):
    res = procsep.validate_isolated(str(honest / "ev"), KEY, timeout_s=2, _cmd=[sys.executable, "-c", code])
    assert res["trusted"] is False and res["reasons"] and name


def test_validator_mac_is_over_nonce_and_result():
    n, k = "a" * 32, b"k" * 32
    assert procsep._reply_mac(k, n, {"a": 1}) != procsep._reply_mac(k, "b" * 32, {"a": 1}) != procsep._reply_mac(k, n, {"a": 2})


def test_cli_verify_reports_capture_and_anchor(honest, tmp_path, capsys, monkeypatch):
    from sbgv8.__main__ import main
    assert main(["verify", str(honest / "ev")]) == 0
    d = cp(honest, tmp_path); edit(d, "v8_capture.json", lambda c: c.update(trusted=False))
    assert main(["verify", str(d)]) == 1
