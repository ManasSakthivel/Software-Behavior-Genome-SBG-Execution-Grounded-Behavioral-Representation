"""
baselines/v2/b07_dynamic_v2.py
================================
Baseline B07-v2: Dynamic-only SBG V2.

Uses ONLY Output-free dynamic features (SAFEGUARD-2).
No static features. Compares DynamicGenome distance on pairs.

Protocol
--------
1. Load program from path (each pair has base_path, variant_path)
2. Discover entry function (auto-detect or from harness)
3. Extract DynamicGenome using v2 canonical inputs (SAFEGUARD-3)
4. Compute dynamic distance → similarity
5. Score DEV → select threshold → evaluate TEST (threshold never from test)

SAFEGUARD-3: V2 canonical inputs are independent from v1's 5 fixed inputs.
"""
from __future__ import annotations

import importlib.util
import inspect
import pathlib
import sys
import types
from typing import Any, Callable, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sbg.v2.execution.runner import SandboxRunner
from sbg.v2.execution.normalizer import TraceNormalizer
from sbg.v2.execution.genome import DynamicGenomeExtractor, DynamicGenome, distance as dyn_distance
from baselines.common import (
    load_pairs, pairs_to_labels, find_optimal_threshold,
    compute_metrics, save_results,
)

ARTIFACT_DIR = str(REPO_ROOT / "artifacts" / "v2" / "B07")

# V2 canonical inputs (SAFEGUARD-3: independent from v1 canonical [[], [1], [1,2,3], [5,4,3,2,1], range(20)])
# These 8 inputs cover: empty, single, small sorted, small reverse, duplicates, boundary, mixed types
V2_CANONICAL_INPUTS: List[Any] = [
    [],
    [1],
    [3, 1, 4, 1, 5, 9, 2, 6],   # fibonacci-ish digits
    [10, 9, 8, 7, 6, 5],          # descending
    [0, 0, 0, 0],                 # all same — boundary for off-by-one
    [2, 1],                       # minimal unsorted
    [-3, 0, 3],                   # negative values
    list(range(8)),               # 8 elements ascending
]

_runner = SandboxRunner()
_normalizer = TraceNormalizer()
_extractor = DynamicGenomeExtractor()

# Cache to avoid re-running programs for multiple pairs
_genome_cache: Dict[str, Optional[DynamicGenome]] = {}


def _load_entry_fn(source_path: str) -> Optional[Callable]:
    """Load a Python source file and auto-discover the entry function."""
    path = pathlib.Path(source_path)
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("_sbg_b07_prog", str(path))
    if spec is None or spec.loader is None:
        return None
    mod = types.ModuleType("_sbg_b07_prog")
    # Suppress stdout during import
    import io
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

    # Fall back to first public top-level function
    for name, obj in inspect.getmembers(mod, inspect.isfunction):
        if not name.startswith("_"):
            if getattr(obj, "__module__", None) == "_sbg_b07_prog":
                return obj

    # Phase 4 Wave 1 fix: class-based execution adapter fallback.
    # Handles class-only programs with no top-level callable (e.g.
    # conc_read_write_lock.py). See docs/v2/ENTRYPOINT_LIMITATION.md.
    adapter = _build_class_adapter(mod)
    if adapter is not None:
        return adapter

    return None


