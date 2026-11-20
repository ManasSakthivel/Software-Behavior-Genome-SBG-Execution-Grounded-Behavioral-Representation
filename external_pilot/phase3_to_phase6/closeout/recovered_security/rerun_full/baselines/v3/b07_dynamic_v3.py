"""
baselines/v3/b07_dynamic_v3.py
================================
Baseline B07-v3: Dynamic SBG V3.

Uses v3 DynamicGenomeV3 with enriched behavioral features:
  - call_transition_bigrams (order-sensitive)
  - input_sensitivity_score
  - call_depth_variance
  - hot_path_stability
  - exception_causality_hash

Plus all v2 features preserved.

Uses the v3 tie-aware AUROC (sbg.v3.metrics.compute_auroc_v3).
Uses the v3 distance function (sbg.v3.genome.distance_v3).

Protocol
--------
Same as b07_dynamic_v2.py:
1. Load program from path
2. Discover entry function
3. Extract DynamicGenomeV3 using V3 canonical inputs
4. Compute distance_v3 → similarity
5. Score DEV → select threshold → evaluate TEST
"""
from __future__ import annotations

import importlib.util
import inspect
import io
import json
import pathlib
import sys
import types
from typing import Any, Callable, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sbg.v2.execution.runner import SandboxRunner
from sbg.v3.genome import DynamicGenomeExtractorV3, DynamicGenomeV3, distance_v3
from sbg.v3.metrics import (
    compute_auroc_v3, compute_metrics_v3,
    bootstrap_auroc_ci, permutation_test_auroc
)

ARTIFACT_DIR = str(REPO_ROOT / "artifacts" / "v3" / "B07")

# V3 canonical inputs: V2 inputs + additional boundary conditions
V3_CANONICAL_INPUTS: List[Any] = [
    [],
    [1],
    [3, 1, 4, 1, 5, 9, 2, 6],
    [10, 9, 8, 7, 6, 5],
    [0, 0, 0, 0],
    [2, 1],
    [-3, 0, 3],
    list(range(8)),
    # Additional v3 inputs for better SC-3 mutation detection
    list(range(1)),       # minimal
    list(range(3)),       # three elements
    list(range(16)),      # power-of-2 boundary
]

_runner = SandboxRunner()
_extractor = DynamicGenomeExtractorV3()

# Cache to avoid re-running programs for multiple pairs
_genome_cache_v3: Dict[str, Optional[DynamicGenomeV3]] = {}


def _load_entry_fn(source_path: str) -> Optional[Callable]:
    """Load a Python source file and auto-discover the entry function."""
    path = pathlib.Path(source_path)
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("_sbg_b07v3_prog", str(path))
    if spec is None or spec.loader is None:
        return None
    mod = types.ModuleType("_sbg_b07v3_prog")
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except Exception:
        sys.stdout = old_stdout
        return None
    finally:
        sys.stdout = old_stdout

    # Priority order for entry function discovery
    for priority_name in ("sort", "search", "run", "main", "solve", "process", "compute",
                          "encode", "decode", "parse", "validate", "execute"):
        fn = getattr(mod, priority_name, None)
        if callable(fn) and isinstance(fn, types.FunctionType):
            return fn

    # Fall back to call-graph-root selector (v3 fix for SP-2 entry-fn bug)
    # Call-graph root: top-level function that is NOT called by other top-level functions
    call_graph_root = _find_call_graph_root(mod)
    if call_graph_root is not None:
        return call_graph_root

    # Final fallback: first public top-level function
    for name, obj in inspect.getmembers(mod, inspect.isfunction):
        if not name.startswith("_"):
            if getattr(obj, "__module__", None) == "_sbg_b07v3_prog":
                return obj

    return None


def _find_call_graph_root(mod: types.ModuleType) -> Optional[Callable]:
    """
    Find the call-graph root function: a top-level function that is not
    called by any other top-level function in the module.

    This is the v3 fix for the SP-2 entry-function discovery bug (forensic
    audit finding: alphabetical fallback selects wrong function after rename).

    A call-graph root is more semantically meaningful as the entry point
    because it is the "outermost" function that drives the others.
    """
    top_level_fns = {
        name: obj for name, obj in inspect.getmembers(mod, inspect.isfunction)
        if (not name.startswith("_") and
            getattr(obj, "__module__", None) == "_sbg_b07v3_prog")
    }

    if not top_level_fns:
        return None

    # Find which function names are called from within other functions
    called_names = set()
    for name, fn in top_level_fns.items():
        try:
            import dis
            bytecode = dis.Bytecode(fn)
            for instr in bytecode:
                if instr.opname in ("CALL_FUNCTION", "CALL", "CALL_EX",
                                    "LOAD_GLOBAL", "LOAD_FAST", "LOAD_DEREF"):
                    if instr.argval in top_level_fns and instr.argval != name:
                        called_names.add(instr.argval)
        except Exception:
            pass

    # Roots = top-level functions NOT in called_names
    roots = {n: f for n, f in top_level_fns.items() if n not in called_names}

    if not roots:
        # All functions call each other (e.g., mutual recursion)
        # Fall back to longest name (heuristic for "main" function)
        return max(top_level_fns.values(), key=lambda f: len(f.__name__), default=None)

    # Among roots, prefer longer names (more specific) over shorter ones
    return max(roots.values(), key=lambda f: len(f.__name__), default=None)


