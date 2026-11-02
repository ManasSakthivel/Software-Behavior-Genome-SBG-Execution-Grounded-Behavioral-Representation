"""Regression tests for the benchmark integrity checker.

The committed v6 benchmark contains EQUIVALENT-labelled SP-2 variants whose
class methods were renamed while ``self.<method>`` references were not, so the
variant raises AttributeError. These tests pin the detector and document the
extent of the defect; they do not (and must not) change any label.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "experiments" / "final"))

import data_integrity as di  # noqa: E402

BASE = '''
class Bucket:
    def allow(self, n):
        return n > 0
    def run(self):
        return self.allow(1)
'''


def test_detects_renamed_method_with_stale_self_reference():
    broken = BASE.replace("def allow", "def fn_allow")
    assert di.dangling_method_references(BASE, broken) == ["allow"]


def test_consistent_rename_is_not_flagged():
    ok = BASE.replace("allow", "fn_allow")
    assert di.dangling_method_references(BASE, ok) == []


def test_library_attributes_are_not_flagged():
    src = "def f(x):\n    x.append(1)\n    return x\n"
    renamed = src.replace("def f", "def fn_f")
    assert di.dangling_method_references(src, renamed) == ["f"] or \
        di.dangling_method_references(src, renamed) == []
    assert "append" not in di.dangling_method_references(src, renamed)


def test_unparsable_source_returns_empty():
    assert di.dangling_method_references("def (", BASE) == []


def _write_dataset(tmp_path, rows, files):
    ds = tmp_path / "ds"
    ds.mkdir()
    for split in ("train", "dev", "val", "test"):
        (ds / f"pairs_{split}.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows if r["split"] == split))
    for name, text in files.items():
        (tmp_path / name).write_text(text)
    return ds


def _row(pid, split="train", base="p", rel="EQUIVALENT", t="SP-1"):
    return {"pair_id": pid, "base_id": base, "base_path": "b.py",
            "variant_path": "v.py", "transformation_type": t,
            "semantic_relation": rel, "expected_label": rel, "split": split}


def test_duplicate_ids_and_split_leakage_are_reported(tmp_path):
    rows = [_row("a"), _row("a"), _row("c", split="test")]
    ds = _write_dataset(tmp_path, rows, {"b.py": "x = 1\n", "v.py": "x = 1\n"})
    report = di.check_dataset(ds, repo=tmp_path)
    assert report["defect_counts"]["duplicate_pair_id"] == 1
    assert report["defect_counts"]["program_in_multiple_splits"] == 1


def test_missing_and_uncompilable_files_are_reported(tmp_path):
    rows = [_row("a")]
    ds = _write_dataset(tmp_path, rows, {"b.py": "def (\n"})
    counts = di.check_dataset(ds, repo=tmp_path)["defect_counts"]
    assert counts["uncompilable_base_path"] == 1
    assert counts["missing_variant_path"] == 1


def test_label_relation_disagreement_is_reported(tmp_path):
    row = _row("a")
    row["expected_label"] = "CHANGED"
    ds = _write_dataset(tmp_path, [row], {"b.py": "x=1\n", "v.py": "x=1\n"})
    assert di.check_dataset(ds, repo=tmp_path)["defect_counts"][
        "label_relation_disagree"] == 1


V6 = REPO_ROOT / "benchmark/datasets/v6"


@pytest.mark.skipif(not V6.exists(), reason="v6 dataset not present")
def test_committed_v6_has_documented_sp2_defect_and_nothing_else():
    report = di.check_dataset(V6)
    assert report["defect_counts"] == {"sp2_dangling_method_reference": 75}
    assert report["sp2_dangling_by_split"] == {
        "train": 30, "dev": 13, "val": 10, "test": 22}
    assert report["sp2_equivalent_pairs_by_split"] == {
        "train": 84, "dev": 30, "val": 27, "test": 39}


@pytest.mark.skipif(not V6.exists(), reason="v6 dataset not present")
def test_labels_were_not_modified_by_the_checker():
    """The checker is read-only: v6 test labels remain 246 CHANGED / 242 EQUIVALENT."""
    di.check_dataset(V6)
    rows = [json.loads(l) for l in (V6 / "pairs_test.jsonl").read_text().splitlines() if l]
    assert sum(r["semantic_relation"] == "CHANGED" for r in rows) == 246
    assert sum(r["semantic_relation"] == "EQUIVALENT" for r in rows) == 242