def _build_class_adapter(mod: types.ModuleType) -> Optional[Callable]:
    """
    Fallback entry point for class-only programs with no top-level callable
    function (e.g. conc_read_write_lock.py — Phase 4 Wave 1 fix).

    Builds a deterministic, SINGLE-THREADED driver over the module's
    "primary" (outermost/composed) class using reflection over its public
    methods, so it survives method-renaming transforms (SP-2) without
    hardcoding any method names.

    Class selection: composition-based, not source-order-based
    -------------------------------------------------------------
    Source-line ordering is UNRELIABLE here (inspect.getsourcelines fails
    for modules loaded via importlib without sys.modules registration).
    Instead, the "primary" class is detected structurally: a class C is
    "composed" if an instance of C holds an attribute whose type is another
    class also defined in this module (e.g. ProtectedDict holds a
    ReadWriteLock instance). Composed/outer classes are preferred because
    they typically enforce correct usage protocol (e.g. paired
    acquire/release) internally, whereas driving an inner primitive class's
    methods directly and independently can produce genuine deadlocks
    (e.g. calling acquire_write() before release_read() on a raw
    ReadWriteLock). If no composition relationship is found, falls back to
    the class with the most public methods.

    Rationale for safety
    ---------------------
    conc_read_write_lock was previously excluded from dynamic execution
    entirely (via SandboxRunner._UNSAFE_PROGRAMS) because its __main__ test
    block spawns real concurrent threads, which is non-deterministic. This
    adapter does NOT spawn threads — it drives the class's public API
    sequentially. This still exercises genuine lock acquire/release code
    paths (ProtectedDict enforces correct acquire/release discipline
    internally) but does not reproduce concurrent contention.

    Disclosed limitation (docs/v2/ENTRYPOINT_LIMITATION.md): this adapter
    measures SEQUENTIAL behavioral correctness of the class's public API,
    not genuine concurrent/interleaved behavior.
    """
    classes = [
        obj for _, obj in inspect.getmembers(mod, inspect.isclass)
        if getattr(obj, "__module__", None) == mod.__name__
        and not issubclass(obj, BaseException)
    ]
    if not classes:
        return None

    def _try_instantiate(cls: type) -> Any:
        try:
            return cls()
        except Exception:
            return None

    instances: Dict[type, Any] = {}
    for cls in classes:
        inst = _try_instantiate(cls)
        if inst is not None:
            instances[cls] = inst

    if not instances:
        return None

    # Prefer a class whose instance holds an attribute that is itself an
    # instance of another discovered class (composition == likely "outer"
    # class that safely wraps a primitive).
    primary_cls = None
    for cls, inst in instances.items():
        try:
            attr_values = list(vars(inst).values())
        except TypeError:
            continue
        if any(type(v) in instances and type(v) is not cls for v in attr_values):
            primary_cls = cls
            break

    if primary_cls is None:
        # Fall back: class with the most public methods (heuristic proxy
        # for "richer surface API" == likely the outer/composed class).
        primary_cls = max(
            instances,
            key=lambda c: sum(
                1 for n, _ in inspect.getmembers(instances[c], predicate=inspect.ismethod)
                if not n.startswith("_")
            ),
        )

    # Method NAMES are resolved once (not bound methods), so a fresh
    # instance can be constructed on every call — see below.
    method_names = [
        name for name, _ in inspect.getmembers(instances[primary_cls], predicate=inspect.ismethod)
        if not name.startswith("_")
    ]
    if not method_names:
        return None

    def _class_adapter_driver(inp: Any) -> None:
        # A FRESH instance is created for EVERY individual method call (not
        # shared across calls). This is required because some transform
        # variants contain genuine bugs (e.g. SP-2's incomplete
        # method-rename: a try/finally block that calls a lock-release
        # method under its OLD name after the method was renamed — see
        # docs/v2/ENTRYPOINT_LIMITATION.md). If such a bug leaves internal
        # lock state corrupted (e.g. a reader count that is incremented but
        # never decremented because the release call raised AttributeError),
        # reusing the SAME instance for a subsequent method call would
        # deadlock permanently on a real threading.Condition.wait() that is
        # never notified. Fresh-instance-per-call fully isolates each
        # individual call so a single broken transaction cannot cascade or
        # hang the rest of genome extraction. This trades away cross-call
        # state persistence (an already-disclosed limitation: this adapter
        # measures per-call sequential correctness of the public API, not
        # stateful behavior across a call sequence).
        seq = inp if isinstance(inp, (list, tuple)) else [inp]
        for v in seq:
            for name in method_names:
                try:
                    instance = primary_cls()
                except Exception:
                    continue
                m = getattr(instance, name, None)
                if m is None:
                    continue
                try:
                    n_p = len(inspect.signature(m).parameters)
                except (TypeError, ValueError):
                    n_p = 1
                try:
                    if n_p == 0:
                        m()
                    elif n_p == 1:
                        m(v)
                    else:
                        m(v, v)
                except Exception:
                    pass  # tolerate arg/semantic mismatches; shape of trace is what matters
        return None

    return _class_adapter_driver


