"""
sbg.v2.static_proxy
====================
Provides full v1 behavioral_distance() as a static component for the v2 hybrid genome.

This module replaces the token-overlap proxy in the original B08 hybrid implementation.
It uses the identical extraction pipeline as baselines/b08_full_sbg.py to compute the
v1 behavioral distance that produced AUROC=0.4237.

API
---
v1_behavioral_distance(path_a, path_b) -> Optional[float]
    Returns v1 behavioral distance in [0,1], or None on extraction failure.

v1_behavioral_similarity(path_a, path_b) -> Optional[float]
    Returns 1 - v1_behavioral_distance, or None on extraction failure.
"""
from __future__ import annotations

import pathlib
import sys
import types
from functools import lru_cache
from typing import Any, Dict, Optional

# Ensure repo root is on path
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sbg.distance import behavioral_distance, DEFAULT_WEIGHTS
from sbg.extraction.static.extractor import ControlGenomeExtractor, canonicalize as canon_ctrl
from sbg.extraction.static.data_genome import DataGenomeExtractor, canonicalize as canon_data
from sbg.extraction.static.error_genome import ErrorGenomeExtractor, canonicalize as canon_err
from sbg.extraction.dynamic.tracer import Tracer, ExecutionGenomeExtractor, canonicalize as canon_exec
from sbg.extraction.dynamic.state_genome import StateGenomeExtractor, canonicalize as canon_state
from sbg.extraction.dynamic.resource_genome import ResourceGenomeExtractor, canonicalize as canon_res
from sbg.extraction.dynamic.temporal_genome import TemporalGenomeExtractor, canonicalize as canon_temp
from sbg.extraction.dynamic.interaction_genome import InteractionGenomeExtractor, canonicalize as canon_inter

# v1 fixed canonical inputs (identical to b08_full_sbg.py)
_V1_FIXED_INPUTS = [-5, 0, 1, 5, 10, 100,
                    [], [1], [1, 2, 3], [5, 4, 3, 2, 1],
                    "", "a", "hello", "hello world"]


def _load_fn_from_source(source: str):
    """Load callable entry point from source string (mirrors b08_full_sbg.py)."""
    _c = getattr(_load_fn_from_source, '_c', 0) + 1
    _load_fn_from_source._c = _c
    mod = types.ModuleType(f"_proxy_mod_{_c}")
    try:
        exec(compile(source, f"<proxy_{_c}>", "exec"), mod.__dict__)
    except Exception:
        return None
    for name in ("main", "solve", "run", "compute"):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    fns = [v for k, v in mod.__dict__.items()
           if callable(v) and not k.startswith('_') and isinstance(v, types.FunctionType)]
    return fns[0] if len(fns) == 1 else None


def _extract_static_genomes(source: str) -> Dict[str, Any]:
    """Extract CONTROL, DATA, ERROR genomes from source."""
    result = {}
    try:
        result["CONTROL"] = canon_ctrl(ControlGenomeExtractor().extract(source))
    except Exception:
        pass
    try:
        result["DATA"] = canon_data(DataGenomeExtractor().extract(source))
    except Exception:
        pass
    try:
        result["ERROR"] = canon_err(ErrorGenomeExtractor().extract(source))
    except Exception:
        pass
    return result


def _extract_dynamic_genomes(source: str) -> Dict[str, Any]:
    """Extract STATE, RESOURCE, TEMPORAL, INTERACTION, EXECUTION genomes via Tracer."""
    fn = _load_fn_from_source(source)
    if fn is None:
        return {}
    tracer = Tracer()
    try:
        traces = tracer.trace(fn, _V1_FIXED_INPUTS, max_events=5000)
    except Exception:
        return {}
    result = {}
    for name, extractor, canon in [
        ("EXECUTION", ExecutionGenomeExtractor(), canon_exec),
        ("STATE", StateGenomeExtractor(), canon_state),
        ("RESOURCE", ResourceGenomeExtractor(), canon_res),
        ("TEMPORAL", TemporalGenomeExtractor(), canon_temp),
        ("INTERACTION", InteractionGenomeExtractor(), canon_inter),
    ]:
        try:
            result[name] = canon(extractor.extract(traces))
        except Exception:
            pass
    return result


# LRU cache keyed by resolved file path
@lru_cache(maxsize=512)
def _cached_extract_genome(resolved_path: str) -> Optional[Dict[str, Any]]:
    """Extract full 8-dim v1 genome from a file path. Cached by resolved path."""
    try:
        source = pathlib.Path(resolved_path).read_text(encoding="utf-8")
    except Exception:
        return None
    genome = {}
    genome.update(_extract_static_genomes(source))
    genome.update(_extract_dynamic_genomes(source))
    return genome if genome else None


def v1_behavioral_distance(path_a: str, path_b: str) -> Optional[float]:
    """
    Compute full v1 behavioral_distance() between two Python source files.

    Returns a float in [0, 1], or None if either genome fails to extract.
    This is the same distance that produces AUROC=0.4237 in v1 SBG evaluation.
    """
    rpa = str(pathlib.Path(path_a).resolve())
    rpb = str(pathlib.Path(path_b).resolve())
    ga = _cached_extract_genome(rpa)
    gb = _cached_extract_genome(rpb)
    if ga is None or gb is None:
        return None
    result = behavioral_distance(ga, gb, DEFAULT_WEIGHTS)
    return float(result["total_distance"])


def v1_behavioral_similarity(path_a: str, path_b: str) -> Optional[float]:
    """
    Compute full v1 behavioral similarity (1 - behavioral_distance).

    Returns a float in [0, 1], or None on extraction failure.
    """
    d = v1_behavioral_distance(path_a, path_b)
    return None if d is None else 1.0 - d
