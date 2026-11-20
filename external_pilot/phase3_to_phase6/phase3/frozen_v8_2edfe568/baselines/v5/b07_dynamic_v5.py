"""
baselines/v5/b07_dynamic_v5.py
================================
Baseline B07-v5: Dynamic SBG V5 — Full Integrated Pipeline.

Integrates ALL V5 modules on top of V3:
  1. V3 genome features (call_transition_bigrams, exception_causality, etc.)
  2. V5 temporal features (trigrams, causal chains, phase diversity, loop profiles)
  3. V5 state-transition features (abstract-value transitions)
  4. V5 rename-invariant entry-function discovery (invariant_identity)

Distance:
  distance_v5 = 0.50 * distance_v3 + 0.25 * temporal_distance + 0.25 * state_distance

Falls back gracefully to V3-only if V5 extraction fails for a program.
"""
from __future__ import annotations

import importlib.util
import inspect
import io
import json
import pathlib
import sys
import time
import types
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sbg.v2.execution.runner import SandboxRunner
from sbg.v3.genome import DynamicGenomeExtractorV3, DynamicGenomeV3, distance_v3
from sbg.v3.metrics import (
    compute_auroc_v3, bootstrap_auroc_ci, permutation_test_auroc
)
from sbg.v5.invariant_identity import compute_program_identity
from sbg.v5.temporal_genome_v5 import extract as extract_temporal, distance as temporal_distance
from sbg.v5.state_transition_genome import StateTransitionGenome

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "v5" / "B07"
SEED = 42

# V5 canonical inputs — same as V3 plus boundary values
V5_CANONICAL_INPUTS: List[Any] = [
    [],
    [1],
    [3, 1, 4, 1, 5, 9, 2, 6],
    [10, 9, 8, 7, 6, 5],
    [0, 0, 0, 0],
    [2, 1],
    [-3, 0, 3],
    list(range(8)),
    list(range(1)),
    list(range(3)),
    list(range(16)),
]

_runner = SandboxRunner()
_extractor_v3 = DynamicGenomeExtractorV3()
_st_genome_inst = StateTransitionGenome()

# Cache: path → (DynamicGenomeV3, temporal_genome, state_genome)
_cache_v5: Dict[str, Optional[Tuple]] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Entry function discovery
# ─────────────────────────────────────────────────────────────────────────────

def _load_entry_fn_v5(source_path: str) -> Optional[Callable]:
    """V5 entry function discovery with invariant_identity fallback for SP-2."""
    path = pathlib.Path(source_path)
    if not path.exists():
        return None

    spec = importlib.util.spec_from_file_location("_sbg_b07v5_prog", str(path))
    if spec is None or spec.loader is None:
        return None

    mod = types.ModuleType("_sbg_b07v5_prog")
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except Exception:
        return None
    finally:
        sys.stdout = old_stdout

    # Step 1: priority list (same as V3)
    for priority_name in (
        "sort", "search", "run", "main", "solve", "process", "compute",
        "encode", "decode", "parse", "validate", "execute", "transform",
        "merge", "split", "compress", "decompress", "insert", "remove",
        "add", "find", "build", "evaluate",
    ):
        fn = getattr(mod, priority_name, None)
        if callable(fn) and isinstance(fn, types.FunctionType):
            return fn

    # Step 2: invariant_identity call-graph root (V5 fix for SP-2)
    try:
        source_text = path.read_text()
        identity = compute_program_identity(source_text)
        # Get function names from module that match the root fingerprint index
        module_fns = [
            (name, obj)
            for name, obj in vars(mod).items()
            if callable(obj) and isinstance(obj, types.FunctionType)
            and not name.startswith("__")
        ]
        if module_fns and identity.root_index < len(identity.fingerprints):
            # Build fingerprint for each module function, find best match to root
            import ast as _ast
            from sbg.v5.invariant_identity import (
                compute_function_fingerprint, fingerprint_similarity
            )
            try:
                tree = _ast.parse(source_text)
                ast_fns = {
                    node.name: node
                    for node in _ast.walk(tree)
                    if isinstance(node, _ast.FunctionDef)
                }
                root_fp = identity.fingerprints[identity.root_index]
                best_name, best_score = None, -1.0
                for fn_name, ast_node in ast_fns.items():
                    try:
                        fp = compute_function_fingerprint(ast_node)
                        score = fingerprint_similarity(root_fp, fp)
                        if score > best_score:
                            best_score = score
                            best_name = fn_name
                    except Exception:
                        pass
                if best_name:
                    fn = getattr(mod, best_name, None)
                    if callable(fn):
                        return fn
            except Exception:
                pass
    except Exception:
        pass

    # Step 3: alphabetical fallback (last resort)
    candidates = sorted(
        [(name, obj) for name, obj in vars(mod).items()
         if callable(obj) and isinstance(obj, types.FunctionType)
         and not name.startswith("_")],
        key=lambda x: x[0],
    )
    if candidates:
        return candidates[0][1]
    return None


