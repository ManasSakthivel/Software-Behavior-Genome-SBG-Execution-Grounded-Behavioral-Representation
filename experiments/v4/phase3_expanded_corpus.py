"""
experiments/v4/phase3_expanded_corpus.py
==========================================
Phase 3 — Expanded Corpus Evaluation

SCIENTIFIC QUESTION:
  Does SBG V3 generalize beyond the 13 frozen test programs?
  What is the AUROC on the remaining 47 programs (DEV+TRAIN+VAL splits)?

METHODOLOGY:
  The 13 test programs are FROZEN and already evaluated (AUROC=0.5455).
  We evaluate SBG V3 on the DEV split (10 programs) as a generalization check.
  We also compute per-program AUROC to identify which programs SBG handles well.

  NOTE: We use DEV pairs (pairs_dev.jsonl), NOT test pairs, to avoid contamination.
  The DEV threshold was selected during v3 evaluation — we use the SAME threshold
  from the v3 frozen result to avoid further test-set touching.

OUTPUT: artifacts/v4/EXPANDED_CORPUS_EVAL.json
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

ARTIFACT_OUT = REPO_ROOT / "artifacts" / "v4" / "EXPANDED_CORPUS_EVAL.json"

# Threshold from frozen v3 dev evaluation
V3_FROZEN_THRESHOLD = 0.5  # Will be overridden by loading artifacts/v3/B07/results_dev.json

V3_INPUTS: List[Any] = [
    [], [1], [3, 1, 4, 1, 5, 9, 2, 6], [10, 9, 8, 7, 6, 5],
    [0, 0, 0, 0], [2, 1], [-3, 0, 3], list(range(8)),
    list(range(3)), list(range(16)),
]

_runner = SandboxRunner()
_extractor = DynamicGenomeExtractorV3()
_genome_cache: Dict[str, Any] = {}


def _load_frozen_threshold() -> float:
    """Load the threshold from frozen v3 dev results."""
    try:
        p = REPO_ROOT / "artifacts" / "v3" / "B07" / "results_dev.json"
        with open(p) as f:
            data = json.load(f)
        return float(data.get("threshold", 0.5))
    except Exception:
        return 0.5


def _load_fn(path: str) -> Optional[Callable]:
    p = pathlib.Path(path)
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location("_p3prog", str(p))
    if not spec or not spec.loader:
        return None
    mod = types.ModuleType("_p3prog")
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
        if not nm.startswith("_") and getattr(obj, "__module__", None) == "_p3prog":
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
    n_p = 1
    try:
        n_p = len(inspect.signature(fn).parameters)
    except Exception:
        pass
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


def _load_pairs(split: str) -> list:
    path = REPO_ROOT / "benchmark" / "datasets" / f"pairs_{split}.jsonl"
    pairs = []
    with open(path) as fh:
        for line in fh:
            ln = line.strip()
            if ln:
                pairs.append(json.loads(ln))
    return pairs


def main() -> None:
    print("\n" + "="*60)
    print("PHASE 3 — EXPANDED CORPUS EVALUATION")
    print("="*60)

    threshold = _load_frozen_threshold()
    print(f"Loaded frozen threshold: {threshold:.4f}")

    dev_pairs = _load_pairs("dev")
    val_pairs = _load_pairs("val")
    print(f"DEV pairs: {len(dev_pairs)}")
    print(f"VAL pairs: {len(val_pairs)}\n")

    def _score_split(pairs: list, split_name: str) -> Dict:
        sims, labels, pair_ids = [], [], []
        n_missing = 0

        print(f"Scoring {len(pairs)} {split_name} pairs...", flush=True)
        for i, p in enumerate(pairs):
            base = str(REPO_ROOT / p["base_path"])
            var = str(REPO_ROOT / p["variant_path"])
            g1 = _get_genome(base)
            g2 = _get_genome(var)
            lbl = 0 if p["semantic_relation"] == "EQUIVALENT" else 1
            if g1 is None or g2 is None:
                n_missing += 1
                continue
            sim = 1.0 - distance_v3(g1, g2)
            sims.append(sim)
            labels.append(lbl)
            pair_ids.append(pathlib.Path(p["base_path"]).stem)
            if (i+1) % 100 == 0:
                print(f"  {i+1}/{len(pairs)}", flush=True)

        if not sims:
            return {"auroc": 0.5, "ci": [0.5, 0.5], "n_valid": 0, "n_missing": n_missing}

        auroc = compute_auroc_v3(sims, labels)
        ci_l, ci_u = bootstrap_auroc_ci(sims, labels, pair_ids=pair_ids,
                                         n_bootstrap=300, seed=42)

        # Per-program AUROC
        by_prog: Dict[str, List] = {}
        for sim, lbl, pid in zip(sims, labels, pair_ids):
            by_prog.setdefault(pid, []).append((sim, lbl))

        per_prog = {}
        for prog, data in sorted(by_prog.items()):
            ps = [d[0] for d in data]
            pl = [d[1] for d in data]
            n_pos = sum(pl)
            n_neg = len(pl) - n_pos
            if n_pos > 0 and n_neg > 0:
                per_prog[prog] = {
                    "auroc": round(compute_auroc_v3(ps, pl), 6),
                    "n": len(pl),
                    "n_pos": n_pos,
                    "n_neg": n_neg,
                }
            else:
                per_prog[prog] = {"auroc": None, "n": len(pl), "n_pos": n_pos, "n_neg": n_neg}

        return {
            "auroc": round(auroc, 6),
            "ci": [round(ci_l, 6), round(ci_u, 6)],
            "n_valid": len(sims),
            "n_missing": n_missing,
            "per_program": per_prog,
        }

    dev_result = _score_split(dev_pairs, "DEV")
    val_result = _score_split(val_pairs, "VAL")

    # Reference: frozen test result
    test_auroc = 0.545537  # from artifacts/v3/FINAL_RESULTS.json

    print(f"\n{'='*50}")
    print(f"TEST  AUROC (frozen v3): {test_auroc:.4f}")
    print(f"DEV   AUROC: {dev_result['auroc']:.4f}  CI={dev_result['ci']}")
    print(f"VAL   AUROC: {val_result['auroc']:.4f}  CI={val_result['ci']}")

    summary = {
        "experiment": "PHASE3_EXPANDED_CORPUS",
        "version": "v4",
        "test_auroc_frozen": test_auroc,
        "test_n_programs": 13,
        "dev_result": dev_result,
        "val_result": val_result,
        "generalization_analysis": {
            "test_vs_dev_delta": round(test_auroc - dev_result["auroc"], 6),
            "test_vs_val_delta": round(test_auroc - val_result["auroc"], 6),
            "verdict": (
                "GENERALIZES" if abs(test_auroc - dev_result["auroc"]) < 0.05
                else "PERFORMANCE_VARIES_BY_SPLIT"
            ),
        },
        "methodology": {
            "note": "DEV/VAL pairs used; TEST set remains frozen/untouched",
            "threshold": f"{threshold:.4f} (from frozen v3 dev evaluation)",
            "auroc": "WMW tie-aware",
        }
    }

    ARTIFACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_OUT, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[PHASE3] Saved → {ARTIFACT_OUT}")


if __name__ == "__main__":
    main()
