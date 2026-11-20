"""
baselines/b06_dynamic.py
==========================
B6: Dynamic Trace Baseline — flat trace feature comparison.

Uses the SAME execution traces as SBG but without genome structure.
Critical test: does SBG's structured genome provide value over flat trace features?

Features extracted per program:
1. Function call bigrams (ordered pairs) — Jaccard similarity
2. Line coverage set — Jaccard similarity
3. Return value type histogram — L1 similarity
4. Exception rate — absolute difference → similarity

Primary: equal-weight combination of all 4.

Scoring: HIGH → EQUIVALENT, LOW → CHANGED
"""
import collections
import importlib.util
import pathlib
import sys
import threading
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from baselines.common import (
    load_pairs, load_source, run_baseline, REPO_ROOT, ARTIFACTS_DIR
)

ARTIFACT_DIR = str(ARTIFACTS_DIR / "B06")
TIMEOUT = 2.0
_FIXED_INT_INPUTS = [-5, 0, 1, 5, 10, 100]
_FIXED_LIST_INPUTS = [[], [1], [1, 2, 3], [5, 4, 3, 2, 1]]
_FIXED_STR_INPUTS = ["", "a", "hello", "hello world"]


def _load_fn(source: str):
    """Load main/solve/run from source string. Returns callable or None."""
    _counter = getattr(_load_fn, '_counter', 0) + 1
    _load_fn._counter = _counter
    mod = types.ModuleType(f"_dyn_mod_{_counter}")
    try:
        exec(compile(source, f"<module_{_counter}>", "exec"), mod.__dict__)
    except Exception:
        return None
    for name in ("main", "solve", "run", "compute"):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    # Find single top-level function
    fns = [v for k, v in mod.__dict__.items()
           if callable(v) and not k.startswith('_') and
           getattr(v, '__module__', None) is None or True]
    # Filter to only functions defined in this module
    fns = [v for k, v in mod.__dict__.items()
           if callable(v) and not k.startswith('_')
           and isinstance(v, types.FunctionType)]
    if len(fns) == 1:
        return fns[0]
    return None


def _run_with_timeout(fn, inp, timeout=TIMEOUT):
    """Run fn(inp) with timeout. Returns (result_type, call_list, lines_covered)."""
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
                ret = fn(*inp)
            elif isinstance(inp, dict):
                ret = fn(**inp)
            else:
                ret = fn(inp)
            result["ret_type"] = type(ret).__name__
            result["calls"] = calls[:200]
            result["lines"] = lines
        except Exception as e:
            result["exception"] = True
            result["calls"] = calls[:200]
            result["lines"] = lines
        finally:
            sys.settrace(old_trace)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout=timeout)
    return result


def _extract_trace_features(source: str) -> dict:
    """Extract flat trace features from a program over fixed inputs."""
    fn = _load_fn(source)
    if fn is None:
        return {"call_bigrams": set(), "coverage": set(),
                "ret_type_hist": {}, "exception_rate": 0.5,
                "n_traces": 0}

    all_calls = []
    all_lines = set()
    ret_types = []
    n_exc = 0
    n_total = 0

    for inputs in [_FIXED_INT_INPUTS, _FIXED_LIST_INPUTS, _FIXED_STR_INPUTS]:
        for inp in inputs:
            r = _run_with_timeout(fn, inp)
            n_total += 1
            if r["exception"]:
                n_exc += 1
            else:
                if r["ret_type"]:
                    ret_types.append(r["ret_type"])
            all_calls.extend(r["calls"])
            all_lines.update(r["lines"])

    # Call bigrams
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
    return 1.0 - min(l1 / 2.0, 1.0)  # L1 between distributions is at most 2


_cache: dict = {}


def _get_features(source: str) -> dict:
    key = hash(source[:500])
    if key not in _cache:
        _cache[key] = _extract_trace_features(source)
    return _cache[key]


def call_sequence_similarity(src_a: str, src_b: str) -> float:
    fa = _get_features(src_a)
    fb = _get_features(src_b)
    return _jaccard(fa["call_bigrams"], fb["call_bigrams"])


def full_trace_similarity(src_a: str, src_b: str) -> float:
    fa = _get_features(src_a)
    fb = _get_features(src_b)
    sim_calls = _jaccard(fa["call_bigrams"], fb["call_bigrams"])
    sim_cov = _jaccard(fa["coverage"], fb["coverage"])
    sim_ret = _l1_similarity(fa["ret_type_hist"], fb["ret_type_hist"])
    exc_diff = abs(fa["exception_rate"] - fb["exception_rate"])
    sim_exc = 1.0 - exc_diff
    return 0.25 * sim_calls + 0.25 * sim_cov + 0.25 * sim_ret + 0.25 * sim_exc


score_fn = full_trace_similarity


if __name__ == "__main__":
    dev_pairs = load_pairs("dev")
    test_pairs = load_pairs("test")

    print(f"[B06] Dynamic trace baseline")
    print(f"[B06] Pre-caching features for dev base programs...")
    seen = set()
    for p in dev_pairs[:20]:  # warm up cache check
        h = hash(p["base_id"])
        if h not in seen:
            seen.add(h)

    dev_m, test_m, threshold = run_baseline(
        "B06", score_fn, dev_pairs, test_pairs,
        artifact_dir=ARTIFACT_DIR
    )

    print(f"\n=== B6 Dynamic Trace Baseline ===")
    print(f"  DEV  F1={dev_m['f1']:.4f} AUROC={dev_m['auroc']:.4f}")
    print(f"  TEST F1={test_m['f1']:.4f} AUROC={test_m['auroc']:.4f} "
          f"[{test_m['ci_f1_lower']:.3f}–{test_m['ci_f1_upper']:.3f}]")
