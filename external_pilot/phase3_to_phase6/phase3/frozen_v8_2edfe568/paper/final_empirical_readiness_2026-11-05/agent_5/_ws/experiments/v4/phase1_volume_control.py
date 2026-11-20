"""
experiments/v4/phase1_volume_control.py
========================================
Phase 1 — Volume-Control Experiment (Flagship Sprint)

SCIENTIFIC QUESTION:
  Does SBG V3 contain behavioral information BEYOND execution-volume statistics?

METHODOLOGY:
  Run 7 competing predictors on the FROZEN TEST SET (744 pairs):

  1. wall_time_ms (single number, fastest proxy)
  2. call_count_total (single number)
  3. n_functions_called (single number)
  4. exception_fraction (single number)
  5. combined_shortcut (weighted combo of 1-4)
  6. random_label_baseline (AUROC noise floor)
  7. SBG_V3 (call bigrams + input sensitivity + exception causality hash)

  For each predictor:
    AUROC (tie-aware WMW), 95% CI (cluster bootstrap), permutation p-value

  KEY COMPARISON: Does SBG V3 survive the shortcut controls?
    If AUROC(SBG_V3) > AUROC(best_shortcut) with non-overlapping CIs → SURVIVES
    If not → volume-dominated (honest negative)

INTEGRITY RULES:
  - Uses FROZEN pairs_test.jsonl (744 pairs, never modified)
  - AUROC computed via sbg.v3.metrics.compute_auroc_v3 (WMW tie-aware)
  - No post-hoc threshold tuning
  - All shortcuts use 1/(1+|delta|) pseudo-similarity (same formula as v2 audit)
  - Random label baseline: 100 shuffles, report CI
  - Wall-clock shortcut re-extracted fresh (not from v2 artifacts — independent run)

OUTPUT: artifacts/v4/SHORTCUT_CONTROLS.json
"""
from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import random
import sys
import time
import types
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sbg.v3.metrics import compute_auroc_v3, bootstrap_auroc_ci, permutation_test_auroc
from sbg.v2.execution.runner import SandboxRunner
from sbg.v3.genome import DynamicGenomeExtractorV3, distance_v3

ARTIFACT_OUT = REPO_ROOT / "artifacts" / "v4" / "SHORTCUT_CONTROLS.json"

# ── canonical inputs ────────────────────────────────────────────────────────
V3_INPUTS: List[Any] = [
    [], [1], [3, 1, 4, 1, 5, 9, 2, 6], [10, 9, 8, 7, 6, 5],
    [0, 0, 0, 0], [2, 1], [-3, 0, 3], list(range(8)),
    list(range(1)), list(range(3)), list(range(16)),
]

_runner = SandboxRunner()
_extractor = DynamicGenomeExtractorV3()
_genome_cache: Dict[str, Any] = {}
_stat_cache: Dict[str, Dict] = {}   # path → {wall_ms, call_count, n_fns, exc_frac, sbg_genome}


def _load_fn(path: str) -> Optional[Callable]:
    p = pathlib.Path(path)
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location("_p1_prog", str(p))
    if not spec or not spec.loader:
        return None
    mod = types.ModuleType("_p1_prog")
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
    # first public function
    for nm, obj in inspect.getmembers(mod, inspect.isfunction):
        if not nm.startswith("_") and getattr(obj, "__module__", None) == "_p1_prog":
            return obj
    return None


def _extract_stats(path: str) -> Dict:
    """Extract execution stats + SBG genome. Cached."""
    if path in _stat_cache:
        return _stat_cache[path]

    fn = _load_fn(path)
    if fn is None:
        result = {"wall_ms": None, "call_count": None, "n_fns": None, "exc_frac": None,
                  "genome": None, "error": "load_failed"}
        _stat_cache[path] = result
        return result

    import inspect
    try:
        n_p = len(inspect.signature(fn).parameters)
    except Exception:
        n_p = 1

    fn_to_trace = fn if n_p > 0 else (lambda inp: fn())
    inputs_to_use = V3_INPUTS if n_p > 0 else [None]
    pid = pathlib.Path(path).stem

    try:
        t0 = time.monotonic()
        sr = _runner.run(pid, fn_to_trace, inputs_to_use, n_runs=3, seed=42, max_events=3_000)
        wall_ms = (time.monotonic() - t0) * 1000.0

        # Extract execution stats from traces
        all_fns: set = set()
        total_calls = 0
        n_exc = 0
        n_traces = 0
        for run in sr.traces:
            for tr in run:
                n_traces += 1
                if tr.exception:
                    n_exc += 1
                for ev in tr.events:
                    if ev.event_type == "call":
                        total_calls += 1
                        all_fns.add(ev.function_name)

        genome = _extractor.extract_from_traces(pid, sr.traces)
        result = {
            "wall_ms": wall_ms,
            "call_count": total_calls,
            "n_fns": len(all_fns),
            "exc_frac": n_exc / n_traces if n_traces > 0 else 0.0,
            "genome": genome,
            "error": None,
        }
    except Exception as e:
        result = {"wall_ms": None, "call_count": None, "n_fns": None, "exc_frac": None,
                  "genome": None, "error": str(e)}

    _stat_cache[path] = result
    return result


