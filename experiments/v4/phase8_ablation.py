"""
experiments/v4/phase8_ablation.py
===================================
Phase 8 — Feature Ablation Study

SCIENTIFIC QUESTION:
  Which features in DynamicGenomeV3 actually carry the discriminative signal?
  Can any single feature alone match or beat the full model?
  What does removing each feature do to AUROC?

METHODOLOGY:
  For each feature group, re-weight the distance_v3() formula to give
  weight=0 to the ablated components (redistribute to remaining).
  Compare AUROC of ablated model vs. full model.

  Feature groups:
    A. full_model (baseline, all weights)
    B. ablate_call_bigrams (set W_seq=0, redistribute)
    C. ablate_input_sensitivity (set W_inp=0)
    D. ablate_exc_causality (set W_exc2=0)
    E. ablate_call_freq (set W_freq=0)
    F. ablate_coverage (set W_cov=0)
    G. ablate_depth (set W_dep=0)
    H. ablate_consistency (set W_con=0)
    I. ablate_exception (set W_exc=0)
    J. volume_only (only W_cov + W_freq, zeroes for all v3 features)
    K. order_only (only W_seq, zero all volume features)
    L. single_bigrams (only call_transition_bigrams)
    M. single_coverage (only coverage)

  Preregistered comparison criterion:
    A feature "matters" if removing it reduces AUROC by >= 0.01.

OUTPUT: artifacts/v4/FEATURE_ABLATION.json
"""
from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import sys
import types
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sbg.v2.execution.runner import SandboxRunner
from sbg.v3.genome import DynamicGenomeExtractorV3, DynamicGenomeV3
from sbg.v3.metrics import compute_auroc_v3, bootstrap_auroc_ci

ARTIFACT_OUT = REPO_ROOT / "artifacts" / "v4" / "FEATURE_ABLATION.json"

V3_INPUTS: List[Any] = [
    [], [1], [3, 1, 4, 1, 5, 9, 2, 6], [10, 9, 8, 7, 6, 5],
    [0, 0, 0, 0], [2, 1], [-3, 0, 3], list(range(8)),
    list(range(3)), list(range(16)),
]

_runner = SandboxRunner()
_extractor = DynamicGenomeExtractorV3()
_genome_cache: Dict[str, Optional[DynamicGenomeV3]] = {}


def _load_fn(path: str) -> Optional[Callable]:
    p = pathlib.Path(path)
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location("_p8prog", str(p))
    if not spec or not spec.loader:
        return None
    mod = types.ModuleType("_p8prog")
    old = sys.stdout; sys.stdout = io.StringIO()
    try:
        spec.loader.exec_module(mod)  # type: ignore
    except Exception:
        sys.stdout = old
        return None
    finally:
        sys.stdout = old
    import inspect
    for nm in ("sort", "search", "run", "main", "solve", "process", "compute",
               "encode", "decode", "parse", "validate"):
        fn = getattr(mod, nm, None)
        if callable(fn) and isinstance(fn, types.FunctionType):
            return fn
    for nm, obj in inspect.getmembers(mod, inspect.isfunction):
        if not nm.startswith("_") and getattr(obj, "__module__", None) == "_p8prog":
            return obj
    return None


def _get_genome(path: str) -> Optional[DynamicGenomeV3]:
    if path in _genome_cache:
        return _genome_cache[path]
    fn = _load_fn(path)
    if fn is None:
        _genome_cache[path] = None
        return None
    import inspect
    try:
        n_p = len(inspect.signature(fn).parameters)
    except Exception:
        n_p = 1
    fn_to_trace = fn if n_p > 0 else (lambda inp: fn())
    inputs_to_use = V3_INPUTS if n_p > 0 else [None]
    pid = pathlib.Path(path).stem
    try:
        sr = _runner.run(pid, fn_to_trace, inputs_to_use, n_runs=3, seed=42, max_events=3_000)
        genome = _extractor.extract_from_traces(pid, sr.traces)
    except Exception:
        genome = None
    _genome_cache[path] = genome
    return genome


