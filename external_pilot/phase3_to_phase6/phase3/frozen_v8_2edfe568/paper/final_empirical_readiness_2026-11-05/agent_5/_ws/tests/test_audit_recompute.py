"""The audit recomputation must reproduce the committed headline AUROCs."""
from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "experiments" / "final" / "audit_recompute.py"
ART = REPO_ROOT / "artifacts" / "final" / "pairs_v6test_output_free_v6.jsonl"


@pytest.mark.skipif(not ART.exists(), reason="artifact not present")
def test_headline_aurocs_reproduce_from_per_pair_records(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--out-dir", str(tmp_path), "--shuffles", "20"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (tmp_path / "audit_recompute.json").exists()
    assert (tmp_path / "results_manifest.json").exists()


@pytest.mark.skipif(not ART.exists(), reason="artifact not present")
def test_script_writes_only_under_out_dir(tmp_path):
    before = {p for p in REPO_ROOT.joinpath("artifacts").rglob("*") if p.is_file()}
    subprocess.run([sys.executable, str(SCRIPT), "--out-dir", str(tmp_path),
                    "--shuffles", "5"], cwd=REPO_ROOT, check=True,
                   capture_output=True, timeout=120)
    after = {p for p in REPO_ROOT.joinpath("artifacts").rglob("*") if p.is_file()}
    assert before == after