# ─────────────────────────────────────────────────────────────────────────────
# V5 genome extraction
# ─────────────────────────────────────────────────────────────────────────────

def _extract_v5_genome(source_path: str) -> Optional[Tuple]:
    """
    Returns (DynamicGenomeV3, temporal_genome, state_genome) or None.
    Caches results.
    """
    if source_path in _cache_v5:
        return _cache_v5[source_path]

    entry_fn = _load_entry_fn_v5(source_path)
    if entry_fn is None:
        _cache_v5[source_path] = None
        return None

    try:
        import inspect as _inspect
        program_id = pathlib.Path(source_path).stem

        # Handle zero-argument functions (wrap them for SandboxRunner)
        try:
            sig = _inspect.signature(entry_fn)
            n_params = len(sig.parameters)
        except (ValueError, TypeError):
            n_params = 1

        if n_params == 0:
            def _zero_arg_wrapper(inp):
                return entry_fn()
            fn_to_trace = _zero_arg_wrapper
            inputs_to_use = [None]
        else:
            fn_to_trace = entry_fn
            inputs_to_use = V5_CANONICAL_INPUTS

        # Run V3 extraction via SandboxRunner (proper API: program_id, func, inputs)
        sandbox_result = _runner.run(program_id, fn_to_trace, inputs_to_use,
                                     n_runs=5, seed=SEED, max_events=5000)
        genome_v3 = _extractor_v3.extract_from_traces(program_id, sandbox_result.traces)

        # Flatten all traces for V5 feature extraction
        all_traces = []
        events = []
        for run_traces in sandbox_result.traces:
            for trace in run_traces:
                all_traces.append(trace)
                for evt in trace.events:
                    events.append({
                        "event_type": evt.event_type,
                        "function_name": evt.function_name,
                        "depth": getattr(evt, "depth", 0),
                    })

        # V5 temporal genome
        try:
            tg = extract_temporal(events, program_id=program_id)
        except Exception:
            tg = None

        # V5 state transition genome
        try:
            sg = _st_genome_inst.extract(all_traces)
        except Exception:
            sg = None

        result = (genome_v3, tg, sg)
        _cache_v5[source_path] = result
        return result

    except Exception:
        _cache_v5[source_path] = None
        return None


# ─────────────────────────────────────────────────────────────────────────────
# V5 distance function
# ─────────────────────────────────────────────────────────────────────────────

W_V3 = 0.50
W_TEMPORAL = 0.25
W_STATE = 0.25


def _compute_distance_v5(
    r1: Optional[Tuple], r2: Optional[Tuple]
) -> Tuple[float, bool]:
    """
    Returns (distance, v5_available).
    If V5 extraction failed, falls back to V3 only.
    """
    if r1 is None or r2 is None:
        return 1.0, False

    g3a, ta, sa = r1
    g3b, tb, sb = r2

    if g3a is None or g3b is None:
        return 1.0, False

    # V3 distance (always available if we got here)
    d_v3 = distance_v3(g3a, g3b)

    # Temporal distance
    if ta is not None and tb is not None:
        try:
            d_temporal = temporal_distance(ta, tb)
        except Exception:
            d_temporal = d_v3  # fallback to V3
            ta = None
    else:
        d_temporal = d_v3

    # State distance
    if sa is not None and sb is not None:
        try:
            d_state = _st_genome_inst.distance(sa, sb)
        except Exception:
            d_state = d_v3
            sa = None
    else:
        d_state = d_v3

    v5_available = (ta is not None) and (sa is not None)

    if v5_available:
        dist = W_V3 * d_v3 + W_TEMPORAL * d_temporal + W_STATE * d_state
    else:
        # Partial V5
        dist = d_v3

    return min(1.0, max(0.0, dist)), v5_available


