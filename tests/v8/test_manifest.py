import dataclasses, os
import pytest
from sbgv8 import manifest as M

def row(pid, proj="p1", split="development", **k):
    return M.ManifestRow(project=proj, family="f1", family_rule="r", pair_id=pid, split=split, provenance={"s": "synthetic-fixture"}, **k)

def test_valid_and_duplicate_and_missing():
    assert M.validate([row("a"), row("b", "p2")]) == []
    assert any("duplicate" in i for i in M.validate([row("a"), row("a", "p2")]))
    assert any("missing family_rule" in i for i in M.validate([dataclasses.replace(row("a"), family_rule="")]))
    with pytest.raises(ValueError): M.validate([row("a"), row("a")], raise_on_error=True)

def test_one_split_per_project_and_family_rule_consistency():
    assert any("several splits" in i for i in M.validate([row("a", "p", "development"), row("b", "p", "evaluation")]))
    r2 = dataclasses.replace(row("b", "p"), family="other")
    assert any("several family" in i for i in M.validate([row("a", "p"), r2]))

def test_holdout_rows_carry_no_labels():
    assert any("holdout" in i for i in M.validate([row("a", split="holdout", y=1)]))
    assert any("holdout" in i for i in M.validate([row("a", split="holdout", label_source="x")]))
    assert M.validate([row("a", split="holdout", outcome_class="sealed")]) == []

def test_exclusion_needs_reason():
    assert any("without reason" in i for i in M.validate([row("a", include=False)]))

def test_io_roundtrip_and_hash_determinism(tmp_path):
    rows = [row("b", "p2", y=1, reasons=["x"]), row("a", change_meta={"k": [1, 2]})]
    h = M.manifest_hash(rows)
    M.write_jsonl(rows, str(tmp_path / "m.jsonl")); M.write_csv(rows, str(tmp_path / "m.csv"))
    for back in (M.read_jsonl(str(tmp_path / "m.jsonl")), M.read_csv(str(tmp_path / "m.csv"))):
        assert M.manifest_hash(back) == h
    assert M.manifest_hash(list(reversed(rows))) == h
    assert M.manifest_hash([row("a")]) != M.manifest_hash([row("a2")])

def test_family_rule_label_independent():
    assert M.derive_family_dev("quixbugs:gcd") == M.derive_family_dev("quixbugs_neg:gcd__sp-1_s0") == "quixbugs"
    assert M.derive_family_dev("synthetic:dev__x__sc1_s0") == "synthetic"
    assert M.derive_family_dev("bugsinpy_units:a__1__b") == "bugsinpy"

CSV = M.DEV_CSV
@pytest.mark.skipif(not os.path.exists(CSV) and not os.path.exists("datasets/v8/dev_records.jsonl"), reason="no dev source")
def test_dev_manifest_builds_valid_and_labelled_as_dev():
    rows = M.build_dev_manifest()
    assert M.validate(rows) == [] and len(rows) == len({r.pair_id for r in rows})
    assert all(r.status == M.DEV_STATUS and r.split == "development" and r.outcome_class == "not_adjudicated" for r in rows)
    assert all((r.y is None) == (not r.include) for r in rows)
    assert M.manifest_hash(rows) == M.manifest_hash(M.build_dev_manifest())
