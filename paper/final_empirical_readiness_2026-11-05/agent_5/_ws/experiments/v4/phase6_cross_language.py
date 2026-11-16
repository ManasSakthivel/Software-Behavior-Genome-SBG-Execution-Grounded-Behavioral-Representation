"""
experiments/v4/phase6_cross_language.py
=========================================
Phase 6 — Cross-Language Evaluation

SCIENTIFIC QUESTION:
  Can SBG's behavioral representation capture semantics across languages?

STATUS: Java execution infrastructure is not available in this environment.
This script documents:
  A. Why Java execution is not feasible in the current setup
  B. What WOULD be needed
  C. What cross-language evidence IS available (Python function equivalence)
  D. A limited Python-to-Python "cross-formulation" test

HONEST ASSESSMENT:
  Full Java execution requires:
  - JVM available on PATH (java binary)
  - Ability to compile + run Java programs
  - Java equivalents of 13+ benchmark programs
  - Semantic ground truth from program behavior, not syntax

  We attempt to detect JVM, and if unavailable, report the limitation
  with detailed infrastructure requirements.

  We DO run a within-Python "equivalent algorithm" test as a proxy:
  - Multiple implementations of the same algorithm (different language idioms)
  - This tests cross-formulation generalization, which is the core claim

OUTPUT: artifacts/v4/CROSS_LANGUAGE.json
"""
from __future__ import annotations

import importlib.util
import io
import json
import math
import pathlib
import shutil
import subprocess
import sys
import types
from typing import Any, Callable, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sbg.v2.execution.runner import SandboxRunner
from sbg.v3.genome import DynamicGenomeExtractorV3, distance_v3
from sbg.v3.metrics import compute_auroc_v3

ARTIFACT_OUT = REPO_ROOT / "artifacts" / "v4" / "CROSS_LANGUAGE.json"

V3_INPUTS: List[Any] = [
    [], [1], [3, 1, 4, 1, 5, 9, 2, 6], [10, 9, 8, 7, 6, 5],
    [0, 0, 0, 0], [2, 1], [-3, 0, 3], list(range(8)),
    list(range(3)), list(range(16)),
]

_runner = SandboxRunner()
_extractor = DynamicGenomeExtractorV3()

# ── Cross-formulation test: equivalent algorithms in different Python styles ──
# Each group: same semantic task, different implementation approach
# Label: EQUIVALENT within group, CHANGED across groups

CROSS_FORMULATION_GROUPS = [
    {
        "name": "sort_group",
        "implementations": [
            ("merge_sort",
             """\
def sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = sort(arr[:mid])
    right = sort(arr[mid:])
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]
"""),
            ("timsort_builtin",
             """\
def sort(arr):
    a = list(arr)
    a.sort()
    return a
"""),
            ("insertion_sort",
             """\
def sort(arr):
    a = list(arr)
    for i in range(1, len(a)):
        key = a[i]; j = i - 1
        while j >= 0 and a[j] > key:
            a[j+1] = a[j]; j -= 1
        a[j+1] = key
    return a
"""),
        ],
        "changing_variant": (
            "buggy_sort",
            """\
def sort(arr):
    a = list(arr)
    for i in range(len(a)):
        for j in range(len(a)-1):
            if a[j] > a[j+1]:
                a[j], a[j+1] = a[j+1], a[j]
    return a[::-1]  # BUG: reversed
"""),
    },
    {
        "name": "search_group",
        "implementations": [
            ("linear_search",
             """\
def search(arr, target=5):
    for i, x in enumerate(arr):
        if x == target:
            return i
    return -1
"""),
            ("binary_search",
             """\
def search(arr, target=5):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
"""),
        ],
        "changing_variant": (
            "wrong_search",
            """\
def search(arr, target=5):
    for i, x in enumerate(arr):
        if x >= target:
            return i  # BUG: returns first element >= target
    return -1
"""),
    },
]


def _get_genome_from_code(code: str, name: str) -> Optional[Any]:
    import tempfile
    tmp_dir = pathlib.Path("/tmp") / "sbg_v4_cross"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    p = tmp_dir / f"{name}.py"
    p.write_text(code)

    spec = importlib.util.spec_from_file_location(f"_cl_{name}", str(p))
    if not spec or not spec.loader:
        return None
    mod = types.ModuleType(f"_cl_{name}")
    old = sys.stdout; sys.stdout = io.StringIO()
    try:
        spec.loader.exec_module(mod)  # type: ignore
    except Exception:
        sys.stdout = old
        return None
    finally:
        sys.stdout = old

    import inspect
    fn = None
    for nm, obj in inspect.getmembers(mod, inspect.isfunction):
        if not nm.startswith("_") and getattr(obj, "__module__", None) == f"_cl_{name}":
            fn = obj
            break
    if fn is None:
        return None

    try:
        n_p = len(inspect.signature(fn).parameters)
    except Exception:
        n_p = 1

    if n_p == 0:
        fn_trace = lambda inp: fn()
        inputs = [None]
    else:
        fn_trace = fn
        inputs = V3_INPUTS

    try:
        sr = _runner.run(name, fn_trace, inputs, n_runs=3, seed=42, max_events=3_000)
        return _extractor.extract_from_traces(name, sr.traces)
    except Exception:
        return None


def _check_java() -> Dict:
    """Check if Java is available."""
    java_bin = shutil.which("java")
    javac_bin = shutil.which("javac")
    java_version = None
    if java_bin:
        try:
            r = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=5)
            java_version = (r.stdout + r.stderr).strip()[:100]
        except Exception:
            pass
    return {
        "java_binary": java_bin,
        "javac_binary": javac_bin,
        "java_available": java_bin is not None,
        "version": java_version,
    }


