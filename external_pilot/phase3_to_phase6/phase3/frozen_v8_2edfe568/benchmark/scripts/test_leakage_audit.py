#!/usr/bin/env python3
"""
test_leakage_audit.py — Unit tests for leakage_audit.py and assign_splits.py.

Run:  python3 -m pytest benchmark/scripts/test_leakage_audit.py -v
  or: python3 benchmark/scripts/test_leakage_audit.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Make sure sibling scripts are importable regardless of cwd
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from leakage_audit import (
    check_base_program_leakage,
    check_category_leakage,
    check_filename_collisions,
    check_near_duplicates,
    check_transformation_family_leakage,
    run_audit,
)
from assign_splits import assign_splits


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_programs(ids_prefixes: list[tuple[str, str]]) -> list[dict]:
    """Build a minimal programs list from (program_id, category_prefix) pairs."""
    return [
        {
            "program_id": pid,
            "category_prefix": prefix,
            "category": prefix.upper(),
            "filename": f"{pid}.py",
        }
        for pid, prefix in ids_prefixes
    ]


_PRESERVING_MANIFEST = {
    "transformations": [
        {"id": "SP-1"},
        {"id": "SP-2"},
    ]
}

_MUTATION_MANIFEST = {
    "mutation_types": [
        {"id": "SC-1"},
        {"id": "SC-2"},
    ]
}


# ---------------------------------------------------------------------------
# check_base_program_leakage
# ---------------------------------------------------------------------------

class TestBaseProgramLeakage(unittest.TestCase):

    def test_no_leakage(self):
        splits = {"train": ["a", "b"], "test": ["c", "d"]}
        found, issues = check_base_program_leakage(splits)
        self.assertFalse(found)
        self.assertEqual(issues, [])

    def test_leakage_detected(self):
        splits = {"train": ["a", "b", "c"], "test": ["c", "d"]}
        found, issues = check_base_program_leakage(splits)
        self.assertTrue(found)
        self.assertEqual(len(issues), 1)
        self.assertIn("'c'", issues[0])

    def test_multiple_leakage(self):
        splits = {"train": ["a", "b", "c"], "test": ["b", "c"]}
        found, issues = check_base_program_leakage(splits)
        self.assertTrue(found)
        self.assertEqual(len(issues), 2)

    def test_empty_splits(self):
        splits = {"train": [], "test": []}
        found, issues = check_base_program_leakage(splits)
        self.assertFalse(found)
        self.assertEqual(issues, [])

    def test_missing_test_key(self):
        splits = {"train": ["a"]}
        found, issues = check_base_program_leakage(splits)
        self.assertFalse(found)

    def test_missing_train_key(self):
        splits = {"test": ["a"]}
        found, issues = check_base_program_leakage(splits)
        self.assertFalse(found)


# ---------------------------------------------------------------------------
# check_transformation_family_leakage
# ---------------------------------------------------------------------------

class TestTransformationFamilyLeakage(unittest.TestCase):

    def test_no_leakage_normal(self):
        splits = {"train": ["a", "b"], "test": ["c"]}
        found, issues = check_transformation_family_leakage(
            splits, _PRESERVING_MANIFEST, _MUTATION_MANIFEST
        )
        self.assertFalse(found)
        self.assertEqual(issues, [])

    def test_empty_test_no_leakage(self):
        splits = {"train": ["a", "b"], "test": []}
        found, issues = check_transformation_family_leakage(
            splits, _PRESERVING_MANIFEST, _MUTATION_MANIFEST
        )
        self.assertFalse(found)

    def test_empty_train_with_test_is_leakage(self):
        splits = {"train": [], "test": ["a"]}
        found, issues = check_transformation_family_leakage(
            splits, _PRESERVING_MANIFEST, _MUTATION_MANIFEST
        )
        self.assertTrue(found)
        # One issue per transformation type (SP-1, SP-2, SC-1, SC-2)
        self.assertEqual(len(issues), 4)

    def test_both_empty_no_leakage(self):
        splits = {"train": [], "test": []}
        found, issues = check_transformation_family_leakage(
            splits, _PRESERVING_MANIFEST, _MUTATION_MANIFEST
        )
        self.assertFalse(found)


# ---------------------------------------------------------------------------
# check_category_leakage
# ---------------------------------------------------------------------------

class TestCategoryLeakage(unittest.TestCase):

    def _programs(self):
        return _make_programs([
            ("sort_qs", "sort"),
            ("sort_ms", "sort"),
            ("graph_bfs", "graph"),
            ("graph_dfs", "graph"),
            ("ds_bst", "ds"),
        ])

    def test_no_leakage(self):
        programs = self._programs()
        splits = {
            "train": ["sort_qs", "graph_bfs", "ds_bst"],
            "test":  ["sort_ms", "graph_dfs"],
        }
        found, issues = check_category_leakage(programs, splits)
        self.assertFalse(found)
        self.assertEqual(issues, [])

    def test_category_only_in_test(self):
        programs = self._programs()
        splits = {
            "train": ["sort_qs", "sort_ms"],
            "test":  ["graph_bfs", "ds_bst"],   # graph and ds absent from train
        }
        found, issues = check_category_leakage(programs, splits)
        self.assertTrue(found)
        cats_in_issues = " ".join(issues)
        self.assertIn("graph", cats_in_issues)
        self.assertIn("ds",    cats_in_issues)

    def test_empty_test_no_leakage(self):
        programs = self._programs()
        splits   = {"train": ["sort_qs"], "test": []}
        found, issues = check_category_leakage(programs, splits)
        self.assertFalse(found)


# ---------------------------------------------------------------------------
# check_filename_collisions
# ---------------------------------------------------------------------------

class TestFilenameCollisions(unittest.TestCase):

    def test_no_collisions(self):
        programs = [
            {"program_id": "a", "filename": "a.py"},
            {"program_id": "b", "filename": "b.py"},
        ]
        count, issues = check_filename_collisions(programs)
        self.assertEqual(count, 0)
        self.assertEqual(issues, [])

    def test_single_collision(self):
        programs = [
            {"program_id": "a",  "filename": "dup.py"},
            {"program_id": "a2", "filename": "dup.py"},
            {"program_id": "b",  "filename": "b.py"},
        ]
        count, issues = check_filename_collisions(programs)
        self.assertEqual(count, 1)
        self.assertIn("dup.py", issues[0])

    def test_multiple_collisions(self):
        programs = [
            {"program_id": "a",  "filename": "x.py"},
            {"program_id": "a2", "filename": "x.py"},
            {"program_id": "b",  "filename": "y.py"},
            {"program_id": "b2", "filename": "y.py"},
        ]
        count, issues = check_filename_collisions(programs)
        self.assertEqual(count, 2)


# ---------------------------------------------------------------------------
# check_near_duplicates (synthetic, no file I/O)
# ---------------------------------------------------------------------------

class TestNearDuplicates(unittest.TestCase):
    """
    We patch _load_source via monkeypatching the module-level dict so we can
    inject controlled source strings without touching the filesystem.
    """

    def _run_with_sources(self, source_map: dict[str, str]) -> tuple[int, list[str]]:
        """
        Invoke near-dup logic by temporarily overriding the BASE_PROG_DIR
        through a controlled _load_source shim.
        """
        import leakage_audit as la
        original = la._load_source

        def fake_load(filename: str) -> str | None:
            # filename is "prog_id.py"; strip .py to get the key
            key = filename.replace(".py", "")
            return source_map.get(key)

        la._load_source = fake_load
        try:
            programs = [{"program_id": k, "filename": f"{k}.py"} for k in source_map]
            count, issues = la.check_near_duplicates(programs, threshold=0.95)
        finally:
            la._load_source = original

        return count, issues

    def test_no_duplicates(self):
        sources = {
            "prog_a": "def foo(): return 1",
            "prog_b": "def bar(): x = [1, 2, 3]; return sum(x)",
        }
        count, issues = self._run_with_sources(sources)
        self.assertEqual(count, 0)

    def test_identical_programs_flagged(self):
        code = "def foo(): return 42"
        sources = {"prog_a": code, "prog_b": code}
        count, issues = self._run_with_sources(sources)
        self.assertEqual(count, 1)
        self.assertIn("prog_a", issues[0])
        self.assertIn("prog_b", issues[0])

    def test_high_overlap_flagged(self):
        # 19 shared tokens, 1 different → Jaccard = 19/20 = 0.95
        shared = " ".join([f"tok{i}" for i in range(19)])
        src_a = shared + " unique_a"
        src_b = shared + " unique_b"
        count, issues = self._run_with_sources({"prog_a": src_a, "prog_b": src_b})
        # Jaccard = 19 / (19+1+1) = 19/21 ≈ 0.905 < 0.95 → not flagged
        self.assertEqual(count, 0)

    def test_exact_threshold_boundary(self):
        # 95 shared tokens, 5 unique each → |A∪B| = 105, |A∩B| = 95 → J = 95/105 ≈ 0.905
        shared = " ".join([f"t{i}" for i in range(95)])
        extra_a = " ".join([f"ua{i}" for i in range(5)])
        extra_b = " ".join([f"ub{i}" for i in range(5)])
        src_a = shared + " " + extra_a
        src_b = shared + " " + extra_b
        count, _ = self._run_with_sources({"p_a": src_a, "p_b": src_b})
        # J = 95/105 ≈ 0.905 — below threshold
        self.assertEqual(count, 0)


# ---------------------------------------------------------------------------
# assign_splits
# ---------------------------------------------------------------------------

class TestAssignSplits(unittest.TestCase):

    def _make_60_programs(self) -> list[dict]:
        """Recreate the exact 60-program manifest structure."""
        data = [
            ("api",   4),
            ("conc",  3),
            ("ds",    6),
            ("err",   4),
            ("file",  5),
            ("fsm",   5),
            ("graph", 6),
            ("math",  6),
            ("parse", 3),
            ("res",   4),
            ("sort",  8),
            ("str",   6),
        ]
        programs = []
        for prefix, count in data:
            for i in range(count):
                programs.append({
                    "program_id": f"{prefix}_{i:02d}",
                    "category_prefix": prefix,
                    "category": prefix.upper(),
                    "filename": f"{prefix}_{i:02d}.py",
                })
        return programs

    def test_total_coverage(self):
        programs = self._make_60_programs()
        splits = assign_splits(programs, seed=42)
        all_assigned = (
            splits["train"] + splits["dev"] + splits["val"] + splits["test"]
        )
        self.assertEqual(len(all_assigned), 60)

    def test_no_duplicates_across_splits(self):
        programs = self._make_60_programs()
        splits = assign_splits(programs, seed=42)
        all_assigned = (
            splits["train"] + splits["dev"] + splits["val"] + splits["test"]
        )
        self.assertEqual(len(all_assigned), len(set(all_assigned)))

    def test_all_programs_assigned(self):
        programs = self._make_60_programs()
        splits = assign_splits(programs, seed=42)
        all_ids = {p["program_id"] for p in programs}
        assigned_ids = set(
            splits["train"] + splits["dev"] + splits["val"] + splits["test"]
        )
        self.assertEqual(all_ids, assigned_ids)

    def test_approximate_split_ratios(self):
        programs = self._make_60_programs()
        splits = assign_splits(programs, seed=42)
        total = 60
        train_pct = len(splits["train"]) / total
        test_pct  = len(splits["test"])  / total
        # Allow ±10% tolerance for small-category adjustments
        self.assertAlmostEqual(train_pct, 0.50, delta=0.10)
        self.assertAlmostEqual(test_pct,  0.20, delta=0.10)

    def test_small_category_has_test_entry(self):
        """Categories with <5 programs must have ≥1 in test."""
        programs = self._make_60_programs()
        splits = assign_splits(programs, seed=42)
        test_set = set(splits["test"])
        # conc (3), parse (3) are small
        for prefix in ("conc", "parse"):
            in_test = [pid for pid in test_set if pid.startswith(prefix)]
            self.assertGreaterEqual(
                len(in_test), 1,
                msg=f"Category '{prefix}' has no programs in test split",
            )

    def test_deterministic_with_same_seed(self):
        programs = self._make_60_programs()
        splits1  = assign_splits(programs, seed=42)
        splits2  = assign_splits(programs, seed=42)
        self.assertEqual(splits1, splits2)

    def test_different_seeds_differ(self):
        programs = self._make_60_programs()
        splits1  = assign_splits(programs, seed=42)
        splits2  = assign_splits(programs, seed=99)
        self.assertNotEqual(splits1["train"], splits2["train"])

    def test_no_category_only_in_test(self):
        """After assignment, no category should appear exclusively in test."""
        programs = self._make_60_programs()
        splits   = assign_splits(programs, seed=42)
        found, issues = check_category_leakage(programs, splits)
        self.assertFalse(found, msg="\n".join(issues))

    def test_no_base_program_leakage(self):
        programs = self._make_60_programs()
        splits   = assign_splits(programs, seed=42)
        found, issues = check_base_program_leakage(splits)
        self.assertFalse(found, msg="\n".join(issues))


# ---------------------------------------------------------------------------
# run_audit integration (no filesystem)
# ---------------------------------------------------------------------------

class TestRunAuditIntegration(unittest.TestCase):

    def _minimal_manifest(self) -> dict:
        progs = _make_programs([
            ("sort_qs", "sort"),
            ("sort_ms", "sort"),
            ("graph_bfs", "graph"),
            ("graph_dfs", "graph"),
            ("ds_bst", "ds"),
            ("ds_ht",  "ds"),
        ])
        return {"programs": progs}

    def test_clean_audit_passes(self):
        manifest = self._minimal_manifest()
        split_assignment = {
            "splits": {
                "train": ["sort_qs", "graph_bfs", "ds_bst"],
                "dev":   ["sort_ms"],
                "val":   ["graph_dfs"],
                "test":  ["ds_ht"],
            }
        }
        report = run_audit(
            manifest, split_assignment,
            _PRESERVING_MANIFEST, _MUTATION_MANIFEST,
        )
        self.assertTrue(report["audit_passed"])
        self.assertFalse(report["base_program_leakage"])
        self.assertFalse(report["transformation_family_leakage"])
        self.assertFalse(report["category_leakage"])
        self.assertEqual(report["filename_collisions"], 0)

    def test_base_program_leakage_detected(self):
        manifest = self._minimal_manifest()
        split_assignment = {
            "splits": {
                "train": ["sort_qs", "ds_bst"],
                "dev":   [],
                "val":   [],
                "test":  ["sort_qs", "graph_bfs"],  # sort_qs in both train and test
            }
        }
        report = run_audit(
            manifest, split_assignment,
            _PRESERVING_MANIFEST, _MUTATION_MANIFEST,
        )
        self.assertFalse(report["audit_passed"])
        self.assertTrue(report["base_program_leakage"])

    def test_category_leakage_detected(self):
        manifest = self._minimal_manifest()
        split_assignment = {
            "splits": {
                "train": ["sort_qs", "sort_ms"],
                "dev":   [],
                "val":   [],
                "test":  ["graph_bfs"],   # graph only in test
            }
        }
        report = run_audit(
            manifest, split_assignment,
            _PRESERVING_MANIFEST, _MUTATION_MANIFEST,
        )
        self.assertFalse(report["audit_passed"])
        self.assertTrue(report["category_leakage"])

    def test_report_schema(self):
        manifest = self._minimal_manifest()
        split_assignment = {
            "splits": {
                "train": ["sort_qs", "graph_bfs"],
                "dev":   [],
                "val":   [],
                "test":  ["sort_ms", "graph_dfs"],
            }
        }
        report = run_audit(
            manifest, split_assignment,
            _PRESERVING_MANIFEST, _MUTATION_MANIFEST,
        )
        required_keys = {
            "base_program_leakage",
            "transformation_family_leakage",
            "category_leakage",
            "near_duplicate_count",
            "filename_collisions",
            "audit_passed",
            "issues",
        }
        self.assertEqual(required_keys, set(report.keys()))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