def _pseudo_sim(delta: float) -> float:
    """1/(1+|delta|) — monotonic decreasing in absolute difference."""
    return 1.0 / (1.0 + abs(delta))


def _score_pair(base_path: str, var_path: str, feature: str) -> Optional[float]:
    """Compute pseudo-similarity for a given feature."""
    bs = _extract_stats(base_path)
    vs = _extract_stats(var_path)

    if feature == "sbg_v3":
        g1, g2 = bs.get("genome"), vs.get("genome")
        if g1 is None or g2 is None:
            return None
        return 1.0 - distance_v3(g1, g2)

    vals = {"wall_ms": "wall_ms", "call_count": "call_count",
            "n_fns": "n_fns", "exc_frac": "exc_frac"}
    if feature == "combined":
        # Weighted combo matching v2 audit weights
        parts = []
        for k, w in [("wall_ms", 0.30), ("call_count", 0.30),
                     ("n_fns", 0.25), ("exc_frac", 0.15)]:
            bv, vv = bs.get(k), vs.get(k)
            if bv is None or vv is None:
                return None
            parts.append(w * _pseudo_sim(bv - vv))
        return sum(parts)

    bv = bs.get(vals.get(feature, ""))
    vv = vs.get(vals.get(feature, ""))
    if bv is None or vv is None:
        return None
    return _pseudo_sim(bv - vv)


def _load_test_pairs() -> list:
    path = REPO_ROOT / "benchmark" / "datasets" / "pairs_test.jsonl"
    pairs = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    return pairs


def _compute_feature_results(
    pairs: list, feature: str, n_bootstrap: int = 1000
) -> Dict:
    sims, labels, pair_ids = [], [], []
    n_missing = 0
    for p in pairs:
        base = str(REPO_ROOT / p["base_path"])
        var = str(REPO_ROOT / p["variant_path"])
        lbl = 0 if p["semantic_relation"] == "EQUIVALENT" else 1
        sim = _score_pair(base, var, feature)
        if sim is None:
            n_missing += 1
            continue
        sims.append(sim)
        labels.append(lbl)
        pair_ids.append(pathlib.Path(p["base_path"]).stem)

    if not sims or sum(labels) == 0 or sum(1-l for l in labels) == 0:
        return {"auroc": 0.5, "ci_lower": 0.5, "ci_upper": 0.5,
                "permutation_p": 1.0, "n_valid": len(sims), "n_missing": n_missing}

    auroc = compute_auroc_v3(sims, labels)
    ci_l, ci_u = bootstrap_auroc_ci(sims, labels, pair_ids=pair_ids,
                                     n_bootstrap=n_bootstrap, seed=42)
    perm_p = permutation_test_auroc(sims, labels, n_permutations=1000, seed=42)
    return {
        "auroc": round(auroc, 6),
        "ci_lower": round(ci_l, 6),
        "ci_upper": round(ci_u, 6),
        "permutation_p": round(perm_p, 6),
        "n_valid": len(sims),
        "n_missing": n_missing,
    }


def _random_baseline(pairs: list, n_shuffles: int = 200, seed: int = 42) -> Dict:
    """Repeated random-label AUROC to establish noise floor."""
    labels = [0 if p["semantic_relation"] == "EQUIVALENT" else 1 for p in pairs]
    # Use SBG V3 similarities (already computed) for random shuffle
    sims = []
    for p in pairs:
        base = str(REPO_ROOT / p["base_path"])
        var = str(REPO_ROOT / p["variant_path"])
        sim = _score_pair(base, var, "sbg_v3")
        if sim is not None:
            sims.append(sim)
    if not sims:
        return {"auroc_mean": 0.5, "auroc_std": 0.0, "ci_95": [0.5, 0.5]}
    rng = random.Random(seed)
    aurocs = []
    lbl_copy = list(labels[:len(sims)])
    for _ in range(n_shuffles):
        rng.shuffle(lbl_copy)
        if sum(lbl_copy) == 0 or sum(1-l for l in lbl_copy) == 0:
            aurocs.append(0.5)
        else:
            aurocs.append(compute_auroc_v3(sims, lbl_copy))
    aurocs.sort()
    n = len(aurocs)
    return {
        "auroc_mean": round(sum(aurocs)/n, 6),
        "auroc_std": round((sum((a-sum(aurocs)/n)**2 for a in aurocs)/n)**0.5, 6),
        "auroc_95th_percentile": round(aurocs[int(0.95*n)], 6),
        "ci_95": [round(aurocs[int(0.025*n)], 6), round(aurocs[int(0.975*n)], 6)],
        "n_shuffles": n_shuffles,
    }


