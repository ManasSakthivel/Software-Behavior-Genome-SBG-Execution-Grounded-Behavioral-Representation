import pytest
from sbgv8 import splits as S, manifest as M

def items(nproj=30, per=3, fams=("A", "B", "C")):
    return [{"pair_id": f"p{i}-{j}", "project": f"p{i}", "family": fams[i % len(fams)], "split": "development", "y": (i + j) % 2}
            for i in range(nproj) for j in range(per)]

def test_projects_never_split_and_deterministic():
    it = items()
    a = S.project_split(it, 7, {"development": .5, "calibration": .2, "evaluation": .2, "holdout": .1})
    assert S.assert_no_leakage(a)
    assert a == S.project_split(list(reversed(it)), 7, {"development": .5, "calibration": .2, "evaluation": .2, "holdout": .1})
    assert a["rows"] != S.project_split(it, 8)["rows"]
    sizes = {s: sum(1 for r in a["rows"] if r[3] == s) for s in S.SPLITS}
    assert sizes["development"] > sizes["holdout"] > 0

def test_stratification_keeps_projects_whole():
    it = items()
    a = S.project_split(it, 1, strata=lambda g: g[0]["family"])
    S.assert_no_leakage(a)
    for fam in "ABC": assert len({r[3] for r in a["rows"] if r[2] == fam}) >= 2

def test_leakage_detection_cross_project_and_family():
    a = S.project_split(items(), 1)
    bad = dict(a, rows=a["rows"] + [("zz", a["rows"][0][1], "A", "evaluation" if a["rows"][0][3] != "evaluation" else "development")])
    with pytest.raises(AssertionError, match="project leakage"): S.assert_no_leakage(bad)
    # project-grouped split generally shares families across splits: family leakage must be detectable
    with pytest.raises(AssertionError, match="family leakage"): S.assert_no_leakage(a, families=True)
    fa = S.project_split(items(), 1, group="family")
    assert S.assert_no_leakage(fa, families=True)

def test_nested_folds_disjoint():
    it = items(); folds = list(S.nested_group_folds(it, 3, 4, 3))
    assert len(folds) == 4
    assert sorted(g for f in folds for g in f["test_groups"]) == sorted({x["project"] for x in it})
    for f in folds:
        assert not set(f["train_groups"]) & set(f["test_groups"])
        for i in f["inner"]: assert not set(i["train_groups"]) & set(i["val_groups"]) and set(i["train_groups"]) | set(i["val_groups"]) == set(f["train_groups"])
    assert folds == list(S.nested_group_folds(it, 3, 4, 3))

def test_holdout_guard_blocks_by_default(tmp_path):
    it = [{"pair_id": "a", "split": "development", "y": 1}, {"pair_id": "h", "split": "holdout", "y": 0}]
    log = tmp_path / "log.jsonl"
    g = S.HoldoutGuard(log_path=str(log))
    assert g.labels(it[:1]) == {"a": 1}
    with pytest.raises(S.HoldoutLocked): g.labels(it)
    g2 = S.HoldoutGuard(token_path=str(tmp_path / "missing.token"), log_path=str(log))
    with pytest.raises(S.HoldoutLocked): g2.labels(it)
    assert not (tmp_path / "missing.token").exists()          # module never creates a token
    assert len(g.log) == 1 and g.log[0]["allowed"] is False
    assert len(log.read_text().splitlines()) == 2             # both refused attempts logged
    tok = tmp_path / "tok"; tok.write_text("synthetic test token")   # created by the TEST, not the module
    assert S.HoldoutGuard(token_path=str(tok)).labels(it)["h"] == 0
    assert S.strip_holdout_labels(it)[1]["y"] is None

def test_guard_source_never_writes_token():
    import inspect
    assert "open(self.token_path" not in inspect.getsource(S)

def dev_rows():
    return M.build_dev_manifest()

def test_family_shift_split_and_feasibility_synthetic():
    it = items(30, 4, ("A", "B", "C"))
    f = S.family_shift_feasibility(it, min_projects_per_family=5, min_labelled_pairs_per_family=20)
    assert f["feasible"], f
    a = S.family_shift_split(it, 5, n_held_out=1)
    assert S.assert_heldout_families(a) and len(a["held_out_families"]) == 1
    assert a == S.family_shift_split(it, 5, n_held_out=1)
    with pytest.raises(ValueError): S.family_shift_split([x for x in it if x["family"] == "A"], 1)

def test_feasibility_deferred_on_dev_manifest():
    rows = dev_rows()
    f = S.family_shift_feasibility(rows)
    assert not f["feasible"] and f["verdict"].startswith("DEFERRED") and f["reasons"]