def _distance_ablated(g1: DynamicGenomeV3, g2: DynamicGenomeV3, config: Dict[str, float]) -> float:
    """
    Flexible ablated distance function.
    config = {W_cov, W_seq, W_freq, W_exc, W_dep, W_con, W_inp, W_exc2}
    All weights should sum to 1.0.
    """
    W_cov = config.get("W_cov", 0.0)
    W_seq = config.get("W_seq", 0.0)
    W_freq = config.get("W_freq", 0.0)
    W_exc = config.get("W_exc", 0.0)
    W_dep = config.get("W_dep", 0.0)
    W_con = config.get("W_con", 0.0)
    W_inp = config.get("W_inp", 0.0)
    W_exc2 = config.get("W_exc2", 0.0)

    max_cov = max(g1.coverage_size, g2.coverage_size, 1)
    d_coverage = abs(g1.coverage_size - g2.coverage_size) / max_cov

    all_bigrams = set(g1.call_transition_bigrams) | set(g2.call_transition_bigrams)
    if not all_bigrams:
        d_call_trans = 0.0
    else:
        l1 = sum(abs(g1.call_transition_bigrams.get(b, 0.0) - g2.call_transition_bigrams.get(b, 0.0))
                 for b in all_bigrams)
        d_call_trans = min(1.0, l1 / 2.0)

    all_funcs = set(g1.anon_call_freq) | set(g2.anon_call_freq)
    if not all_funcs:
        d_call_freq = 0.0
    else:
        l1 = sum(abs(g1.anon_call_freq.get(f, 0.0) - g2.anon_call_freq.get(f, 0.0))
                 for f in all_funcs)
        d_call_freq = min(1.0, l1 / 2.0)

    s1, s2 = set(g1.exception_type_set), set(g2.exception_type_set)
    union_exc = len(s1 | s2)
    jaccard_exc = 0.0 if union_exc == 0 else (1.0 - len(s1 & s2) / union_exc)
    d_exception = 0.5 * jaccard_exc + 0.5 * abs(g1.exception_rate - g2.exception_rate)

    max_depth = max(g1.call_depth_mean, g2.call_depth_mean, 1.0)
    d_depth = abs(g1.call_depth_mean - g2.call_depth_mean) / max_depth

    d_consistency = abs(g1.coverage_consistency - g2.coverage_consistency)
    d_input_sens = abs(g1.input_sensitivity_score - g2.input_sensitivity_score)
    d_exc_causality = 0.0 if g1.exception_causality_hash == g2.exception_causality_hash else 1.0

    total = (W_cov * d_coverage + W_seq * d_call_trans + W_freq * d_call_freq
             + W_exc * d_exception + W_dep * d_depth + W_con * d_consistency
             + W_inp * d_input_sens + W_exc2 * d_exc_causality)
    return max(0.0, min(1.0, total))


# Ablation configurations (normalized to sum=1.0)
ABLATION_CONFIGS: Dict[str, Dict[str, float]] = {
    "full_model": dict(W_cov=0.20, W_seq=0.25, W_freq=0.20, W_exc=0.10,
                       W_dep=0.10, W_con=0.05, W_inp=0.05, W_exc2=0.05),
    # Remove v3 features
    "no_call_bigrams": dict(W_cov=0.25, W_seq=0.00, W_freq=0.28, W_exc=0.15,
                             W_dep=0.15, W_con=0.07, W_inp=0.05, W_exc2=0.05),
    "no_input_sensitivity": dict(W_cov=0.21, W_seq=0.26, W_freq=0.21, W_exc=0.11,
                                  W_dep=0.11, W_con=0.05, W_inp=0.00, W_exc2=0.05),
    "no_exc_causality": dict(W_cov=0.21, W_seq=0.26, W_freq=0.21, W_exc=0.11,
                              W_dep=0.10, W_con=0.06, W_inp=0.05, W_exc2=0.00),
    "no_all_v3_features": dict(W_cov=0.375, W_seq=0.00, W_freq=0.375, W_exc=0.15,
                                 W_dep=0.10, W_con=0.00, W_inp=0.00, W_exc2=0.00),
    # Remove volume features
    "no_coverage": dict(W_cov=0.00, W_seq=0.30, W_freq=0.25, W_exc=0.15,
                         W_dep=0.12, W_con=0.06, W_inp=0.07, W_exc2=0.05),
    "no_call_freq": dict(W_cov=0.27, W_seq=0.33, W_freq=0.00, W_exc=0.13,
                          W_dep=0.13, W_con=0.07, W_inp=0.07, W_exc2=0.00),
    # Isolated feature tests
    "only_call_bigrams": dict(W_cov=0.00, W_seq=1.00, W_freq=0.00, W_exc=0.00,
                               W_dep=0.00, W_con=0.00, W_inp=0.00, W_exc2=0.00),
    "only_coverage": dict(W_cov=1.00, W_seq=0.00, W_freq=0.00, W_exc=0.00,
                           W_dep=0.00, W_con=0.00, W_inp=0.00, W_exc2=0.00),
    "only_volume": dict(W_cov=0.50, W_seq=0.00, W_freq=0.50, W_exc=0.00,
                         W_dep=0.00, W_con=0.00, W_inp=0.00, W_exc2=0.00),
    "only_exception": dict(W_cov=0.00, W_seq=0.00, W_freq=0.00, W_exc=1.00,
                            W_dep=0.00, W_con=0.00, W_inp=0.00, W_exc2=0.00),
}


