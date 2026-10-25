"""Claims registry must stay well-formed and must not over-claim.

The project is standard-library only, so the registry is checked with regular
expressions rather than a YAML parser.
"""
from __future__ import annotations

import pathlib
import re

REGISTRY = pathlib.Path(__file__).resolve().parent.parent / "docs" / "CLAIMS_REGISTRY.yaml"
STATUSES = {"SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED",
            "INSUFFICIENT_EVIDENCE", "NOT_EVALUABLE"}
EVIDENCE_CLASSES = {"previously_reported", "independently_recomputed",
                    "corrected_implementation", "new_unscored", "unverified"}


def _blocks():
    text = REGISTRY.read_text()
    body = text.split("legacy_claim_annotations:")[0]
    parts = re.split(r"^  - claim_id: ", body, flags=re.M)[1:]
    return [("C" + p.split("\n", 1)[0].strip().lstrip("C"), p) for p in parts]


def _field(block: str, name: str):
    m = re.search(rf"^    {name}: (.+)$", block, flags=re.M)
    return m.group(1).strip().strip('"') if m else None


def test_ids_unique_and_statuses_valid():
    blocks = _blocks()
    ids = [i for i, _ in blocks]
    assert len(blocks) >= 23
    assert len(ids) == len(set(ids))
    for claim_id, block in blocks:
        assert _field(block, "status") in STATUSES, claim_id


def test_new_claims_declare_evidence_class():
    for claim_id, block in _blocks():
        if int(claim_id[1:]) >= 16:
            assert _field(block, "evidence_class") in EVIDENCE_CLASSES, claim_id


def test_non_supported_new_claims_name_the_experiment_that_would_settle_them():
    for claim_id, block in _blocks():
        if int(claim_id[1:]) >= 16 and _field(block, "status") not in (
                "SUPPORTED", "NOT_SUPPORTED"):
            assert _field(block, "required_experiment"), claim_id


def test_observed_splits_are_never_called_held_out():
    for claim_id, block in _blocks():
        if _field(block, "split_status") in (None, "not_applicable"):
            continue
        assert _field(block, "split_status") == "observed_possibly_contaminated", claim_id
    # "held-out" may appear only when negated ("not held-out").
    for match in re.finditer(r"held-out", REGISTRY.read_text(), flags=re.I):
        before = REGISTRY.read_text()[max(0, match.start() - 4):match.start()].lower()
        assert before.endswith("not "), REGISTRY.read_text()[match.start() - 40:match.end()]


def test_publication_ready_claim_is_not_supported():
    block = dict(_blocks())["C023"]
    assert _field(block, "status") == "NOT_SUPPORTED"
