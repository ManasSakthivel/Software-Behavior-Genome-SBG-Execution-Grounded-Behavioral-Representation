"""
experiments/v2/noise_floor.py
==============================
SAFEGUARD-6: Noise floor analysis for V2 dynamic genome extraction.

Predeclared stability criterion (set BEFORE any results are observed):
  STABILITY_CRITERION_CV_THRESHOLD = 0.05  (CV = std/mean > 5% = UNSTABLE)

Methodology:
  - Run 5 executions per program (n_runs=5)
  - Measure variance of each DynamicGenome field across runs
  - Compute: mean, std, CV (coefficient of variation)
  - Features with CV > 0.05 are flagged as unstable
  - Features may ONLY be excluded if they exceed this predeclared criterion
  - Features are NEVER excluded because they hurt test performance

Programs selected: first 2 alphabetically from each of 5 categories
(selection rule applied before any execution, not after seeing results)
Excluded: conc_* programs (non-deterministic threading)
"""
from __future__ import annotations

import json
import math
import pathlib
import sys
from typing import Any, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# ============================================================
# PREDECLARED STABILITY CRITERION — set before any results
# CV > 0.05 = unstable (5% coefficient of variation threshold)
# DO NOT CHANGE THIS AFTER SEEING RESULTS.
# ============================================================
STABILITY_CRITERION_CV_THRESHOLD: float = 0.05
N_RUNS: int = 5          # SAFEGUARD-6 minimum (also exposed as N_RUNS for protocol tests)
N_RUNS_REQUIRED: int = N_RUNS

from baselines.v2.b07_dynamic_v2 import V2_CANONICAL_INPUTS
from sbg.v2.execution.runner import SandboxRunner
from sbg.v2.execution.normalizer import TraceNormalizer
from sbg.v2.execution.genome import DynamicGenomeExtractor, DynamicGenome

_runner = SandboxRunner()
_normalizer = TraceNormalizer()
_extractor = DynamicGenomeExtractor()

ARTIFACT_PATH = REPO_ROOT / "artifacts" / "v2" / "NOISE_FLOOR_RESULTS.json"

# Programs to analyze (first 2 per category, alphabetical, pre-selected)
SAMPLE_PROGRAMS = [
    "benchmark/corpus/base_programs/api_rate_limiter.py",
    "benchmark/corpus/base_programs/binary_search.py",
    "benchmark/corpus/base_programs/bubble_sort.py",
    "benchmark/corpus/base_programs/calculator.py",
    "benchmark/corpus/base_programs/data_pipeline.py",
    "benchmark/corpus/base_programs/fibonacci.py",
    "benchmark/corpus/base_programs/hash_table.py",
    "benchmark/corpus/base_programs/insertion_sort.py",
    "benchmark/corpus/base_programs/lru_cache.py",
    "benchmark/corpus/base_programs/merge_sort.py",
]

# Public constant expected by test_noise_floor_protocol.py
MEASURED_FIELDS = [
    "coverage_size",
    "coverage_consistency",
    "exception_rate",
    "call_depth_mean",
    "call_depth_max",
    "trace_length_mean",
    "trace_length_std",
    "n_unique_functions",
]
# Internal alias kept for backwards compatibility
_DYN_FIELDS = MEASURED_FIELDS


def _load_entry_fn(path: str):
    """Load entry function from a Python source file."""
    import importlib.util
    import inspect
    import io
    import types as _types

    p = pathlib.Path(path)
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location("_sbg_noise_prog", str(p))
    if spec is None or spec.loader is None:
        return None
    mod = _types.ModuleType("_sbg_noise_prog")
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.stdout = old_stdout
        return None
    finally:
        sys.stdout = old_stdout

    for name in ("sort", "search", "run", "main", "solve", "process", "compute"):
        fn = getattr(mod, name, None)
        if callable(fn) and isinstance(fn, _types.FunctionType):
            return fn
    import inspect as _inspect
    for name, obj in _inspect.getmembers(mod, _inspect.isfunction):
        if not name.startswith("_") and getattr(obj, "__module__", None) == "_sbg_noise_prog":
            return obj
    return None


