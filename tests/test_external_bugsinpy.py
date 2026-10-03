"""Tests for the BugsInPy external evaluation (experiments/final/external_bugsinpy.py).

Offline only: they exercise patch parsing, unit extraction, the static
eligibility and safety rules, and the integrity of the committed manifest,
freeze and result artifacts.
"""
import ast
import json
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from experiments.final import external_bugsinpy as eb  # noqa: E402

PATCH = """diff --git a/pkg/mod.py b/pkg/mod.py
index 1..2 100644
--- a/pkg/mod.py
+++ b/pkg/mod.py
@@ -3,3 +3,3 @@ import re
 def f(x):
-    return x + 1
+    return x + 2

@@ -10,2 +10,3 @@ def g(y):
     z = y
+    z += 1
     return z
"""


def test_parse_patch_lines_and_anchors():
    files = eb.parse_patch(PATCH)
    assert len(files) == 1
    f = files[0]
    assert f["old"] == "pkg/mod.py" and f["new"] == "pkg/mod.py"
    assert 4 in f["old_lines"] and 4 in f["new_lines"]
    # the pure insertion in the second hunk anchors to the old line before it
    assert 10 in f["old_lines"] and 11 in f["new_lines"]


def test_parse_patch_survives_a_miscounted_hunk():
    bad = PATCH.replace("@@ -3,3 +3,3 @@", "@@ -3,4 +3,4 @@")
    f = eb.parse_patch(bad)[0]
    assert 10 in f["old_lines"] and 11 in f["new_lines"]


def test_parse_patch_does_not_mistake_removed_dashes_for_headers():
    patch = ("diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n"
             "@@ -1,2 +1,2 @@\n--- comment-like removed line\n+x = 1\n y = 2\n")
    f = eb.parse_patch(patch)[0]
    assert f["old"] == "a.py" and f["old_lines"] == {1}


SOURCE = '''import re
import os
import numpy as np
from . import sibling
LIMIT = 10
DYNAMIC = compute()

def helper(v):
    return v * LIMIT

def changed(text):
    return helper(len(re.findall("a", text)))

def uses_numpy(v):
    return np.sum(v)

def uses_internal(v):
    return sibling.go(v)

def uses_dynamic(v):
    return DYNAMIC + v

def deletes(p):
    os.remove(p)

class Box:
    def __init__(self, items):
        self.items = items
    def total(self):
        return helper(len(self.items))
'''


@pytest.fixture(scope="module")
def index():
    return eb._ModuleIndex(ast.parse(SOURCE), SOURCE, "pkg/mod.py")


def test_unit_closure_includes_helpers_constants_and_stdlib(index):
    unit, reason = eb.build_unit(index, "changed")
    assert reason is None
    assert "import re" in unit and "LIMIT = 10" in unit and "def helper" in unit
    assert "numpy" not in unit and "def uses_numpy" not in unit
    compile(unit, "<unit>", "exec")


def test_third_party_and_internal_imports_are_ineligible(index):
    assert eb.build_unit(index, "uses_numpy")[1].startswith("third_party_import")
    assert eb.build_unit(index, "uses_internal")[1].startswith("project_internal_import")


def test_non_literal_global_is_ineligible(index):
    assert eb.build_unit(index, "uses_dynamic")[1].startswith("non_literal_or_unresolved_global")


def test_unsafe_os_call_is_ineligible(index):
    assert eb.build_unit(index, "deletes")[1] == "unsafe_os_call:os.remove"


def test_class_unit_closes_over_module_helpers(index):
    unit, reason = eb.build_unit(index, "Box")
    assert reason is None and "def helper" in unit and "class Box" in unit


def test_locate_function_method_and_module_level():
    tree = ast.parse(SOURCE)
    lines = SOURCE.splitlines()
    line_of = {text.strip(): n for n, text in enumerate(lines, 1)}
    assert eb._locate(tree, line_of['return helper(len(re.findall("a", text)))'])[:2] == (
        "changed", "changed")
    assert eb._locate(tree, line_of["return helper(len(self.items))"])[:2] == ("Box", "Box.total")
    assert eb._locate(tree, line_of["LIMIT = 10"])[2] == "change_at_module_level"