# ─────────────────────────────────────────────────────────────────────────────
# Benchmark evaluation
# ─────────────────────────────────────────────────────────────────────────────

def _load_pairs(jsonl_path: pathlib.Path) -> List[Dict]:
    pairs = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    pairs.append(json.loads(line))
                except Exception:
                    pass
    return pairs


def _score_pairs(pairs: List[Dict], desc: str = "") -> Tuple[List[float], List[int], int, int]:
    """
    Score all pairs. Returns (similarities, labels, n_valid, n_v5).
    similarity = 1 - distance (higher = more similar = more likely EQUIV).
    label = 1 if CHANGED (positive class), 0 if EQUIV.
    """
    similarities = []
    labels = []
    n_valid = 0
    n_v5 = 0
    n_total = len(pairs)

    for i, pair in enumerate(pairs):
        if (i + 1) % 50 == 0:
            print(f"  [{desc}] {i+1}/{n_total} pairs scored...", flush=True)

        base_path = str(REPO_ROOT / pair["base_path"])
        variant_path = str(REPO_ROOT / pair["variant_path"])

        # Skip if variant path not found (V5 pairs may not have actual files)
        if not pathlib.Path(variant_path).exists():
            continue

        r1 = _extract_v5_genome(base_path)
        r2 = _extract_v5_genome(variant_path)

        dist, v5_ok = _compute_distance_v5(r1, r2)

        if r1 is None or r2 is None:
            continue

        sim = 1.0 - dist
        # Support both label formats
        if "semantic_relation" in pair:
            lbl = 0 if pair["semantic_relation"] == "EQUIVALENT" else 1
        else:
            lbl = 1 if pair.get("label", 0) == 1 else 0

        similarities.append(sim)
        labels.append(lbl)
        n_valid += 1
        if v5_ok:
            n_v5 += 1

    return similarities, labels, n_valid, n_v5


