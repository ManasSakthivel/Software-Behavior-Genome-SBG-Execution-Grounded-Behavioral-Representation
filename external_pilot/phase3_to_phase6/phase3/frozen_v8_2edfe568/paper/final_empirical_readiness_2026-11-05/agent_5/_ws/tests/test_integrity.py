"""Scientific-integrity tests.

Each of these asserts a property whose violation produced a wrong claim in an
earlier release. They are cheap, they run in CI, and they fail the build rather
than producing a warning nobody reads.
"""
from __future__ import annotations

import ast
import itertools
import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "benchmark" / "benchmark_manifest.json"
PROVENANCE = REPO_ROOT / "artifacts" / "final" / "ARTIFACT_PROVENANCE.json"
LEAK_AUDIT = REPO_ROOT / "artifacts" / "final" / "OUTPUT_ORACLE_LEAK_AUDIT.json"
VALIDITY_AUDIT = REPO_ROOT / "artifacts" / "final" / "BENCHMARK_VALIDITY_AUDIT.json"


def load(path: pathlib.Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path.relative_to(REPO_ROOT)} not generated yet")
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Benchmark manifest and split integrity
# ---------------------------------------------------------------------------

class TestManifest:
    def test_manifest_exists(self):
        assert MANIFEST.exists(), "run `make manifest`"

    def test_corpus_accounting_closes(self):
        corpus = load(MANIFEST)["corpus"]
        assert (corpus["n_assigned_to_splits"] + corpus["n_unassigned"]
                == corpus["n_files_on_disk"])

    def test_unassigned_programs_are_named(self):
        # Four corpus files take part in no experiment. Silently leaving them
        # in the directory is how "99 programs" got into the README.
        corpus = load(MANIFEST)["corpus"]
        assert len(corpus["unassigned_programs"]) == corpus["n_unassigned"]

    def test_pair_counts_sum(self):
        for name, block in load(MANIFEST)["datasets"].items():
            summed = sum(s["nominal_pairs"] for s in block["splits"].values())
            assert summed == block["totals"]["nominal_pairs"], name

    def test_labels_partition_each_split(self):
        for name, block in load(MANIFEST)["datasets"].items():
            for split, s in block["splits"].items():
                assert s["changed_pairs"] + s["equivalent_pairs"] == s["nominal_pairs"], \
                    f"{name}/{split}"


class TestSplitIsolation:
    """Program-level disjointness. A base program in two splits would leak the
    test set into training, and a derived variant leaking would be worse."""

    def test_all_six_intersections_are_empty(self):
        for name, block in load(MANIFEST)["datasets"].items():
            for key, shared in block["split_program_intersections"].items():
                assert shared == [], f"{name}: {key} shares {shared}"

    def test_intersection_count_is_six(self):
        for name, block in load(MANIFEST)["datasets"].items():
            splits = list(block["splits"])
            expected = len(list(itertools.combinations(splits, 2)))
            assert len(block["split_program_intersections"]) == expected, name

    def test_no_variant_file_is_shared_between_splits(self):
        seen: dict = {}
        for split in ("train", "dev", "val", "test"):
            path = REPO_ROOT / "benchmark" / "datasets" / f"pairs_{split}.jsonl"
            if not path.exists():
                continue
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                pair = json.loads(line)
                previous = seen.get(pair["variant_path"])
                assert previous in (None, split), \
                    f"{pair['variant_path']} appears in {previous} and {split}"
                seen[pair["variant_path"]] = split

    def test_every_pair_uses_a_base_program_from_its_own_split(self):
        assignment = json.loads(
            (REPO_ROOT / "benchmark" / "splits" / "split_assignment.json").read_text())
        for split, programs in assignment["splits"].items():
            path = REPO_ROOT / "benchmark" / "datasets" / f"pairs_{split}.jsonl"
            if not path.exists():
                continue
            allowed = set(programs)
            for line in path.read_text().splitlines():
                if line.strip():
                    assert json.loads(line)["base_id"] in allowed


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

