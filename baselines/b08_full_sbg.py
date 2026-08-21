"""
baselines/b08_full_sbg.py
===========================
B8: Full SBG — all 8 dimensions (CONTROL, DATA, STATE, RESOURCE, TEMPORAL,
ERROR, INTERACTION, EXECUTION).

Dynamic dimensions use the Tracer with fixed canonical inputs.
Static dimensions use AST extractors.

Weight calibration: use DEFAULT_WEIGHTS from sbg/distance.py.
DO NOT tune on test set. Weights frozen after DEV evaluation.

Scoring: similarity = 1 - distance. HIGH → EQUIVALENT, LOW → CHANGED.
"""
import collections
import importlib.util
import json
import pathlib
import sys
import threading
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from baselines.common import (
    load_pairs, load_source, run_baseline, pairs_to_labels,
    compute_metrics, find_optimal_threshold, save_results, compute_auroc,
    REPO_ROOT, ARTIFACTS_DIR
)

ARTIFACT_DIR = str(ARTIFACTS_DIR / "B08")

# Static extractors
from sbg.extraction.static.extractor import ControlGenomeExtractor, distance as ctrl_dist, canonicalize as canon_ctrl
from sbg.extraction.static.data_genome import DataGenomeExtractor, distance as data_dist, canonicalize as canon_data
from sbg.extraction.static.error_genome import ErrorGenomeExtractor, distance as err_dist, canonicalize as canon_err

# Dynamic extractors
from sbg.extraction.dynamic.tracer import Tracer, ExecutionGenomeExtractor, distance as exec_dist, canonicalize as canon_exec
from sbg.extraction.dynamic.state_genome import StateGenomeExtractor, distance as state_dist, canonicalize as canon_state
from sbg.extraction.dynamic.resource_genome import ResourceGenomeExtractor, distance as res_dist, canonicalize as canon_res
from sbg.extraction.dynamic.temporal_genome import TemporalGenomeExtractor, distance as temp_dist, canonicalize as canon_temp
from sbg.extraction.dynamic.interaction_genome import InteractionGenomeExtractor, distance as inter_dist, canonicalize as canon_inter

# Default weights (from sbg/distance.py)
DEFAULT_WEIGHTS = {
    "CONTROL": 0.20,
    "DATA": 0.15,
    "STATE": 0.15,
    "RESOURCE": 0.10,
    "TEMPORAL": 0.10,
    "ERROR": 0.10,
    "INTERACTION": 0.10,
    "EXECUTION": 0.10,
}

_FIXED_INPUTS = [-5, 0, 1, 5, 10, 100,
                 [], [1], [1, 2, 3], [5, 4, 3, 2, 1],
                 "", "a", "hello", "hello world"]


def _load_fn_from_source(source: str):
    """Load callable entry point from source string."""
    _c = getattr(_load_fn_from_source, '_c', 0) + 1
    _load_fn_from_source._c = _c
    mod = types.ModuleType(f"_sbg_mod_{_c}")
    try:
        exec(compile(source, f"<sbg_{_c}>", "exec"), mod.__dict__)
    except Exception:
        return None
    for name in ("main", "solve", "run", "compute"):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    fns = [v for k, v in mod.__dict__.items()
           if callable(v) and not k.startswith('_') and isinstance(v, types.FunctionType)]
    return fns[0] if len(fns) == 1 else None


def _safe_extract_dynamic(source: str) -> dict:
    """Extract dynamic genomes, returning None per dimension on failure."""
    fn = _load_fn_from_source(source)
    if fn is None:
        return {k: None for k in ("STATE", "RESOURCE", "TEMPORAL", "INTERACTION", "EXECUTION")}

    tracer = Tracer()
    try:
        traces = tracer.trace(fn, _FIXED_INPUTS, max_events=5000)
    except Exception:
        return {k: None for k in ("STATE", "RESOURCE", "TEMPORAL", "INTERACTION", "EXECUTION")}

    result = {}
    try:
        exec_genome = ExecutionGenomeExtractor().extract(traces)
        result["EXECUTION"] = canon_exec(exec_genome)
    except Exception:
        result["EXECUTION"] = None

    try:
        state_genome = StateGenomeExtractor().extract(traces)
        result["STATE"] = canon_state(state_genome)
    except Exception:
        result["STATE"] = None

    try:
        res_genome = ResourceGenomeExtractor().extract(traces)
        result["RESOURCE"] = canon_res(res_genome)
    except Exception:
        result["RESOURCE"] = None

    try:
        temp_genome = TemporalGenomeExtractor().extract(traces)
        result["TEMPORAL"] = canon_temp(temp_genome)
    except Exception:
        result["TEMPORAL"] = None

    try:
        inter_genome = InteractionGenomeExtractor().extract(traces)
        result["INTERACTION"] = canon_inter(inter_genome)
    except Exception:
        result["INTERACTION"] = None

    return result