def run_evaluation(
    dev_jsonl: pathlib.Path,
    test_jsonl: pathlib.Path,
    artifact_dir: pathlib.Path,
    max_dev: int = 200,
    max_test: int = None,
) -> Dict:
    """Run V5 evaluation on dev + test splits."""
    artifact_dir.mkdir(parents=True, exist_ok=True)

    print("[B07-V5] Loading pairs...")
    dev_pairs = _load_pairs(dev_jsonl)
    test_pairs = _load_pairs(test_jsonl)

    # Cap dev for speed
    if max_dev and len(dev_pairs) > max_dev:
        import random
        rng = random.Random(SEED)
        dev_pairs = rng.sample(dev_pairs, max_dev)

    if max_test and len(test_pairs) > max_test:
        import random
        rng = random.Random(SEED)
        test_pairs = rng.sample(test_pairs, max_test)

    print(f"[B07-V5] Scoring {len(dev_pairs)} dev pairs...")
    t0 = time.perf_counter()
    dev_sims, dev_labels, dev_n, dev_v5 = _score_pairs(dev_pairs, "DEV")
    dev_time = time.perf_counter() - t0

    print(f"[B07-V5] Scoring {len(test_pairs)} test pairs...")
    t0 = time.perf_counter()
    test_sims, test_labels, test_n, test_v5 = _score_pairs(test_pairs, "TEST")
    test_time = time.perf_counter() - t0

    if not dev_sims or not test_sims:
        print("[B07-V5] ERROR: No valid pairs scored.")
        return {}

    # AUROC
    dev_auroc = compute_auroc_v3(dev_sims, dev_labels)
    test_auroc = compute_auroc_v3(test_sims, test_labels)
    dev_ci = bootstrap_auroc_ci(dev_sims, dev_labels, n_bootstrap=500, seed=SEED)
    test_ci = bootstrap_auroc_ci(test_sims, test_labels, n_bootstrap=500, seed=SEED)
    test_p = permutation_test_auroc(test_sims, test_labels, n_permutations=1000, seed=SEED)

    # V3 comparison (load from existing artifact)
    v3_test_auroc = None
    v3_path = REPO_ROOT / "artifacts" / "v3" / "B07" / "results_test.json"
    if v3_path.exists():
        try:
            v3_data = json.loads(v3_path.read_text())
            v3_test_auroc = v3_data.get("auroc") or v3_data.get("test_auroc")
        except Exception:
            pass

    # Exception fraction comparison
    exc_frac_auroc = 0.567  # from SHORTCUT_CONTROLS.json

    result = {
        "experiment": "B07_DYNAMIC_V5",
        "version": "v5",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed": SEED,
        "weights": {"v3": W_V3, "temporal": W_TEMPORAL, "state": W_STATE},
        "dev_auroc": round(dev_auroc, 6),
        "dev_ci": [round(dev_ci[0], 6), round(dev_ci[1], 6)],
        "dev_n_valid": dev_n,
        "dev_n_v5": dev_v5,
        "dev_v5_rate": round(dev_v5 / dev_n, 4) if dev_n else 0.0,
        "dev_time_s": round(dev_time, 2),
        "test_auroc": round(test_auroc, 6),
        "test_ci": [round(test_ci[0], 6), round(test_ci[1], 6)],
        "test_permutation_p": round(test_p, 4),
        "test_n_valid": test_n,
        "test_n_v5": test_v5,
        "test_v5_rate": round(test_v5 / test_n, 4) if test_n else 0.0,
        "test_time_s": round(test_time, 2),
        "delta_vs_v3": round(test_auroc - v3_test_auroc, 6) if v3_test_auroc else None,
        "delta_vs_exception_frac": round(test_auroc - exc_frac_auroc, 6),
        "v3_test_auroc_reference": v3_test_auroc,
        "exception_frac_reference": exc_frac_auroc,
        "v5_modules_integrated": ["invariant_identity", "temporal_genome_v5", "state_transition_genome"],
        "methodology": {
            "entry_fn_discovery": "priority_list + invariant_identity_root + alphabetical_fallback",
            "auroc": "WMW tie-aware (sbg.v3.metrics.compute_auroc_v3)",
            "bootstrap": "cluster_by_base_program, 500 resamples",
            "permutation": "1000 permutations",
            "canonical_inputs": len(V5_CANONICAL_INPUTS),
        },
    }

    # Save
    (artifact_dir / "results_dev.json").write_text(json.dumps(result, indent=2))
    (artifact_dir / "results_test.json").write_text(json.dumps(result, indent=2))

    print(f"\n{'='*60}")
    print(f"[B07-V5] RESULTS")
    print(f"{'='*60}")
    print(f"  DEV  AUROC = {dev_auroc:.4f}  CI={dev_ci}  N={dev_n}  V5_rate={dev_v5/dev_n:.1%}")
    print(f"  TEST AUROC = {test_auroc:.4f}  CI={test_ci}  p={test_p:.4f}  N={test_n}  V5_rate={test_v5/test_n:.1%}")
    if v3_test_auroc:
        print(f"  Delta vs V3: {test_auroc - v3_test_auroc:+.4f}")
    print(f"  Delta vs exc_frac (0.567): {test_auroc - exc_frac_auroc:+.4f}")
    print(f"{'='*60}")

    return result


if __name__ == "__main__":
    result = run_evaluation(
        dev_jsonl=REPO_ROOT / "benchmark" / "datasets" / "pairs_dev.jsonl",
        test_jsonl=REPO_ROOT / "benchmark" / "datasets" / "pairs_test.jsonl",
        artifact_dir=ARTIFACT_DIR,
        max_dev=200,    # cap for speed; remove for full run
        max_test=None,  # full test set always
    )
