"""
Tests for sbg.serialization and sbg.cli
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sbg.serialization import GenomeBundle, GenomeBundleSerializer, ProvenanceTracker


def _sample_bundle() -> GenomeBundle:
    return GenomeBundle(
        program_id="test_prog",
        source_hash="abc12345",
        extraction_timestamp="2025-01-01T00:00:00+00:00",
        genome_version="1.0",
        genomes={"CONTROL": {"cyclomatic_complexity": 3, "branch_count": 2}},
        provenance={"source_file": "test.py", "n_traces": 5},
        metadata={"source_lines": 42},
    )


class TestGenomeBundleSerializer(unittest.TestCase):

    def test_to_dict_has_required_keys(self):
        bundle = _sample_bundle()
        d = GenomeBundleSerializer.to_dict(bundle)
        for key in ["program_id", "source_hash", "extraction_timestamp",
                    "genome_version", "genomes", "provenance", "metadata"]:
            self.assertIn(key, d)

    def test_to_json_is_valid_json(self):
        bundle = _sample_bundle()
        j = GenomeBundleSerializer.to_json(bundle)
        parsed = json.loads(j)
        self.assertIsInstance(parsed, dict)

    def test_from_dict_roundtrip(self):
        bundle = _sample_bundle()
        d = GenomeBundleSerializer.to_dict(bundle)
        restored = GenomeBundleSerializer.from_dict(d)
        self.assertEqual(restored.program_id, bundle.program_id)
        self.assertEqual(restored.source_hash, bundle.source_hash)
        self.assertEqual(restored.genomes, bundle.genomes)

    def test_from_json_roundtrip(self):
        bundle = _sample_bundle()
        j = GenomeBundleSerializer.to_json(bundle)
        restored = GenomeBundleSerializer.from_json(j)
        self.assertEqual(restored.program_id, bundle.program_id)

    def test_save_and_load(self):
        bundle = _sample_bundle()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            GenomeBundleSerializer.save(bundle, path)
            loaded = GenomeBundleSerializer.load(path)
            self.assertEqual(loaded.program_id, bundle.program_id)
            self.assertEqual(loaded.genomes, bundle.genomes)
        finally:
            os.unlink(path)

    def test_roundtrip_valid(self):
        bundle = _sample_bundle()
        self.assertTrue(GenomeBundleSerializer.roundtrip_valid(bundle))

    def test_from_dict_missing_optional_fields(self):
        """from_dict must handle missing optional fields gracefully."""
        d = {"program_id": "x", "source_hash": "y", "extraction_timestamp": "t"}
        bundle = GenomeBundleSerializer.from_dict(d)
        self.assertEqual(bundle.program_id, "x")
        self.assertEqual(bundle.genomes, {})
        self.assertEqual(bundle.provenance, {})

    def test_json_contains_genomes(self):
        bundle = _sample_bundle()
        j = GenomeBundleSerializer.to_json(bundle)
        parsed = json.loads(j)
        self.assertIn("CONTROL", parsed["genomes"])

    def test_save_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "subdir", "nested", "genome.json")
            GenomeBundleSerializer.save(_sample_bundle(), path)
            self.assertTrue(os.path.exists(path))

    def test_metadata_preserved(self):
        bundle = _sample_bundle()
        d = GenomeBundleSerializer.to_dict(bundle)
        self.assertEqual(d["metadata"]["source_lines"], 42)


class TestProvenanceTracker(unittest.TestCase):

    def test_required_fields_present(self):
        prov = ProvenanceTracker.create_provenance("test.py", inputs=["1", "2"], n_traces=10)
        for field in ["source_file", "inputs_used", "n_traces", "tool_versions", "timestamp"]:
            self.assertIn(field, prov)

    def test_tool_versions_has_python(self):
        prov = ProvenanceTracker.create_provenance("test.py")
        self.assertIn("python", prov["tool_versions"])

    def test_tool_versions_has_sbg(self):
        prov = ProvenanceTracker.create_provenance("test.py")
        self.assertIn("sbg", prov["tool_versions"])

    def test_inputs_recorded(self):
        prov = ProvenanceTracker.create_provenance("x.py", inputs=["42", "[1,2]"])
        self.assertEqual(prov["inputs_used"], ["42", "[1,2]"])

    def test_flags_recorded(self):
        prov = ProvenanceTracker.create_provenance("x.py", flags={"static_only": True})
        self.assertTrue(prov["extraction_flags"]["static_only"])


class TestCLIExtract(unittest.TestCase):

    def _corpus_file(self):
        repo = Path(__file__).resolve().parents[1]
        return str(repo / "benchmark" / "corpus" / "base_programs" / "sort_insertion_sort.py")

    def test_extract_produces_valid_json(self):
        from sbg.cli import main
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_path = f.name
        try:
            rc = main(["extract", self._corpus_file(), "--output", out_path])
            self.assertEqual(rc, 0)
            with open(out_path) as f:
                data = json.load(f)
            self.assertIn("program_id", data)
            self.assertIn("genomes", data)
        finally:
            os.unlink(out_path)

    def test_extract_missing_file_returns_nonzero(self):
        from sbg.cli import main
        rc = main(["extract", "/nonexistent/path.py"])
        self.assertNotEqual(rc, 0)

    def test_validate_valid_bundle(self):
        from sbg.cli import main
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_path = f.name
        try:
            main(["extract", self._corpus_file(), "--output", out_path])
            rc = main(["validate", out_path])
            self.assertEqual(rc, 0)
        finally:
            os.unlink(out_path)

    def test_compare_two_bundles(self):
        from sbg.cli import main
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fa, \
             tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fb:
            pa, pb = fa.name, fb.name
        try:
            main(["extract", self._corpus_file(), "--output", pa])
            main(["extract", self._corpus_file(), "--output", pb])
            import io
            from contextlib import redirect_stdout
            captured = io.StringIO()
            with redirect_stdout(captured):
                rc = main(["compare", pa, pb])
            self.assertEqual(rc, 0)
            result = json.loads(captured.getvalue())
            self.assertIn("total_distance", result)
            self.assertGreaterEqual(result["total_distance"], 0.0)
            self.assertLessEqual(result["total_distance"], 1.0)
        finally:
            os.unlink(pa)
            os.unlink(pb)


if __name__ == "__main__":
    unittest.main(verbosity=2)
