"""
experiments/v4/phase7_robustness.py
=====================================
Phase 7 — Per-Transformation Robustness Breakdown

SCIENTIFIC QUESTION:
  Which transformation types does SBG V3 handle well vs. poorly?
  Does SBG remain stable (low distance) under semantics-PRESERVING transforms?
  Does SBG detect semantic changes (high distance) under semantics-CHANGING transforms?

METHODOLOGY:
  - Use frozen test set (744 pairs)
  - Group pairs by transformation_type (SP-2, SP-3, ..., SC-1, SC-2, ...)
  - Compute per-transformation AUROC where n >= 9 pairs
  - For SP (preserving) transforms: ideal AUROC ~ 0.5 (correctly neutral)
  - For SC (changing) transforms: ideal AUROC ~ high (correctly detects change)
  - Report: mean similarity per type, AUROC per type, stability under SP
  - Flag: transformations where SBG V3 has AUROC < 0.4 or > 0.6

  CRITICAL INVARIANCE TEST:
  - For semantics-PRESERVING pairs: mean SBG distance should be LOW (< 0.2)
  - This is the SEMANTIC INVARIANCE claim: SBG should not fire on SP transforms

OUTPUT: artifacts/v4/ROBUSTNESS_PER_TRANSFORM.json
"""
from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import sys
import types
from typing import Any, Callable, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sbg.v2.execution.runner import SandboxRunner
from sbg.v3.genome import DynamicGenomeExtractorV3, distance_v3
from sbg.v3.metrics import compute_auroc_v3, bootstrap_auroc_ci

ARTIFACT_OUT = REPO_ROOT / "artifacts" / "v4" / "ROBUSTNESS_PER_TRANSFORM.json"

V3_INPUTS: List[Any] = [
    [], [1], [3, 1, 4, 1, 5, 9, 2, 6], [10, 9, 8, 7, 6, 5],
    [0, 0, 0, 0], [2, 1], [-3, 0, 3], list(range(8)),
    list(range(3)), list(range(16)),
]

_runner = SandboxRunner()
_extractor = DynamicGenomeExtractorV3()
_genome_cache: Dict[str, Any] = {}


def _load_fn(path: str) -> Optional[Callable]:
    p = pathlib.Path(path)
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location("_p7prog", str(p))
    if not spec or not spec.loader:
        return None
    mod = types.ModuleType("_p7prog")
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
        if not nm.startswith("_") and getattr(obj, "__module__", None) == "_p7prog":
            return obj
    return None