def _extract_genome(source_path: str) -> Optional[DynamicGenome]:
    """Extract DynamicGenome for a single program file (cached)."""
    if source_path in _genome_cache:
        return _genome_cache[source_path]

    fn = _load_entry_fn(source_path)
    if fn is None:
        _genome_cache[source_path] = None
        return None

    program_id = pathlib.Path(source_path).stem

    # Determine how to call the function:
    # - 0-param functions (test harnesses): call once with no args
    # - n-param functions: call once per canonical input
    import inspect
    try:
        sig = inspect.signature(fn)
        n_params = len(sig.parameters)
    except (ValueError, TypeError):
        n_params = 1

    if n_params == 0:
        # Zero-arg function: wrap in a lambda that ignores input
        def _zero_arg_wrapper(inp):
            return fn()
        fn_to_trace = _zero_arg_wrapper
        inputs_to_use = [None]  # single trace run
    else:
        fn_to_trace = fn
        inputs_to_use = V2_CANONICAL_INPUTS

    try:
        result = _runner.run(program_id, fn_to_trace, inputs_to_use, n_runs=5, seed=42)
        nb = _normalizer.normalize(program_id, result.traces)
        genome = _extractor.extract(nb)
    except Exception:
        genome = None

    _genome_cache[source_path] = genome
    return genome


def _score_pair(base_path: str, variant_path: str) -> float:
    """Score a pair. Returns similarity in [0,1]: 1.0=identical behavior."""
    g1 = _extract_genome(base_path)
    g2 = _extract_genome(variant_path)

    if g1 is None or g2 is None:
        return 0.5  # neutral on extraction failure

    dist = dyn_distance(g1, g2)
    return max(0.0, min(1.0, 1.0 - dist))