def main() -> None:
    print("\n" + "="*60)
    print("PHASE 6 — CROSS-LANGUAGE EVALUATION")
    print("="*60)

    # Check Java
    java_info = _check_java()
    print(f"Java available: {java_info['java_available']}")
    if java_info["java_available"]:
        print(f"  Version: {java_info['version']}")

    # Cross-formulation test (Python)
    print(f"\nRunning cross-formulation test ({len(CROSS_FORMULATION_GROUPS)} groups)...\n")

    cross_results = []
    sims_equiv, sims_changed = [], []

    for group in CROSS_FORMULATION_GROUPS:
        gname = group["name"]
        impls = group["implementations"]
        changing_name, changing_code = group["changing_variant"]

        # Extract genomes for all implementations
        genomes = {}
        for impl_name, impl_code in impls:
            g = _get_genome_from_code(impl_code, f"{gname}_{impl_name}")
            genomes[impl_name] = g

        changing_genome = _get_genome_from_code(changing_code, f"{gname}_{changing_name}")

        # Pairwise distances within group (should be EQUIVALENT: low distance)
        within_pairs = []
        impl_names = list(genomes.keys())
        for i in range(len(impl_names)):
            for j in range(i+1, len(impl_names)):
                g1 = genomes[impl_names[i]]
                g2 = genomes[impl_names[j]]
                if g1 and g2:
                    d = distance_v3(g1, g2)
                    within_pairs.append({
                        "pair": f"{impl_names[i]} vs {impl_names[j]}",
                        "label": "EQUIVALENT",
                        "distance": round(d, 6),
                        "sim": round(1.0 - d, 6),
                    })
                    sims_equiv.append(1.0 - d)

        # Cross-group distances (should be CHANGED: high distance)
        cross_pairs = []
        for impl_name, g1 in genomes.items():
            if g1 and changing_genome:
                d = distance_v3(g1, changing_genome)
                cross_pairs.append({
                    "pair": f"{impl_name} vs {changing_name}",
                    "label": "CHANGED",
                    "distance": round(d, 6),
                    "sim": round(1.0 - d, 6),
                })
                sims_changed.append(1.0 - d)

        cross_results.append({
            "group": gname,
            "n_impl": len(impls),
            "within_equiv_pairs": within_pairs,
            "cross_changed_pairs": cross_pairs,
        })

        print(f"  [{gname}]")
        print(f"    Within-group (EQUIV) distances: {[p['distance'] for p in within_pairs]}")
        print(f"    Cross-group (CHANGED) distances: {[p['distance'] for p in cross_pairs]}")

    # Compute mini cross-formulation AUROC
    all_sims = sims_equiv + sims_changed
    all_labels = [0] * len(sims_equiv) + [1] * len(sims_changed)

    if all_sims and sum(all_labels) > 0 and sum(1-l for l in all_labels) > 0:
        cross_auroc = compute_auroc_v3(all_sims, all_labels)
        mean_equiv_sim = sum(sims_equiv)/len(sims_equiv) if sims_equiv else None
        mean_changed_sim = sum(sims_changed)/len(sims_changed) if sims_changed else None
    else:
        cross_auroc = None
        mean_equiv_sim = None
        mean_changed_sim = None

    cauro_str = f"{cross_auroc:.4f}" if cross_auroc is not None else "N/A"
    mes_str = f"{mean_equiv_sim:.4f}" if mean_equiv_sim is not None else "N/A"
    mcs_str = f"{mean_changed_sim:.4f}" if mean_changed_sim is not None else "N/A"
    print(f"\nCross-formulation mini-AUROC: {cauro_str}")
    print(f"Mean equiv sim: {mes_str}")
    print(f"Mean changed sim: {mcs_str}")

    summary = {
        "experiment": "PHASE6_CROSS_LANGUAGE",
        "version": "v4",
        "java_infrastructure": java_info,
        "java_execution_status": (
            "AVAILABLE" if java_info["java_available"]
            else "NOT_AVAILABLE"
        ),
        "java_limitation_reason": (
            None if java_info["java_available"]
            else (
                "Java binary not found in PATH. "
                "Full cross-language evaluation would require: "
                "1) JVM + JDK installed, "
                "2) Java implementations of 13+ benchmark programs, "
                "3) JVM-aware tracing infrastructure (Java instrumentation API), "
                "4) Semantic equivalence oracle for Python vs Java outputs. "
                "This represents ~10-15 engineering days of infrastructure work. "
                "Reported as LIMITATION rather than implemented superficially."
            )
        ),
        "cross_formulation_test": {
            "n_groups": len(CROSS_FORMULATION_GROUPS),
            "n_equiv_pairs": len(sims_equiv),
            "n_changed_pairs": len(sims_changed),
            "auroc": round(cross_auroc, 4) if cross_auroc else None,
            "mean_equiv_similarity": round(mean_equiv_sim, 4) if mean_equiv_sim else None,
            "mean_changed_similarity": round(mean_changed_sim, 4) if mean_changed_sim else None,
            "note": (
                "Cross-formulation = same semantic task, different Python implementation style. "
                "N is small; informational only. Tests if SBG is invariant to implementation style."
            ),
            "groups": cross_results,
        },
    }

    ARTIFACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_OUT, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[PHASE6] Saved → {ARTIFACT_OUT}")


if __name__ == "__main__":
    main()