class TestProvenance:
    def test_every_registered_artifact_has_evidence(self):
        for relative, record in load(PROVENANCE)["artifacts"].items():
            assert record.get("evidence"), f"{relative} has no provenance evidence"

    def test_non_measured_artifacts_name_their_replacement(self):
        for relative, record in load(PROVENANCE)["artifacts"].items():
            if record["status"] in ("PARTIALLY_SYNTHETIC", "NON_REPRODUCING",
                                    "SUPERSEDED", "DERIVED"):
                assert record.get("superseded_by"), \
                    f"{relative} is {record['status']} but names no replacement"

    def test_synthetic_flag_logic_is_conjunctive(self):
        # The generator used to set scores_are_real=True when a single feature
        # had real scores. Guard the fixed expression so it cannot regress.
        source = (REPO_ROOT / "experiments" / "v5"
                  / "incremental_info_framework.py").read_text()
        assert '"scores_are_real":    bool(scores_are_real and not synthetic_features)' \
            in source
        assert '"synthetic_features": synthetic_features' in source


# ---------------------------------------------------------------------------
# Output-free constraint
# ---------------------------------------------------------------------------

class TestOutputFreeConstraint:
    def test_leak_audit_records_the_published_violation(self):
        summary = load(LEAK_AUDIT)["corpus_summary"]
        assert summary["n_entry_traces_assertions"] > 0, (
            "the audit must keep recording the published protocol's violation; "
            "if this becomes 0 the finding has been silently dropped")

    def test_output_free_protocol_excludes_scaffolding(self):
        from experiments.final.protocol import _is_scaffolding, eligible_candidates
        assert _is_scaffolding("test_heapsort")
        assert _is_scaffolding("main")
        assert _is_scaffolding("_helper")
        assert not _is_scaffolding("heapsort")

        source = (REPO_ROOT / "benchmark" / "corpus"
                  / "base_programs" / "sort_heapsort.py").read_text()
        names = [name for name, _, _ in eligible_candidates(ast.parse(source))]
        assert names, "sort_heapsort should expose an API function"
        assert not any(n.startswith("test_") for n in names)

    def test_output_free_run_selected_no_self_test_driver(self):
        path = (REPO_ROOT / "artifacts" / "final"
                / "programs_test_output_free_v6.json")
        if not path.exists():
            pytest.skip("output-free protocol has not been run")
        for program, record in json.loads(path.read_text())["programs"].items():
            entry = (record.get("entry_discovery") or "").split(":")[-1]
            assert not entry.startswith("test_"), f"{program} traced {entry}"

    def test_distance_functions_do_not_read_return_values(self):
        import inspect

        from sbg.v3.genome import distance_v3
        from experiments.final.extraction import score_pair
        for fn in (distance_v3, score_pair):
            source = inspect.getsource(fn)
            body = source.split('"""')[2] if source.count('"""') >= 2 else source
            for forbidden in ("return_value", "output_divergence", "expected_output",
                              "stdout"):
                assert forbidden not in body, f"{fn.__name__} reads {forbidden}"


# ---------------------------------------------------------------------------
# Benchmark validity
# ---------------------------------------------------------------------------