def _extract_genome_once(path: str) -> Optional[DynamicGenome]:
    """Extract DynamicGenome from a program file (single extraction)."""
    fn = _load_entry_fn(path)
    if fn is None:
        return None

    program_id = pathlib.Path(path).stem
    try:
        result = _runner.run(program_id, fn, V2_CANONICAL_INPUTS, n_runs=N_RUNS_REQUIRED, seed=42)
        nb = _normalizer.normalize(program_id, result.traces)
        return _extractor.extract(nb)
    except Exception:
        return None


def _compute_stats(values: List[float]) -> Dict[str, float]:
    """Compute mean, std, CV for a list of values."""
    n = len(values)
    if n == 0:
        return {"mean": 0.0, "std": 0.0, "cv": 0.0, "n": 0, "stable": True}
    mean = sum(values) / n
    if n > 1:
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    else:
        std = 0.0
    cv = std / abs(mean) if abs(mean) > 1e-10 else 0.0
    stable = cv <= STABILITY_CRITERION_CV_THRESHOLD
    return {
        "mean": round(mean, 6),
        "std": round(std, 6),
        "cv": round(cv, 6),
        "n": n,
        "stable": stable,
        "criterion": f"CV <= {STABILITY_CRITERION_CV_THRESHOLD}",
    }


def _get_field(genome: DynamicGenome, field: str) -> float:
    """Extract a numeric field from DynamicGenome."""
    return float(getattr(genome, field, 0.0))


def run_noise_floor() -> Dict[str, Any]:
    """
    Run the noise floor analysis.
    For each program, extract DynamicGenome N_RUNS_REQUIRED times.
    Measure variance of each field across extractions.
    """
    print(f"[NOISE_FLOOR] SAFEGUARD-6: n_runs={N_RUNS_REQUIRED}, threshold={STABILITY_CRITERION_CV_THRESHOLD}")
    print(f"[NOISE_FLOOR] Analyzing {len(SAMPLE_PROGRAMS)} programs")

    program_results = {}
    field_aggregates: Dict[str, List[float]] = {f: [] for f in _DYN_FIELDS}

    for prog_path in SAMPLE_PROGRAMS:
        prog_name = pathlib.Path(prog_path).stem
        abs_path = str(REPO_ROOT / prog_path)

        if not pathlib.Path(abs_path).exists():
            print(f"  [SKIP] {prog_name} — file not found")
            program_results[prog_name] = {"status": "FILE_NOT_FOUND"}
            continue

        print(f"  [RUN] {prog_name}")

        # Extract genome once (SandboxRunner uses n_runs internally for noise floor)
        genome = _extract_genome_once(abs_path)
        if genome is None:
            print(f"  [FAIL] {prog_name} — genome extraction failed")
            program_results[prog_name] = {"status": "EXTRACTION_FAILED"}
            continue

        # Collect field values
        field_values = {f: _get_field(genome, f) for f in _DYN_FIELDS}

        # Use SandboxRunner's built-in noise floor stats
        # Re-run separately to measure extraction variance
        fn = _load_entry_fn(abs_path)
        if fn is None:
            program_results[prog_name] = {"status": "LOAD_FAILED"}
            continue

        # Multiple independent extractions to measure genome variance
        genomes = []
        for run_i in range(N_RUNS_REQUIRED):
            try:
                result = _runner.run(prog_name, fn, V2_CANONICAL_INPUTS, n_runs=1, seed=42 + run_i)
                nb = _normalizer.normalize(prog_name, result.traces)
                g = _extractor.extract(nb)
                genomes.append(g)
            except Exception:
                pass

        if len(genomes) < 2:
            program_results[prog_name] = {"status": "INSUFFICIENT_RUNS", "n_runs": len(genomes)}
            continue

        # Compute per-field variance across independent extractions
        field_stats = {}
        for field in _DYN_FIELDS:
            vals = [_get_field(g, field) for g in genomes]
            stats = _compute_stats(vals)
            field_stats[field] = stats
            field_aggregates[field].extend(vals)

        noise_floor_stats = {
            "n_runs_actual": len(genomes),
            "n_runs_required": N_RUNS_REQUIRED,
            "fields": field_stats,
            "noise_floor_from_runner": genome.provenance.get("noise_floor_stats", {}),
            "non_deterministic_flags": genome.provenance.get("non_deterministic_flags", []),
        }

        unstable_fields = [f for f, s in field_stats.items() if not s["stable"]]

        program_results[prog_name] = {
            "status": "OK",
            "noise_floor_stats": noise_floor_stats,
            "unstable_fields": unstable_fields,
        }

        if unstable_fields:
            print(f"  [WARN] {prog_name}: unstable fields: {unstable_fields}")
        else:
            print(f"  [OK] {prog_name}: all fields stable (CV <= {STABILITY_CRITERION_CV_THRESHOLD})")

    # Cross-program aggregates
    aggregate_stats = {}
    for field in _DYN_FIELDS:
        vals = field_aggregates[field]
        if vals:
            aggregate_stats[field] = _compute_stats(vals)

    # Summary
    all_stable_fields = [f for f, s in aggregate_stats.items() if s.get("stable", True)]
    all_unstable_fields = [f for f, s in aggregate_stats.items() if not s.get("stable", True)]

    result = {
        "safeguard": "SAFEGUARD-6",
        "stability_criterion_cv_threshold": STABILITY_CRITERION_CV_THRESHOLD,
        "n_runs_required": N_RUNS_REQUIRED,
        "criterion_predeclared": True,
        "n_programs": len(SAMPLE_PROGRAMS),
        "program_results": program_results,
        "aggregate_field_stats": aggregate_stats,
        "stable_fields": all_stable_fields,
        "unstable_fields_aggregate": all_unstable_fields,
        "exclusion_policy": (
            "Features excluded ONLY if CV > predeclared threshold. "
            "Never excluded for degrading test performance."
        ),
        "summary": {
            "n_stable": len(all_stable_fields),
            "n_unstable": len(all_unstable_fields),
            "recommendation": (
                "EXCLUDE unstable fields from distance computation" if all_unstable_fields
                else "ALL fields stable — no exclusions recommended"
            ),
        },
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(result, indent=2))
    print(f"\n[NOISE_FLOOR] Results saved to {ARTIFACT_PATH}")
    return result


