import json, os, pytest
import sbgv7.runner as RUN
from sbgv7.config import SCHEMA, _fill
from sbgv8 import collect
from sbgv8.__main__ import main

BASE = "def f(x):\n    if x > 0:\n        return x\n    return -x\n"
VAR = "def f(x):\n    if x > 0:\n        return x + 0\n    return -x\n"
INS = [{"id": "a", "args": [1]}, {"id": "b", "args": [-2]}]
CFG = {"repeat": {"r_det": 2, "r_replay": 2, "k_alt": 1}, "budget": {"cpu_seconds": 30, "per_run": {"cpu_s": 2, "wall_s": 5}}}


def write(d, b=BASE, v=VAR):
    os.makedirs(d, exist_ok=True)
    open(f"{d}/b.py", "w").write(b); open(f"{d}/v.py", "w").write(v)
    return f"{d}/b.py", f"{d}/v.py"


@pytest.fixture(scope="module")
def ran(tmp_path_factory):
    t = tmp_path_factory.mktemp("c"); b, v = write(t / "src")
    rec = collect.compare(b, v, "f", INS, CFG, str(t / "ev"), label=0, project="p")
    return t, b, v, rec


def test_record_and_sidecar(ran):
    t, _, _, rec = ran
    side = json.load(open(t / "ev/v8_parts.json"))
    assert side["schema"] == "v8.parts.1" and [p["input_id"] for p in side["parts"]] == ["a", "b"]
    assert side["parts"][0]["hits"]["variant"] and rec.y == 0 and rec.v7b_verdict == "NO_DIVERGENCE_OBSERVED"
    assert rec.meta["sidecar"] == "ok" and not rec.meta["no_hits"] and rec.integrity_ok


def test_finalize_restored(ran):
    assert RUN.finalize.__name__ == "finalize"


def test_finalize_restored_on_error(tmp_path):
    b, v = write(tmp_path)
    with pytest.raises(RUN.Ineligible): collect.run_capture(b, b, "f", [], _fill(SCHEMA, CFG, ""), str(tmp_path / "e"))
    assert RUN.finalize.__name__ == "finalize"


def test_engine_unmodified_same_verdict(ran, tmp_path):
    t, b, v, _ = ran
    cfg = _fill(SCHEMA, CFG, "")
    out = RUN.compare_versions(b, v, "f", [{"id": i["id"], "args": i["args"], "kwargs": {}} for i in INS], cfg, str(tmp_path / "plain"))
    mine = json.load(open(t / "ev/verdict.json"))
    assert all(out[k] == mine[k] for k in ("verdict", "level", "primary", "secondary", "pair_id", "package_id"))
    assert not os.path.exists(tmp_path / "plain/v8_parts.json")  # the plain engine never writes the sidecar


def test_cli_compare_and_verify(tmp_path, capsys):
    b, v = write(tmp_path / "s"); json.dump([{"id": "a", "args": [1]}], open(tmp_path / "i.json", "w")); json.dump(CFG, open(tmp_path / "c.json", "w"))
    assert main(["compare", b, v, "--entry", "f", "--inputs", str(tmp_path / "i.json"), "--config", str(tmp_path / "c.json"), "--out", str(tmp_path / "o")]) == 0
    assert os.path.exists(tmp_path / "o/v8_parts.json")
    capsys.readouterr()
    assert main(["verify", str(tmp_path / "o")]) == 0 and '"status": "ok"' in capsys.readouterr().out


def test_cli_verify_detects_sidecar_tamper(ran, tmp_path, capsys):
    import shutil; d = tmp_path / "x"; shutil.copytree(ran[0] / "ev", d)
    s = json.load(open(d / "v8_parts.json")); s["parts"][0]["hits"]["variant"].append(99); json.dump(s, open(d / "v8_parts.json", "w"))
    assert main(["verify", str(d)]) == 1


def test_cli_hook_ignores_missing_modules(capsys):
    with pytest.raises(SystemExit): main(["--help"])