def run(max_pairs: Optional[int] = None, split: str = "both") -> tuple:
    """
    Run B07 dynamic-only baseline.

    Parameters
    ----------
    max_pairs : int, optional
        Limit pairs for quick testing.
    split : str
        "both", "dev", or "test".

    Returns
    -------
    (dev_metrics, test_metrics, threshold) or (None, test_metrics, threshold)
    """
    print("\n[B07_DYNAMIC_V2] Dynamic-only SBG v2 baseline")
    print("[B07_DYNAMIC_V2] SAFEGUARD-2: Output-free features only")
    print(f"[B07_DYNAMIC_V2] SAFEGUARD-3: {len(V2_CANONICAL_INPUTS)} v2 inputs (independent from v1)")

    dev_pairs = load_pairs("dev")
    test_pairs = load_pairs("test")
    if max_pairs:
        dev_pairs = dev_pairs[:max_pairs]
        test_pairs = test_pairs[:max_pairs]

    # DEV pass — select threshold
    print(f"\n[B07_DYNAMIC_V2] Scoring {len(dev_pairs)} DEV pairs...")
    dev_labels = pairs_to_labels(dev_pairs)
    dev_sims = []
    for i, p in enumerate(dev_pairs):
        base = str(REPO_ROOT / p["base_path"])
        var = str(REPO_ROOT / p["variant_path"])
        dev_sims.append(_score_pair(base, var))
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(dev_pairs)}")

    threshold = find_optimal_threshold(dev_sims, dev_labels)
    dev_metrics = compute_metrics(dev_sims, dev_labels, threshold)
    print(f"[B07_DYNAMIC_V2] DEV threshold={threshold:.4f} F1={dev_metrics['f1']:.4f} AUROC={dev_metrics['auroc']:.4f}")

    # TEST pass — frozen threshold
    print(f"\n[B07_DYNAMIC_V2] Scoring {len(test_pairs)} TEST pairs...")
    test_labels = pairs_to_labels(test_pairs)
    test_sims = []
    for i, p in enumerate(test_pairs):
        base = str(REPO_ROOT / p["base_path"])
        var = str(REPO_ROOT / p["variant_path"])
        test_sims.append(_score_pair(base, var))
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(test_pairs)}")

    test_metrics = compute_metrics(test_sims, test_labels, threshold)
    print(f"[B07_DYNAMIC_V2] TEST F1={test_metrics['f1']:.4f} AUROC={test_metrics['auroc']:.4f} AUPRC={test_metrics['auprc']:.4f}")

    # Inversion analysis (H9 diagnostic)
    equiv_sims = [s for s, l in zip(test_sims, test_labels) if l == 0]
    changed_sims = [s for s, l in zip(test_sims, test_labels) if l == 1]
    equiv_mean = sum(equiv_sims) / len(equiv_sims) if equiv_sims else 0.0
    changed_mean = sum(changed_sims) / len(changed_sims) if changed_sims else 0.0
    inversion_delta = changed_mean - equiv_mean

    print(f"\n[B07_DYNAMIC_V2] === Inversion Analysis (H9) ===")
    print(f"  EQUIV mean similarity:   {equiv_mean:.4f}")
    print(f"  CHANGED mean similarity: {changed_mean:.4f}")
    print(f"  Inversion delta (v2):    {inversion_delta:+.4f}  (v1 static was +0.0335)")
    print(f"  Inversion direction:     {'RESOLVED (negative)' if inversion_delta < 0 else 'STILL INVERTED (positive)'}")

    import pathlib as _pathlib
    _pathlib.Path(ARTIFACT_DIR).mkdir(parents=True, exist_ok=True)

    dev_result = {
        "baseline": "B07_DYNAMIC_V2",
        "split": "dev",
        "threshold": threshold,
        "metrics": dev_metrics,
        "feature_classification": "OUTPUT_FREE",
        "safeguards": ["SAFEGUARD-2", "SAFEGUARD-3"],
        "n_canonical_inputs": len(V2_CANONICAL_INPUTS),
        "n_genomes_cached": len(_genome_cache),
        "score_distribution": {
            "eq_mean": round(sum(s for s, l in zip(dev_sims, dev_labels) if l == 0) /
                             max(1, sum(1 for l in dev_labels if l == 0)), 4),
            "ch_mean": round(sum(s for s, l in zip(dev_sims, dev_labels) if l == 1) /
                             max(1, sum(1 for l in dev_labels if l == 1)), 4),
        },
    }
    test_result = {
        "baseline": "B07_DYNAMIC_V2",
        "split": "test",
        "threshold_from": "dev",
        "threshold": threshold,
        "metrics": test_metrics,
        "inversion_analysis": {
            "equiv_mean_similarity": round(equiv_mean, 6),
            "changed_mean_similarity": round(changed_mean, 6),
            "inversion_delta_v2": round(inversion_delta, 6),
            "inversion_delta_v1_reference": 0.0335,
            "inversion_resolved": bool(inversion_delta < 0),
        },
    }

    save_results("B07_DYNAMIC_V2", "dev", dev_result, ARTIFACT_DIR)
    save_results("B07_DYNAMIC_V2", "test", test_result, ARTIFACT_DIR)
    print(f"\n[B07_DYNAMIC_V2] Results saved to {ARTIFACT_DIR}")
    return dev_metrics, test_metrics, threshold


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pairs", type=int, default=None)
    args = parser.parse_args()
    run(max_pairs=args.max_pairs)
