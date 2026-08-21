"""
baselines/v2/b06_fair_v2.py
==============================
B06-V2-FAIR: Fair dynamic trace baseline using V2 canonical inputs.

Fairness Fix
------------
The original B06 used v1 inputs: int×6, list×4, str×4 (14 inputs, mixed types).
B07-DYNAMIC-V2 uses V2_CANONICAL_INPUTS: 8 list inputs.

For a fair comparison (same inputs, different representation), this script uses
EXACTLY the same V2_CANONICAL_INPUTS as B07, but keeps B06's ORIGINAL feature
extraction (call bigrams, coverage, return type, exception rate).

This isolates the representation variable:
  B06-V2-FAIR vs B07-DYNAMIC-V2 = same inputs, different representations
  B06-ORIGINAL vs B06-V2-FAIR   = same representation, different inputs

SAFEGUARD-5 compliance: B06 re-run with V2 inputs before claiming improvement.
"""
from __future__ import annotations

import collections
import importlib.util
import pathlib
import sys
import threading
import types
from typing import Any, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Import V2 canonical inputs DIRECTLY from B07 — hard reference, not a copy
from baselines.v2.b07_dynamic_v2 import V2_CANONICAL_INPUTS
from baselines.common import (
    load_pairs, pairs_to_labels, find_optimal_threshold,
    compute_metrics, save_results,
)

ARTIFACT_DIR = str(REPO_ROOT / "artifacts" / "v2" / "B06_FAIR")
TIMEOUT = 2.0


def _load_fn(source: str):
    """Load entry point from source string."""
    _counter = getattr(_load_fn, '_counter', 0) + 1
    _load_fn._counter = _counter
    mod = types.ModuleType(f"_b06fair_mod_{_counter}")
    try:
        exec(compile(source, f"<b06fair_{_counter}>", "exec"), mod.__dict__)
    except Exception:
        return None
    for name in ("sort", "search", "run", "main", "solve", "process", "compute",
                 "encode", "decode", "parse", "validate", "execute"):
        fn = getattr(mod, name, None)
        if callable(fn) and isinstance(fn, types.FunctionType):
            return fn
    fns = [v for k, v in mod.__dict__.items()
           if callable(v) and not k.startswith('_') and isinstance(v, types.FunctionType)]
    return fns[0] if len(fns) == 1 else None


def _run_with_timeout(fn, inp, timeout=TIMEOUT):
    """Run fn(inp) with timeout. Returns trace features."""
    result = {"ret_type": None, "calls": [], "lines": set(), "exception": False}

    def worker():
        calls = []
        lines = set()
        old_trace = sys.gettrace()

        def tracer(frame, event, arg):
            if event == "call":
                calls.append(frame.f_code.co_name)
            elif event == "line":
                lines.add(frame.f_lineno)
            return tracer

        sys.settrace(tracer)
        try:
            if isinstance(inp, (list, tuple)):
                ret = fn(*inp) if inp else fn()
            elif isinstance(inp, dict):
                ret = fn(**inp)
            else:
                ret = fn(inp)
            result["ret_type"] = type(ret).__name__
            result["calls"] = calls[:200]
            result["lines"] = lines
        except Exception:
            result["exception"] = True
            result["calls"] = calls[:200]
            result["lines"] = lines
        finally:
            sys.settrace(old_trace)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout=timeout)
    return result


def _extract_trace_features(source: str) -> Dict[str, Any]:
    """Extract flat trace features using V2_CANONICAL_INPUTS."""
    fn = _load_fn(source)
    if fn is None:
        return {"call_bigrams": set(), "coverage": set(),
                "ret_type_hist": {}, "exception_rate": 0.5, "n_traces": 0}

    all_calls = []
    all_lines = set()
    ret_types = []
    n_exc = 0
    n_total = 0

    # Use V2_CANONICAL_INPUTS — IDENTICAL to B07
    for inp in V2_CANONICAL_INPUTS:
        r = _run_with_timeout(fn, inp)
        n_total += 1
        if r["exception"]:
            n_exc += 1
        else:
            if r["ret_type"]:
                ret_types.append(r["ret_type"])
        all_calls.extend(r["calls"])
        all_lines.update(r["lines"])

    bigrams = set()
    for i in range(len(all_calls) - 1):
        bigrams.add((all_calls[i], all_calls[i + 1]))

    ret_hist = collections.Counter(ret_types)
    total_ret = sum(ret_hist.values()) or 1
    ret_hist_norm = {k: v / total_ret for k, v in ret_hist.items()}

    return {
        "call_bigrams": bigrams,
        "coverage": all_lines,
        "ret_type_hist": ret_hist_norm,
        "exception_rate": n_exc / n_total if n_total > 0 else 0.0,
        "n_traces": n_total,
    }


def _jaccard(s1: set, s2: set) -> float:
    if not s1 and not s2:
        return 1.0
    u = s1 | s2
    i = s1 & s2
    return len(i) / len(u)


def _l1_similarity(d1: dict, d2: dict) -> float:
    keys = set(d1) | set(d2)
    if not keys:
        return 1.0
    l1 = sum(abs(d1.get(k, 0.0) - d2.get(k, 0.0)) for k in keys)
    return 1.0 - min(l1 / 2.0, 1.0)


_cache: Dict[str, Any] = {}


def _get_features(source: str) -> Dict[str, Any]:
    key = hash(source[:500])
    if key not in _cache:
        _cache[key] = _extract_trace_features(source)
    return _cache[key]