def _safe_extract_static(source: str) -> dict:
    result = {}
    try:
        result["CONTROL"] = canon_ctrl(ControlGenomeExtractor().extract(source))
    except Exception:
        result["CONTROL"] = None
    try:
        result["DATA"] = canon_data(DataGenomeExtractor().extract(source))
    except Exception:
        result["DATA"] = None
    try:
        result["ERROR"] = canon_err(ErrorGenomeExtractor().extract(source))
    except Exception:
        result["ERROR"] = None
    return result


_DIM_FUNS = {
    "CONTROL": ctrl_dist,
    "DATA": data_dist,
    "STATE": state_dist,
    "RESOURCE": res_dist,
    "TEMPORAL": temp_dist,
    "ERROR": err_dist,
    "INTERACTION": inter_dist,
    "EXECUTION": exec_dist,
}

_genome_cache: dict = {}


def _extract_genome(source: str) -> dict:
    key = hash(source[:1000])
    if key in _genome_cache:
        return _genome_cache[key]
    static = _safe_extract_static(source)
    dynamic = _safe_extract_dynamic(source)
    genome = {**static, **dynamic}
    _genome_cache[key] = genome
    return genome


def _compute_sbg_distance(g_a: dict, g_b: dict, weights: dict = DEFAULT_WEIGHTS) -> tuple:
    """Returns (distance, dims_used, fallback_count)."""
    total_w = 0.0
    total_d = 0.0
    dims_used = []
    fallback_count = 0

    for dim, w in weights.items():
        ga = g_a.get(dim)
        gb = g_b.get(dim)
        if ga is None or gb is None:
            fallback_count += 1
            continue
        fn = _DIM_FUNS.get(dim)
        if fn is None:
            continue
        try:
            d = fn(ga, gb)
            total_d += w * float(d)
            total_w += w
            dims_used.append(dim)
        except Exception:
            fallback_count += 1

    if total_w == 0:
        return 0.0, dims_used, fallback_count
    return total_d / total_w, dims_used, fallback_count


def score_fn(src_a: str, src_b: str) -> float:
    g_a = _extract_genome(src_a)
    g_b = _extract_genome(src_b)
    dist, _, _ = _compute_sbg_distance(g_a, g_b)
    return 1.0 - dist


if __name__ == "__main__":
    dev_pairs = load_pairs("dev")
    test_pairs = load_pairs("test")

    print("[B08] Full SBG baseline (all 8 dimensions)")
    print(f"[B08] Weights: {DEFAULT_WEIGHTS}")

    dev_m, test_m, threshold = run_baseline(
        "B08", score_fn, dev_pairs, test_pairs,
        artifact_dir=ARTIFACT_DIR
    )

    # Record frozen weights
    for split in ("dev", "test"):
        p = pathlib.Path(ARTIFACT_DIR) / f"results_{split}.json"
        if p.exists():
            d = json.loads(p.read_text())
            d["weights_used"] = DEFAULT_WEIGHTS
            d["weights_source"] = "DEFAULT_WEIGHTS from sbg/distance.py — NOT tuned on test set"
            d["fallback_embedding"] = False
            p.write_text(json.dumps(d, indent=2))

    print(f"\n=== B8 Full SBG ===")
    print(f"  DEV  F1={dev_m['f1']:.4f} AUROC={dev_m['auroc']:.4f}")
    print(f"  TEST F1={test_m['f1']:.4f} AUROC={test_m['auroc']:.4f} "
          f"[{test_m['ci_f1_lower']:.3f}–{test_m['ci_f1_upper']:.3f}]")
