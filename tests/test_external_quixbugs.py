"""Integrity tests for the QuixBugs external evaluation.

These tests cover four things:
- Expected outputs never reach extraction.
- The manifest is frozen.
- The declared-entry mapping is structural.
- The per-pair artifacts agree with the frozen manifest.
"""
import ast
import json
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from experiments.final import external_common as ec          # noqa: E402
from experiments.final import external_quixbugs as qb        # noqa: E402

SENTINEL = "EXPECTED_OUTPUT_SENTINEL_7f3a"


def _contains(value, needle) -> bool:
    if value == needle:
        return True
    if isinstance(value, (list, tuple)):
        return any(_contains(v, needle) for v in value)
    if isinstance(value, dict):
        return any(_contains(k, needle) or _contains(v, needle) for k, v in value.items())
    return False


class TestExpectedOutputsNeverReachExtraction:
    def test_loader_drops_expected_half(self, tmp_path):
        case = tmp_path / "prog.json"
        case.write_text(json.dumps([[1, 2], SENTINEL]) + "\n"
                        + json.dumps([[[3, 4]], [SENTINEL, 5]]) + "\n")
        inputs = qb.load_declared_inputs(case)
        assert inputs == [(1, 2), ([3, 4],)]
        assert not _contains(inputs, SENTINEL)

    def test_json_testcases_read_only_by_the_loader(self):
        """Only ``load_declared_inputs`` opens a test-case file.

        The other references to TESTCASE_DIR build paths that are handed to it.
        """
        source = pathlib.Path(qb.__file__).read_text()
        tree = ast.parse(source)
        readers = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                body = ast.unparse(node)
                if "json.loads(line)" in body or "case[0]" in body:
                    readers.append(node.name)
        assert readers == ["load_declared_inputs"]

    def test_worker_gets_inputs_only_from_loader(self):
        source = ast.unparse(ast.parse(pathlib.Path(qb.__file__).read_text()))
        worker_src = source.split("def worker(", 1)[1].split("\ndef ", 1)[0]
        assert "load_declared_inputs(" in worker_src
        assert "TESTCASE_DIR" not in worker_src
        assert "json_testcases" not in worker_src


class TestDeclaredEntryMapping:
    FIXED = "def helper(x):\n    return x\n\ndef prog(a):\n    return helper(a)\n"

    def test_by_name(self):
        assert qb.resolve_declared_entry("prog", self.FIXED, self.FIXED) == ("prog", "by_name")

    def test_by_ordinal_after_rename(self):
        renamed = "def fn_helper(x):\n    return x\n\ndef fn_prog(a):\n    return fn_helper(a)\n"
        assert qb.resolve_declared_entry("prog", self.FIXED, renamed) == ("fn_prog", "by_ordinal:1")


MANIFEST = qb.MANIFEST_PATH
FREEZE = qb.FREEZE_PATH


@pytest.mark.skipif(not MANIFEST.exists(), reason="QuixBugs manifest not generated")
class TestFrozenManifest:
    def test_freeze_matches_manifest_and_negatives(self):
        qb.verify_freeze()

    def test_every_file_accounted_for(self):
        manifest = json.loads(MANIFEST.read_text())
        listed = {p["buggy_path"].split("/")[-1] for p in manifest["programs"]}
        listed |= {s["file"].split("/")[-1] for s in manifest["scaffolding"]}
        on_disk = {p.name for p in qb.BUGGY_DIR.glob("*.py")}
        assert listed == on_disk

    def test_all_programs_external_test_split(self):
        manifest = json.loads(MANIFEST.read_text())
        assert {p["split"] for p in manifest["programs"]} == {"external_test"}
        assert all(p["written_for_sbg"] is False for p in manifest["programs"])

    def test_negatives_follow_preregistered_rule(self):
        manifest = json.loads(MANIFEST.read_text())
        for program in manifest["programs"]:
            kinds = [n["transformation_type"] for n in program.get("negatives", [])]
            assert len(kinds) <= ec.N_NEGATIVES
            order = [ec.SP_ORDER.index(k) for k in kinds]
            assert order == sorted(order)
            assert all(n["seed"] == ec.SP_SEED for n in program.get("negatives", []))


def _artifacts():
    return sorted(ec.ARTIFACT_DIR.glob("pairs_quixbugs_*.jsonl"))


@pytest.mark.skipif(not _artifacts(), reason="QuixBugs per-pair artifacts not generated")
class TestPerPairArtifacts:
    def test_rows_cover_the_frozen_manifest(self):
        manifest = json.loads(MANIFEST.read_text())
        expected = sum(1 + len(p.get("negatives", [])) for p in manifest["programs"])
        freeze_sha = ec.sha256_file(FREEZE)
        for path in _artifacts():
            rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
            assert len(rows) == expected, path.name
            assert len({r["pair_id"] for r in rows}) == len(rows)
            assert {r["freeze_sha256"] for r in rows} == {freeze_sha}

    def test_every_unevaluated_pair_has_a_reason(self):
        for path in _artifacts():
            for line in path.read_text().splitlines():
                row = json.loads(line)
                if not row["evaluated"]:
                    assert row["failure_kind"], row["pair_id"]

    def test_no_absolute_paths(self):
        for path in _artifacts():
            assert str(REPO_ROOT) not in path.read_text()