def score_fn(src_a: str, src_b: str) -> float:
    """Full trace similarity with V2 canonical inputs (B06 formula, V2 inputs)."""
    fa = _get_features(src_a)
    fb = _get_features(src_b)
    # Phase 4 Wave 1 fairness fix: if either program's entry function could
    # not be discovered/executed, _jaccard({}, {}) == 1.0 would fabricate a
    # fake MAXIMUM similarity score. Return the same neutral 0.5 imputation
    # convention B07 uses instead (docs/v2/ENTRYPOINT_LIMITATION.md).
    if fa["n_traces"] == 0 or fb["n_traces"] == 0:
        return 0.5
    sim_calls = _jaccard(fa["call_bigrams"], fb["call_bigrams"])
    sim_cov = _jaccard(fa["coverage"], fb["coverage"])
    sim_ret = _l1_similarity(fa["ret_type_hist"], fb["ret_type_hist"])
    exc_diff = abs(fa["exception_rate"] - fb["exception_rate"])
    sim_exc = 1.0 - exc_diff
    return 0.25 * sim_calls + 0.25 * sim_cov + 0.25 * sim_ret + 0.25 * sim_exc


def run(max_pairs: Optional[int] = None) -> tuple:
    """Run B06-V2-FAIR baseline."""
    print("\n[B06_FAIR_V2] Dynamic trace baseline with V2 canonical inputs (SAFEGUARD-5)")
    print(f"[B06_FAIR_V2] Inputs: V2_CANONICAL_INPUTS ({len(V2_CANONICAL_INPUTS)} inputs, same as B07)")
    print(f"[B06_FAIR_V2] Features: B06 original (call bigrams + coverage + ret type + exc rate)")
    print(f"[B06_FAIR_V2] Fairness: input set now identical to B07; representation differs")

    dev_pairs = load_pairs("dev")
    test_pairs = load_pairs("test")
    if max_pairs:
        dev_pairs = dev_pairs[:max_pairs]
        test_pairs = test_pairs[:max_pairs]

    from baselines.common import load_source

    # DEV pass
    print(f"\n[B06_FAIR_V2] Scoring {len(dev_pairs)} DEV pairs...")
    dev_labels = pairs_to_labels(dev_pairs)
    dev_sims = []
    for i, p in enumerate(dev_pairs):
        try:
            s = score_fn(load_source(p["base_path"]), load_source(p["variant_path"]))
        except Exception:
            s = 0.5
        dev_sims.append(float(s))
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(dev_pairs)}")

    threshold = find_optimal_threshold(dev_sims, dev_labels)
    dev_metrics = compute_metrics(dev_sims, dev_labels, threshold)
    print(f"[B06_FAIR_V2] DEV threshold={threshold:.4f} F1={dev_metrics['f1']:.4f} AUROC={dev_metrics['auroc']:.4f}")

    # TEST pass
    print(f"\n[B06_FAIR_V2] Scoring {len(test_pairs)} TEST pairs...")
    test_labels = pairs_to_labels(test_pairs)
    test_sims = []
    for i, p in enumerate(test_pairs):
        try:
            s = score_fn(load_source(p["base_path"]), load_source(p["variant_path"]))
        except Exception:
            s = 0.5
        test_sims.append(float(s))
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(test_pairs)}")

    test_metrics = compute_metrics(test_sims, test_labels, threshold)
    print(f"[B06_FAIR_V2] TEST F1={test_metrics['f1']:.4f} AUROC={test_metrics['auroc']:.4f} AUPRC={test_metrics['auprc']:.4f}")

    # Inversion analysis
    equiv_sims = [s for s, l in zip(test_sims, test_labels) if l == 0]
    changed_sims = [s for s, l in zip(test_sims, test_labels) if l == 1]
    equiv_mean = sum(equiv_sims) / len(equiv_sims) if equiv_sims else 0.0
    changed_mean = sum(changed_sims) / len(changed_sims) if changed_sims else 0.0
    inversion_delta = changed_mean - equiv_mean

    print(f"\n[B06_FAIR_V2] Inversion delta: {inversion_delta:+.4f}  (v1 B06 was unknown, B07-v2 is -0.0453)")

    pathlib.Path(ARTIFACT_DIR).mkdir(parents=True, exist_ok=True)

    dev_result = {
        "baseline": "B06_FAIR_V2",
        "fairness_note": "Same V2_CANONICAL_INPUTS as B07; B06 feature formula unchanged",
        "split": "dev",
        "n_canonical_inputs": len(V2_CANONICAL_INPUTS),
        "canonical_inputs_source": "baselines.v2.b07_dynamic_v2.V2_CANONICAL_INPUTS",
        "threshold": threshold,
        "metrics": dev_metrics,
    }
    test_result = {
        "baseline": "B06_FAIR_V2",
        "fairness_note": "SAFEGUARD-5 compliant: B06 re-run with V2 inputs",
        "split": "test",
        "threshold_from": "dev",
        "n_canonical_inputs": len(V2_CANONICAL_INPUTS),
        "threshold": threshold,
        "metrics": test_metrics,
        "inversion_analysis": {
            "equiv_mean_similarity": round(equiv_mean, 6),
            "changed_mean_similarity": round(changed_mean, 6),
            "inversion_delta": round(inversion_delta, 6),
            "v1_b06_delta": "not_recorded",
            "b07_dynamic_v2_delta": -0.045265,
        },
        "comparison_note": "B06-V2-FAIR vs B07: same inputs, different representations. Delta AUROC measures representation value.",
    }

    save_results("B06_FAIR_V2", "dev", dev_result, ARTIFACT_DIR)
    save_results("B06_FAIR_V2", "test", test_result, ARTIFACT_DIR)
    print(f"\n[B06_FAIR_V2] Results saved to {ARTIFACT_DIR}")
    return dev_metrics, test_metrics, threshold


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pairs", type=int, default=None)
    args = parser.parse_args()
    run(max_pairs=args.max_pairs)
