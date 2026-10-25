"""Regression tests for defects found in the IEEE Access remediation.

1. stanford_gate._consistency matched check IDs by string prefix, so "C1"
   selected "C10"; C10 runs the gate as a subprocess => unbounded recursion.
2. external_bugsinpy computed an empty stdlib set on Python 3.9, silently
   changing which units are eligible depending on the interpreter.
"""
from __future__ import annotations

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "final"))


def test_gate_consistency_selects_only_exact_check_ids(monkeypatch):
    import consistency_check as cc
    import stanford_gate as sg

    called = []

    def make(label):
        def check():
            called.append(label.split()[0])
            return True, []
        return check

    monkeypatch.setattr(cc, "CHECKS", [(f"C{i} dummy", make(f"C{i} dummy"))
                                       for i in (1, 10, 2)])
    evidence, missing = sg._consistency(("C1",))
    assert called == ["C1"]
    assert len(evidence) == 1 and not missing


def test_gate_internal_consistency_never_runs_c10():
    """C10 re-runs the gate; internal_consistency must not include it."""
    import consistency_check as cc
    import stanford_gate as sg

    ran = []
    original = list(cc.CHECKS)
    try:
        cc.CHECKS[:] = [(label, (lambda l=label: (ran.append(l.split()[0]) or (True, []))))
                        for label, _ in original]
        sg.internal_consistency()
    finally:
        cc.CHECKS[:] = original
    assert "C10" not in ran
    assert set(ran) <= {"C1", "C2", "C3", "C4", "C7", "C8"}


def test_stdlib_set_is_populated_and_correct():
    import external_bugsinpy as eb

    for name in ("re", "os", "math", "json", "collections", "__future__"):
        assert name in eb._STDLIB, name
    for name in ("numpy", "pytest", "requests"):
        assert name not in eb._STDLIB, name


def test_stdlib_fallback_scans_interpreter_directory(monkeypatch):
    """Simulate Python 3.9 (no sys.stdlib_module_names)."""
    import external_bugsinpy as eb

    if hasattr(sys, "stdlib_module_names"):
        monkeypatch.delattr(sys, "stdlib_module_names")
    names = eb._stdlib_module_names()
    assert {"re", "os", "math", "json", "__future__"} <= names
    assert "numpy" not in names and "pytest" not in names


def test_c7_exception_list_is_exactly_the_known_historical_driver_traces():
    """C7 now inspects per-pair entries. The allow-list must equal the set of
    committed evaluated pairs that trace a (renamed) self-test driver, so it
    can neither hide a new defect nor go stale."""
    import json
    import consistency_check as cc

    found = set()
    for path in (REPO_ROOT / "artifacts" / "final").glob("pairs_*output_free*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if not row.get("evaluated"):
                continue
            for side in ("base_entry", "variant_entry"):
                if cc._is_scaffolding_entry((row.get(side) or "").split(":")[-1]):
                    found.add(row["pair_id"])
    assert found == set(cc.KNOWN_HISTORICAL_DRIVER_TRACES)
    assert len(found) == 11
    ok, problems = cc.check_output_free_protocol()
    assert ok, problems


def test_c7_rejects_a_new_driver_trace(tmp_path, monkeypatch):
    import consistency_check as cc

    final = tmp_path / "artifacts" / "final"
    final.mkdir(parents=True)
    (final / "pairs_x_output_free_v8.jsonl").write_text(
        '{"pair_id": "p1", "evaluated": true, "base_entry": "annotated:f", '
        '"variant_entry": "annotated:fn_test_f"}\n')
    monkeypatch.setattr(cc, "REPO_ROOT", tmp_path)
    ok, problems = cc.check_output_free_protocol()
    assert not ok and "fn_test_f" in problems[0]


def test_synthesised_inputs_do_not_alias_the_module_batteries():
    """An in-place sorter used to mutate LIST_BATTERY, so the second extraction
    in a process saw different inputs (sort_heapsort: 8771 cold, 8855 warm)."""
    from experiments.final import protocol as pr

    snapshot = [list(x) for x in pr.LIST_BATTERY]
    inputs = pr.synthesise_inputs(["list"])
    for item in inputs:
        item.append(999)
        item.reverse()
    assert [list(x) for x in pr.LIST_BATTERY] == snapshot


def test_repeated_extraction_is_order_independent():
    from experiments.final import extraction as ex

    path = str(REPO_ROOT / "benchmark/corpus/base_programs/sort_heapsort.py")
    counts = [ex.extract_program(path, {}, "output_free_v6").stats["n_events"]
              for _ in range(3)]
    assert len(set(counts)) == 1, counts
    if sys.version_info[:2] == (3, 13):
        # Committed cold-start record. Other interpreters legitimately differ
        # (3.9 gives 8024; see docs/current/PYTHON_VERSIONS.md).
        assert counts[0] == 8771