def _extract_genome_v3(source_path: str) -> Optional[DynamicGenomeV3]:
    """Extract DynamicGenomeV3 for a single program file (cached)."""
    if source_path in _genome_cache_v3:
        return _genome_cache_v3[source_path]

    fn = _load_entry_fn(source_path)
    if fn is None:
        _genome_cache_v3[source_path] = None
        return None

    program_id = pathlib.Path(source_path).stem

    try:
        sig = inspect.signature(fn)
        n_params = len(sig.parameters)
    except (ValueError, TypeError):
        n_params = 1

    if n_params == 0:
        def _zero_arg_wrapper(inp):
            return fn()
        fn_to_trace = _zero_arg_wrapper
        inputs_to_use = [None]
    else:
        fn_to_trace = fn
        inputs_to_use = V3_CANONICAL_INPUTS

    try:
        result = _runner.run(program_id, fn_to_trace, inputs_to_use, n_runs=5, seed=42,
                             max_events=5_000)  # Reduce max_events to prevent stack overflow
        genome = _extractor.extract_from_traces(program_id, result.traces)
    except (Exception, RecursionError, MemoryError):
        genome = None

    _genome_cache_v3[source_path] = genome
    return genome


def _score_pair_v3(base_path: str, variant_path: str) -> float:
    """Score a pair using v3 distance. Returns similarity in [0,1]."""
    g1 = _extract_genome_v3(base_path)
    g2 = _extract_genome_v3(variant_path)

    if g1 is None or g2 is None:
        return 0.5  # neutral on extraction failure

    dist = distance_v3(g1, g2)
    return max(0.0, min(1.0, 1.0 - dist))


def _load_pairs(split: str) -> list:
    path = REPO_ROOT / "benchmark" / "datasets" / f"pairs_{split}.jsonl"
    pairs = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    return pairs


def _pairs_to_labels(pairs: list) -> list:
    return [0 if p["semantic_relation"] == "EQUIVALENT" else 1 for p in pairs]


def _find_optimal_threshold(similarities: list, labels: list) -> float:
    """Find threshold maximising F1 for CHANGED detection."""
    if not similarities:
        return 0.5
    unique = sorted(set(similarities))
    if unique[0] > 0.0:
        unique = [0.0] + unique
    unique.append(unique[-1] + 1e-6)

    best_f1 = -1.0
    best_t = 0.5
    for t in unique:
        tp = fp = fn = 0
        for sim, lbl in zip(similarities, labels):
            pred = 1 if sim < t else 0
            if lbl == 1 and pred == 1:
                tp += 1
            elif lbl == 0 and pred == 1:
                fp += 1
            elif lbl == 1 and pred == 0:
                fn += 1
        denom = 2 * tp + fp + fn
        f1 = (2 * tp) / denom if denom > 0 else 0.0
        if f1 > best_f1:
            best_f1 = f1
            best_t = t
    return best_t