def _load_test_pairs() -> list:
    path = REPO_ROOT / "benchmark" / "datasets" / "pairs_test.jsonl"
    pairs = []
    with open(path) as fh:
        for line in fh:
            ln = line.strip()
            if ln:
                pairs.append(json.loads(ln))
    return pairs


def main() -> None:
    print("\n" + "="*60)
    print("PHASE 8 — FEATURE ABLATION STUDY")
    print("="*60)

    pairs = _load_test_pairs()
    print(f"Loaded {len(pairs)} test pairs.\n")

    # Pre-extract all genomes
    print("Pre-extracting genomes...", flush=True)
    all_paths = set()
    for p in pairs:
        all_paths.add(str(REPO_ROOT / p["base_path"]))
        all_paths.add(str(REPO_ROOT / p["variant_path"]))
    for i, path in enumerate(sorted(all_paths)):
        _get_genome(path)
        if (i+1) % 20 == 0:
            print(f"  {i+1}/{len(all_paths)} programs", flush=True)

    ablation_results = {}
    labels = [0 if p["semantic_relation"] == "EQUIVALENT" else 1 for p in pairs]
    pair_ids = [pathlib.Path(p["base_path"]).stem for p in pairs]

    for config_name, weights in ABLATION_CONFIGS.items():
        sims = []
        valid_labels = []
        valid_pair_ids = []
        for p, lbl, pid in zip(pairs, labels, pair_ids):
            g1 = _get_genome(str(REPO_ROOT / p["base_path"]))
            g2 = _get_genome(str(REPO_ROOT / p["variant_path"]))
            if g1 is None or g2 is None:
                continue
            dist = _distance_ablated(g1, g2, weights)
            sims.append(1.0 - dist)
            valid_labels.append(lbl)
            valid_pair_ids.append(pid)

        if not sims:
            auroc = 0.5
            ci = [0.5, 0.5]
        else:
            auroc = compute_auroc_v3(sims, valid_labels)
            ci_l, ci_u = bootstrap_auroc_ci(sims, valid_labels, pair_ids=valid_pair_ids,
                                             n_bootstrap=300, seed=42)
            ci = [round(ci_l, 6), round(ci_u, 6)]

        ablation_results[config_name] = {
            "auroc": round(auroc, 6),
            "auroc_ci": ci,
            "n_valid": len(sims),
            "weights": weights,
        }
        print(f"  {config_name:30s}  AUROC={auroc:.4f}  CI=[{ci[0]:.4f},{ci[1]:.4f}]")

    # Compute deltas vs. full model
    full_auroc = ablation_results["full_model"]["auroc"]
    for name, r in ablation_results.items():
        r["delta_vs_full"] = round(r["auroc"] - full_auroc, 6)
        r["matters"] = abs(r["delta_vs_full"]) >= 0.01

    # Find most important features
    important = {n: r for n, r in ablation_results.items()
                 if r["matters"] and n != "full_model"}

    summary = {
        "experiment": "PHASE8_FEATURE_ABLATION",
        "version": "v4",
        "n_test_pairs": len(pairs),
        "full_model_auroc": full_auroc,
        "ablation_results": ablation_results,
        "important_features": list(important.keys()),
        "criterion": "Feature matters if |AUROC_ablated - AUROC_full| >= 0.01",
        "methodology": {
            "ablation_method": "Set feature weights to 0, normalize remaining weights to sum=1",
            "auroc": "WMW tie-aware",
            "bootstrap": "cluster-by-base-program, 300 resamples",
        }
    }

    ARTIFACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_OUT, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[PHASE8] Saved → {ARTIFACT_OUT}")
    print(f"\nFull model AUROC: {full_auroc:.4f}")
    print(f"Important features (delta >= 0.01): {list(important.keys())}")


if __name__ == "__main__":
    main()
