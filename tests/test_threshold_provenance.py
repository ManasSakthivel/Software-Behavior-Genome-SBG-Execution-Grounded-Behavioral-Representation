"""Threshold provenance regression tests.

* tau* for output_free_v7 is re-derivable from the dev split alone.
* The derivation refuses non-dev input.
* The frozen artifact matches an independent recomputation.
* tau = 0.08 has NO derivation artifact; no document may state that it was
  "fixed in advance / before scoring / not re-tuned" as established fact.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "final"))

import derive_threshold as dt  # noqa: E402

FROZEN = REPO_ROOT / "artifacts/final/THRESHOLD_FROZEN.json"


def test_youden_known_case():
    pts = [(0.0, 0), (0.1, 0), (0.5, 1), (0.9, 1)]
    tau, j, tpr, fpr = dt.youden(pts)
    assert j == 1.0 and tpr == 1.0 and fpr == 0.0
    assert 0.1 < tau < 0.5


def test_youden_ties_go_to_smaller_threshold():
    pts = [(0.0, 0), (0.2, 1), (0.4, 1), (0.4, 0)]
    tau, *_ = dt.youden(pts)
    assert tau == pytest.approx(0.1)


def test_derivation_inputs_are_dev_only():
    for path in (dt.DEV_PAIRS, dt.DEV_DATASET):
        assert "dev" in path.name
        assert "test" not in path.name
    assert "test" not in dt.AUDIT.name.lower().replace("v7", "")


def test_derivation_rows_are_all_dev():
    rows = dt.valid_dev_rows()
    assert rows and {r["split"] for r in rows} == {"dev"}


@pytest.mark.skipif(not FROZEN.exists(), reason="frozen threshold missing")
def test_frozen_threshold_matches_recomputation():
    frozen = json.loads(FROZEN.read_text())
    points = [(r["scores"][dt.PREDICTOR], r["label"]) for r in dt.valid_dev_rows()]
    tau, j, tpr, fpr = dt.youden(points)
    assert round(tau, 6) == frozen["tau_star"] == 0.072905
    assert round(j, 6) == frozen["dev_operating_point"]["youden_j"]
    assert len(points) == frozen["derived_on"]["n_valid_pairs"] == 345
    assert frozen["reads_no_test_or_external_labels"] is True


@pytest.mark.skipif(not FROZEN.exists(), reason="frozen threshold missing")
def test_frozen_artifact_records_008_as_superseded_not_derived():
    prev = json.loads(FROZEN.read_text())["previous_value"]
    assert prev["tau_star"] == 0.08
    assert "superseded" in prev["status"]


UNVERIFIED_PHRASES = (
    "fixed in advance and not re-tuned",
    "fixed before these pairs were scored and not re-tuned",
    "was fixed before these pairs were scored.",
    "the median SBG distance of semantics-preserving dev pairs, fixed",
)
CHECKED = ("README.md", "docs/generated/readme_results.md",
           "docs/generated/table_hard_negatives.md", "docs/figures/README.md",
           "docs/current/LIMITATIONS.md",
           "experiments/final/make_tables.py",
           "experiments/final/hard_negative_evaluation.py")


@pytest.mark.parametrize("rel", CHECKED)
def test_no_unverified_threshold_provenance_claim(rel):
    text = (REPO_ROOT / rel).read_text()
    for phrase in UNVERIFIED_PHRASES:
        assert phrase not in text, f"{rel} asserts unverified provenance: {phrase!r}"


def test_008_has_no_derivation_artifact():
    """If a derivation artifact for 0.08 is ever added, replace this test with one
    that verifies it; until then the provenance wording must stay hedged."""
    assert not (REPO_ROOT / "artifacts/final/THRESHOLD_008_DERIVATION.json").exists()
    assert (REPO_ROOT / "docs/current/THRESHOLD_PROVENANCE.md").exists()