def _assess_stability(cv):
    """
    Return True if a feature is stable (CV <= STABILITY_CRITERION_CV_THRESHOLD).

    Uses STABILITY_CRITERION_CV_THRESHOLD (predeclared, never hardcoded).
    Called by measure_program_noise and _compute_stats.
    """
    return cv <= STABILITY_CRITERION_CV_THRESHOLD


def measure_program_noise(prog_path: str) -> Dict[str, Any]:
    """
    Measure noise floor for a single program.

    Runs N_RUNS independent genome extractions and computes per-field
    variance statistics. Returns a dict with 'fields', 'unstable_fields',
    'n_runs_actual', and 'status'.
    """
    abs_path = str(REPO_ROOT / prog_path) if not pathlib.Path(prog_path).is_absolute() else prog_path
    prog_name = pathlib.Path(abs_path).stem

    fn = _load_entry_fn(abs_path)
    if fn is None:
        return {"status": "LOAD_FAILED", "prog": prog_name}

    genomes = []
    for run_i in range(N_RUNS):
        try:
            result = _runner.run(prog_name, fn, V2_CANONICAL_INPUTS, n_runs=1, seed=42 + run_i)
            nb = _normalizer.normalize(prog_name, result.traces)
            g = _extractor.extract(nb)
            genomes.append(g)
        except Exception:
            pass

    if len(genomes) < 2:
        return {"status": "INSUFFICIENT_RUNS", "n_runs_actual": len(genomes)}

    field_stats = {}
    for field in MEASURED_FIELDS:
        vals = [_get_field(g, field) for g in genomes]
        stats = _compute_stats(vals)
        field_stats[field] = stats

    unstable_fields = [f for f, s in field_stats.items() if not _assess_stability(s["cv"])]
    return {
        "status": "OK",
        "prog": prog_name,
        "n_runs_actual": len(genomes),
        "fields": field_stats,
        "unstable_fields": unstable_fields,
    }


def run() -> Dict[str, Any]:
    """Entry point alias for run_noise_floor() — expected by test_noise_floor_protocol.py."""
    return run_noise_floor()


if __name__ == "__main__":
    results = run_noise_floor()
    print(f"\n[NOISE_FLOOR] Stable fields: {results['stable_fields']}")
    print(f"[NOISE_FLOOR] Unstable fields: {results['unstable_fields_aggregate']}")
