import json, os, shutil
from sbgv8 import adapter, collect
from sbgv8.schema import EvidenceRecord
from .test_collect import BASE, CFG, VAR, write

INS = [{"id": "a", "args": [1]}, {"id": "b", "args": [2]}, {"id": "c", "args": [-3]}]


import pytest


@pytest.fixture(scope="module")
def ev(tmp_path_factory):
    t = tmp_path_factory.mktemp("a"); b, v = write(t / "s")
    rec = collect.compare(b, v, "f", INS, CFG, str(t / "ev"), label=1, project="proj", family="fam")
    return t / "ev", rec


def test_fields(ev):
    d, r = ev
    assert isinstance(r, EvidenceRecord) and r.pair_id.startswith("Pai") or r.pair_id.startswith("pai")
    assert (r.project, r.family, r.y) == ("proj", "fam", 1) and len(r.inputs) == 3
    assert all(i.outcome == "SAME" and i.deterministic and i.n_repeat_runs == 2 for i in r.inputs)  # r_det=2 -> 1 repeat per side
    assert set(r.config) == {"r_det", "r_replay", "k_alt", "s2_branch_floor"} and r.config["r_det"] == 2
    assert r.changed_units["variant"] == [3] and r.changed_units["base"] == [3]
    assert r.static_branches == {"base": 0, "variant": 0}  # the changed line holds no branch instruction


def test_fingerprint_and_channels(ev):
    _, r = ev
    assert len({i.obs_fingerprint for i in r.inputs}) == 3 and all(len(i.obs_fingerprint) == 32 for i in r.inputs)
    assert all(i.channels_present == ["outcome", "exception", "side_effect", "api"] for i in r.inputs)


def test_hits_from_sidecar(ev):
    _, r = ev
    assert 3 in r.inputs[0].hits["variant"] and r.inputs[0].hits["variant"] != r.inputs[2].hits["variant"]


def test_no_sidecar(ev, tmp_path):
    d = tmp_path / "n"; shutil.copytree(ev[0], d); os.unlink(d / "v8_parts.json")
    r = adapter.load_record(str(d))
    assert r.meta["no_hits"] and r.meta["sidecar"] == "missing" and all(i.hits == {"base": [], "variant": []} for i in r.inputs)
    assert r.integrity_ok and r.project == "unknown"


def test_bad_sidecar_ignored_and_integrity_false(ev, tmp_path):
    d = tmp_path / "t"; shutil.copytree(ev[0], d)
    s = json.load(open(d / "v8_parts.json")); s["parts"][0]["hits"]["variant"] = [1]; json.dump(s, open(d / "v8_parts.json", "w"))
    r = adapter.load_record(str(d))
    assert r.meta["sidecar"] == "inconsistent" and r.meta["no_hits"] and not r.integrity_ok


def test_roundtrip_digest(ev):
    _, r = ev
    r2 = EvidenceRecord.from_json(r.to_json())
    assert r2.digest() == r.digest() and r2.inputs[0].hits == r.inputs[0].hits


def test_divergent_record_and_lossy_free(tmp_path):
    b, v = write(tmp_path / "s", v="def f(x):\n    return x + 5\n")
    r = collect.compare(b, v, "f", INS, CFG, str(tmp_path / "e"))
    assert r.v7b_verdict == "DIVERGENT_OBSERVABLE" and r.inputs[0].outcome == "CONFIRMED_DIFF" and r.y is None