def _get_genome(path: str) -> Optional[Any]:
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
    print("PHASE 7 — PER-TRANSFORMATION ROBUSTNESS")
    print("="*60)

    pairs = _load_test_pairs()
    print(f"Loaded {len(pairs)} test pairs.\n")

    # Score all pairs
    per_pair = []
    total = len(pairs)
    for i, p in enumerate(pairs):
        base = str(REPO_ROOT / p["base_path"])
        var = str(REPO_ROOT / p["variant_path"])
        g1 = _get_genome(base)
        g2 = _get_genome(var)
        if g1 is None or g2 is None:
            sim = None
        else:
            sim = round(1.0 - distance_v3(g1, g2), 6)
        lbl = 0 if p["semantic_relation"] == "EQUIVALENT" else 1
        per_pair.append({
            "pair_id": p["pair_id"],
            "transformation_type": p["transformation_type"],
            "label": lbl,
            "similarity": sim,
            "base_id": p["base_id"],
        })
        if (i+1) % 100 == 0:
            print(f"  {i+1}/{total} pairs scored", flush=True)

    # Group by transformation type
    by_type: Dict[str, List] = {}
    for r in per_pair:
        t = r["transformation_type"]
        by_type.setdefault(t, []).append(r)

    # Compute per-type stats
    type_results = {}
    for ttype, rows in sorted(by_type.items()):
        valid = [(r["similarity"], r["label"]) for r in rows if r["similarity"] is not None]
        n = len(valid)
        n_pos = sum(1 for _, l in valid if l == 1)
        n_neg = sum(1 for _, l in valid if l == 0)
        sims = [s for s, _ in valid]
        labels = [l for _, l in valid]

        if n < 3:
            auroc = None
            ci = None
        elif n_pos == 0 or n_neg == 0:
            # Homogeneous label set — cannot compute AUROC
            auroc = None
            ci = None
        else:
            auroc = round(compute_auroc_v3(sims, labels), 6)
            ci_l, ci_u = bootstrap_auroc_ci(sims, labels, n_bootstrap=300, seed=42)
            ci = [round(ci_l, 6), round(ci_u, 6)]

        mean_sim = round(sum(sims)/len(sims), 6) if sims else None

        # For SP (preserving) transforms: low distance = good (invariant)
        # For SC (changing) transforms: high distance = good (detected)
        is_preserving = ttype.startswith("SP") or ttype.startswith("sp")
        is_changing = ttype.startswith("SC") or ttype.startswith("sc")

        # Invariance score for SP: fraction of pairs with sim >= 0.7 (low dist)
        if is_preserving:
            invariance = sum(1 for s in sims if s >= 0.7) / len(sims) if sims else None
        else:
            invariance = None

        type_results[ttype] = {
            "n_total": len(rows),
            "n_valid": n,
            "n_positive_changed": n_pos,
            "n_negative_equiv": n_neg,
            "label_type": "PRESERVING" if is_preserving else ("CHANGING" if is_changing else "MIXED"),
            "mean_similarity": mean_sim,
            "auroc": auroc,
            "auroc_ci": ci,
            "invariance_rate_sp": invariance,
        }

    # Summary statistics
    sp_aurocs = [r["auroc"] for r in type_results.values()
                 if r["label_type"] == "PRESERVING" and r["auroc"] is not None]
    sc_aurocs = [r["auroc"] for r in type_results.values()
                 if r["label_type"] == "CHANGING" and r["auroc"] is not None]

    # Identify failure modes
    failures = []
    for ttype, r in type_results.items():
        if r["auroc"] is not None:
            if r["label_type"] == "CHANGING" and r["auroc"] < 0.45:
                failures.append({"type": ttype, "auroc": r["auroc"],
                                  "issue": "FAILS_TO_DETECT_SEMANTIC_CHANGE"})
            elif r["label_type"] == "PRESERVING":
                # For SP, we want mean_sim HIGH (SBG thinks they're equivalent)
                if r["mean_similarity"] is not None and r["mean_similarity"] < 0.5:
                    failures.append({"type": ttype, "mean_sim": r["mean_similarity"],
                                     "issue": "FALSE_POSITIVE_ON_PRESERVING_TRANSFORM"})

    summary = {
        "experiment": "PHASE7_ROBUSTNESS_PER_TRANSFORM",
        "version": "v4",
        "n_test_pairs": len(pairs),
        "n_transformation_types": len(by_type),
        "per_type_results": type_results,
        "aggregate": {
            "n_sp_types_evaluated": len(sp_aurocs),
            "n_sc_types_evaluated": len(sc_aurocs),
            "mean_sp_auroc": round(sum(sp_aurocs)/len(sp_aurocs), 6) if sp_aurocs else None,
            "mean_sc_auroc": round(sum(sc_aurocs)/len(sc_aurocs), 6) if sc_aurocs else None,
        },
        "failure_modes": failures,
        "methodology": {
            "note": "SP = semantics-preserving (EQUIV label); SC = semantics-changing (CHANGED label)",
            "ideal_sp_behavior": "mean_similarity >= 0.7 (SBG correctly finds SP variants similar)",
            "ideal_sc_behavior": "AUROC > 0.6 (SBG correctly detects semantic changes)",
            "n_bootstrap": 300,
            "auroc": "WMW tie-aware",
        }
    }

    ARTIFACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_OUT, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[PHASE7] Saved → {ARTIFACT_OUT}")
    print(f"\nTransformation types found: {len(by_type)}")
    for ttype, r in sorted(type_results.items()):
        auroc_str = f"AUROC={r['auroc']:.4f}" if r['auroc'] is not None else "AUROC=N/A"
        sim_str = f"mean_sim={r['mean_similarity']:.4f}" if r['mean_similarity'] is not None else ""
        print(f"  {ttype:12s}  n={r['n_valid']:3d}  {r['label_type']:10s}  {auroc_str}  {sim_str}")

    if failures:
        print(f"\n⚠ Failure modes detected ({len(failures)}):")
        for f in failures:
            print(f"  {f}")


if __name__ == "__main__":
    main()