class TestBenchmarkValidity:
    def test_audit_covers_every_pair(self):
        audit = load(VALIDITY_AUDIT)
        manifest = load(MANIFEST)["datasets"]["v5_published"]
        assert len(audit["pairs"]) == manifest["totals"]["nominal_pairs"]

    def test_corrected_benchmark_is_clean(self):
        path = REPO_ROOT / "artifacts" / "final" / "BENCHMARK_VALIDITY_AUDIT_V6.json"
        if not path.exists():
            pytest.skip("v6 benchmark not generated")
        for split, block in json.loads(path.read_text())["summary"].items():
            assert block["n_uncompilable"] == 0, f"{split} has uncompilable variants"
            assert block["n_changed_unobservable"] == 0, \
                f"{split} has CHANGED pairs whose mutation is unreachable"

    def test_generated_variants_compile(self):
        directory = REPO_ROOT / "benchmark" / "datasets" / "v6" / "variants"
        if not directory.exists():
            pytest.skip("v6 benchmark not generated")
        for path in sorted(directory.rglob("*.py")):
            compile(path.read_text(), str(path), "exec")

    def test_sp3_never_emits_return_outside_a_function(self):
        from benchmark.transformations.preserving.transformations.sp3_dead_code_insert \
            import DeadCodeInsertTransformation
        transformation = DeadCodeInsertTransformation()
        corpus = sorted((REPO_ROOT / "benchmark" / "corpus"
                         / "base_programs").glob("*.py"))
        for path in corpus[:12]:
            source = path.read_text()
            for seed in (0, 1, 2):
                compile(transformation.apply(source, seed), str(path), "exec")

    def test_sp3_validate_uses_compile_not_parse(self):
        from benchmark.transformations.preserving.transformations.sp3_dead_code_insert \
            import DeadCodeInsertTransformation
        # ast.parse accepts a module-level return; only compile rejects it.
        # That is exactly how 103 corrupt variants passed validation.
        broken = "def f():\n    pass\nreturn None\n"
        assert not DeadCodeInsertTransformation().validate("def f():\n    pass\n", broken)

    def test_mutations_stay_out_of_scaffolding(self):
        from benchmark.transformations.mutations.mutator import MutatorRegistry
        source = (REPO_ROOT / "benchmark" / "corpus" / "base_programs"
                  / "sort_counting_sort.py").read_text()
        for mutation in ("SC-2", "SC-5", "SC-13"):
            mutated = MutatorRegistry.get(mutation).apply(source, seed=0, mutation_site=0)
            assert "__name__ != '__main__'" not in mutated, (
                f"{mutation} mutated the __main__ guard, which changes no behaviour "
                "but makes the file run its own test driver on import")

    def test_threshold_is_a_fixed_constant(self):
        from experiments.final.hard_negative_evaluation import TAU_STAR as hard_tau
        from experiments.final.regression_evaluation import TAU_STAR as regression_tau
        assert hard_tau == regression_tau == 0.08


# ---------------------------------------------------------------------------
# Source compiles on the minimum supported Python
# ---------------------------------------------------------------------------

class TestSourceCompiles:
    """Every first-party source file must compile on the interpreter running the
    tests. CI runs 3.9 and 3.13.

    This exists because a clean-checkout run on 3.9 found an f-string containing
    a backslash in `make_figures.py` -- legal from 3.12, a SyntaxError before it.
    It never showed up in development because development used 3.13, and the
    figure step is not exercised by any other test.
    """

    # Generated program variants are benchmark *data*, not source. 104 of them
    # do not compile, all from the same SP-3 scope bug: 103 in
    # benchmark/datasets/ (counted by the validity audit) and one V2-era leftover
    # at benchmark/regression/controls/ctrl_reg_018_SP3.py, which no current
    # experiment reads.
    DATA_MARKERS = ("datasets/variants", "benchmark/regression/controls")

    def _source_files(self):
        for path in sorted(REPO_ROOT.rglob("*.py")):
            relative = path.relative_to(REPO_ROOT).as_posix()
            if any(part in (".venv", "__pycache__", ".git") or part.startswith(".venv")
                   for part in path.parts):
                continue
            if any(marker in relative for marker in self.DATA_MARKERS):
                continue
            yield path

    def test_all_first_party_source_compiles(self):
        failures = []
        for path in self._source_files():
            try:
                compile(path.read_text(), str(path), "exec")
            except SyntaxError as exc:
                failures.append(f"{path.relative_to(REPO_ROOT)}: {exc.msg} "
                                f"(line {exc.lineno})")
        assert not failures, "source does not compile:\n" + "\n".join(failures)

    def test_figure_and_table_generators_are_importable(self):
        # The two steps a `make check` run exercises last, and therefore the two
        # most likely to carry an unnoticed version incompatibility.
        import importlib
        for module in ("experiments.final.make_figures",
                       "experiments.final.make_tables",
                       "experiments.final.consistency_check",
                       "experiments.final.protocol",
                       "sbg.statistics"):
            importlib.import_module(module)