def test_positive_observability_uses_static_reachability():
    source = "def entry(x):\n    return inner(x)\n\ndef inner(x):\n    return x\n\ndef other(x):\n    return x\n"
    unit = {"changed_members": ["inner"], "kind": "function", "unit": "inner"}
    assert eb._positive_is_observable(source, "entry", "annotated:entry", unit)
    unit_other = {"changed_members": ["other"], "kind": "function", "unit": "other"}
    assert not eb._positive_is_observable(source, "entry", "annotated:entry", unit_other)


# ---------------------------------------------------------------------------
# Committed artifacts
# ---------------------------------------------------------------------------

needs_manifest = pytest.mark.skipif(not eb.MANIFEST.exists(), reason="BugsInPy manifest not built")


@needs_manifest
def test_manifest_accounts_for_every_bug():
    manifest = json.loads(eb.MANIFEST.read_text())
    bugs = manifest["bugs"]
    assert manifest["counts"]["bugs_total"] == len(bugs)
    for entry in bugs:
        assert entry["split"] == "external_test"
        assert entry["eligible"] or entry["exclusion_reason"], entry["id"]
        for unit in entry["units"]:
            assert unit["eligible"] or unit["exclusion_reason"], (entry["id"], unit["unit"])
    excluded = sum(manifest["bug_exclusion_taxonomy"].values())
    assert excluded + manifest["counts"]["bugs_eligible"] == len(bugs)


@needs_manifest
def test_freeze_matches_vendored_inputs():
    frozen = json.loads(eb.FREEZE.read_text())
    combined, _ = eb._freeze_digest()
    assert combined == frozen["combined_sha256"]


@needs_manifest
def test_vendored_units_compile_and_negatives_differ():
    manifest = json.loads(eb.MANIFEST.read_text())
    for entry in manifest["bugs"]:
        for unit in entry["units"]:
            if not unit["eligible"]:
                continue
            fixed = (REPO_ROOT / unit["fixed_path"]).read_text()
            compile((REPO_ROOT / unit["buggy_path"]).read_text(), unit["buggy_path"], "exec")
            compile(fixed, unit["fixed_path"], "exec")
            for neg in unit["negatives"]:
                source = (REPO_ROOT / neg["path"]).read_text()
                compile(source, neg["path"], "exec")
                assert eb._normalised(source) != eb._normalised(fixed)


def _result_artifacts():
    return sorted(eb.ARTIFACTS.glob("BUGSINPY_*.json"))


@pytest.mark.skipif(not _result_artifacts(), reason="no BugsInPy result artifact")
@pytest.mark.parametrize("path", _result_artifacts(), ids=lambda p: p.name)
def test_result_artifact_is_consistent(path):
    result = json.loads(path.read_text())
    frozen = json.loads(eb.FREEZE.read_text())
    assert result["freeze"]["combined_sha256"] == frozen["combined_sha256"]
    pairs_path = eb.ARTIFACTS / f"pairs_bugsinpy_{result['protocol']}.jsonl"
    rows = [json.loads(line) for line in pairs_path.read_text().splitlines()]
    sets = result["sets"]
    assert sets["ALL"]["n_pairs"] == len(rows)
    assert sets["EVALUABLE"]["n_pairs"] == sum(r["evaluated"] for r in rows)
    assert sets["ALL"]["n_pairs"] >= sets["EVALUABLE"]["n_pairs"] >= sets["VALID"]["n_pairs"]
    failed = sum(result["stage_counts"]["pairs_failed_at_execution"].values())
    assert failed + sets["EVALUABLE"]["n_pairs"] == len(rows)
    for row in rows:
        assert row["label"] in (0, 1)
        assert (row["role"] == "positive") == (row["label"] == 1)