def run(max_pairs: Optional[int] = None, split: str = "both") -> tuple:
    """
    Run B07-v3 dynamic SBG baseline.

    Returns (dev_metrics, test_metrics, threshold)
    """
    print("\n[B07_DYNAMIC_V3] Dynamic SBG V3 baseline")
    print("[B07_DYNAMIC_V3] Features: v2 + call_bigrams + input_sensitivity + "
          "call_depth_variance + hot_path_stability + exc_causality")
    print("[B07_DYNAMIC_V3] AUROC: tie-aware WMW (sbg.v3.metrics)")
    print(f"[B07_DYNAMIC_V3] {len(V3_CANONICAL_INPUTS)} canonical inputs (v3, superset of v2)")

    dev_pairs = _load_pairs("dev")
    test_pairs = _load_pairs("test")
    if max_pairs:
        dev_pairs = dev_pairs[:max_pairs]
        test_pairs = test_pairs[:max_pairs]

    # DEV pass
    print(f"\n[B07_DYNAMIC_V3] Scoring {len(dev_pairs)} DEV pairs...")
    dev_labels = _pairs_to_labels(dev_pairs)
    dev_sims = []
    dev_pair_ids = []
    for i, p in enumerate(dev_pairs):
        base = str(REPO_ROOT / p["base_path"])
        var = str(REPO_ROOT / p["variant_path"])
        dev_sims.append(_score_pair_v3(base, var))
        # Extract base program id for cluster bootstrap
        dev_pair_ids.append(pathlib.Path(p["base_path"]).stem)
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(dev_pairs)}")

    threshold = _find_optimal_threshold(dev_sims, dev_labels)
    dev_metrics = compute_metrics_v3(
        dev_sims, dev_labels, threshold,
        pair_ids=dev_pair_ids, n_bootstrap=500, seed=42
    )
    print(f"[B07_DYNAMIC_V3] DEV threshold={threshold:.4f} AUROC={dev_metrics['auroc']:.4f} "
          f"CI=[{dev_metrics['ci_auroc_lower']:.4f},{dev_metrics['ci_auroc_upper']:.4f}]")

    # TEST pass
    print(f"\n[B07_DYNAMIC_V3] Scoring {len(test_pairs)} TEST pairs...")
    test_labels = _pairs_to_labels(test_pairs)
    test_sims = []
    test_pair_ids = []
    for i, p in enumerate(test_pairs):
        base = str(REPO_ROOT / p["base_path"])
        var = str(REPO_ROOT / p["variant_path"])
        test_sims.append(_score_pair_v3(base, var))
        test_pair_ids.append(pathlib.Path(p["base_path"]).stem)
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(test_pairs)}")

    test_metrics = compute_metrics_v3(
        test_sims, test_labels, threshold,
        pair_ids=test_pair_ids, n_bootstrap=1000, seed=42
    )
    auroc_v3 = test_metrics['auroc']
    print(f"[B07_DYNAMIC_V3] TEST AUROC={auroc_v3:.4f} "
          f"CI=[{test_metrics['ci_auroc_lower']:.4f},{test_metrics['ci_auroc_upper']:.4f}]")
    print(f"[B07_DYNAMIC_V3] permutation_p={test_metrics['permutation_p']:.4f}")
    print(f"[B07_DYNAMIC_V3] tie_fraction={test_metrics['tie_fraction']:.4f}")

    # Inversion analysis
    equiv_sims = [s for s, l in zip(test_sims, test_labels) if l == 0]
    changed_sims = [s for s, l in zip(test_sims, test_labels) if l == 1]
    equiv_mean = sum(equiv_sims) / len(equiv_sims) if equiv_sims else 0.0
    changed_mean = sum(changed_sims) / len(changed_sims) if changed_sims else 0.0
    inversion_delta = changed_mean - equiv_mean
    print(f"\n[B07_DYNAMIC_V3] === Inversion Analysis ===")
    print(f"  EQUIV mean similarity:   {equiv_mean:.4f}")
    print(f"  CHANGED mean similarity: {changed_mean:.4f}")
    print(f"  Inversion delta (v3):    {inversion_delta:+.4f}  (v2 was -0.0453)")

    # Save results
    import pathlib as _pl
    _pl.Path(ARTIFACT_DIR).mkdir(parents=True, exist_ok=True)

    dev_result = {
        "baseline": "B07_DYNAMIC_V3",
        "version": "v3",
        "split": "dev",
        "threshold": threshold,
        "metrics": dev_metrics,
        "n_canonical_inputs": len(V3_CANONICAL_INPUTS),
        "genome_version": "DynamicGenomeV3",
        "new_v3_features": [
            "call_transition_bigrams", "input_sensitivity_score",
            "call_depth_variance", "hot_path_stability", "exception_causality_hash"
        ],
        "auroc_method": "tie_aware_wmw",
        "bootstrap_method": "cluster_by_base_program",
    }
    test_result = {
        "baseline": "B07_DYNAMIC_V3",
        "version": "v3",
        "split": "test",
        "threshold_from": "dev",
        "threshold": threshold,
        "metrics": test_metrics,
        "inversion_analysis": {
            "equiv_mean_similarity": round(equiv_mean, 6),
            "changed_mean_similarity": round(changed_mean, 6),
            "inversion_delta_v3": round(inversion_delta, 6),
            "inversion_delta_v2_reference": -0.045265,
            "inversion_resolved": bool(inversion_delta < 0),
        },
        "v2_comparison": {
            "v2_b07_auroc_naive": 0.531023,
            "v2_b07_auroc_tie_corrected": 0.5434,
            "v3_auroc": auroc_v3,
            "delta_vs_v2_tie_corrected": round(auroc_v3 - 0.5434, 6),
        },
    }

    for split_name, result in [("dev", dev_result), ("test", test_result)]:
        out_path = _pl.Path(ARTIFACT_DIR) / f"results_{split_name}.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)

    print(f"\n[B07_DYNAMIC_V3] Results saved to {ARTIFACT_DIR}")
    return dev_metrics, test_metrics, threshold


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pairs", type=int, default=None)
    args = parser.parse_args()
    run(max_pairs=args.max_pairs)