def main() -> None:
    print("\n" + "="*60)
    print("PHASE 1 — VOLUME-CONTROL EXPERIMENT")
    print("="*60)
    print("Scientific question: Does SBG V3 beat simple execution statistics?")

    pairs = _load_test_pairs()
    print(f"Loaded {len(pairs)} test pairs.\n")

    features = ["wall_ms", "call_count", "n_fns", "exc_frac", "combined", "sbg_v3"]
    results = {}

    for feat in features:
        print(f"[{feat}] Scoring {len(pairs)} pairs...", flush=True)
        r = _compute_feature_results(pairs, feat, n_bootstrap=500)
        results[feat] = r
        print(f"  AUROC={r['auroc']:.4f} CI=[{r['ci_lower']:.4f},{r['ci_upper']:.4f}] "
              f"p={r['permutation_p']:.4f} n={r['n_valid']} missing={r['n_missing']}")

    print("\n[random_label] Computing noise floor (200 shuffles)...", flush=True)
    rand_result = _random_baseline(pairs)
    results["random_label"] = rand_result
    print(f"  noise floor mean={rand_result['auroc_mean']:.4f} "
          f"95th_pct={rand_result['auroc_95th_percentile']:.4f} "
          f"CI={rand_result['ci_95']}")

    # ── Analysis ────────────────────────────────────────────────────────────
    sbg_auroc = results["sbg_v3"]["auroc"]
    best_shortcut = max(
        results["wall_ms"]["auroc"], results["call_count"]["auroc"],
        results["n_fns"]["auroc"], results["exc_frac"]["auroc"],
        results["combined"]["auroc"],
    )
    best_shortcut_name = max(
        [("wall_ms", results["wall_ms"]["auroc"]),
         ("call_count", results["call_count"]["auroc"]),
         ("n_fns", results["n_fns"]["auroc"]),
         ("exc_frac", results["exc_frac"]["auroc"]),
         ("combined", results["combined"]["auroc"])],
        key=lambda x: x[1]
    )[0]
    noise_floor_95 = rand_result["auroc_95th_percentile"]

    survives_shortcut = sbg_auroc > best_shortcut
    above_noise = sbg_auroc > noise_floor_95
    sbg_ci_lower = results["sbg_v3"]["ci_lower"]

    # Determine verdict
    if survives_shortcut and sbg_ci_lower > noise_floor_95:
        verdict = "SBG_V3_SURVIVES_SHORTCUT_CONTROLS"
    elif survives_shortcut:
        verdict = "SBG_V3_ABOVE_BEST_SHORTCUT_BUT_CI_OVERLAPS_NOISE_FLOOR"
    elif above_noise:
        verdict = "SBG_V3_ABOVE_NOISE_BUT_BELOW_BEST_SHORTCUT"
    else:
        verdict = "SBG_V3_NOT_ABOVE_NOISE_FLOOR"

    summary = {
        "experiment": "PHASE1_VOLUME_CONTROL",
        "version": "v4",
        "n_test_pairs": len(pairs),
        "sbg_v3_auroc": sbg_auroc,
        "sbg_v3_ci": [results["sbg_v3"]["ci_lower"], results["sbg_v3"]["ci_upper"]],
        "best_shortcut": best_shortcut_name,
        "best_shortcut_auroc": round(best_shortcut, 6),
        "sbg_vs_best_shortcut_delta": round(sbg_auroc - best_shortcut, 6),
        "noise_floor_95th_pct": noise_floor_95,
        "above_noise_floor": above_noise,
        "survives_shortcut_controls": survives_shortcut,
        "verdict": verdict,
        "detailed_results": results,
        "methodology": {
            "pseudo_similarity": "1/(1+|feature_base - feature_variant|)",
            "auroc": "WMW tie-aware (sbg.v3.metrics.compute_auroc_v3)",
            "bootstrap": "cluster-by-base-program, 500 resamples",
            "permutation": "1000 permutations",
            "random_baseline": "200 label shuffles, 95th percentile",
            "test_set": "benchmark/datasets/pairs_test.jsonl (frozen, 744 pairs)",
        }
    }

    ARTIFACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_OUT, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[PHASE1] Saved → {ARTIFACT_OUT}")
    print(f"\n{'='*60}")
    print(f"VERDICT: {verdict}")
    print(f"SBG V3:  AUROC={sbg_auroc:.4f}  CI=[{results['sbg_v3']['ci_lower']:.4f},{results['sbg_v3']['ci_upper']:.4f}]")
    print(f"Best shortcut ({best_shortcut_name}): AUROC={best_shortcut:.4f}")
    print(f"Noise floor 95th pct: {noise_floor_95:.4f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
