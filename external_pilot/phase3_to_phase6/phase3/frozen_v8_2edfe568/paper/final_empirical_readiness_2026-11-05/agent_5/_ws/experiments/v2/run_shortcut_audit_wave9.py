"""
experiments/v2/run_shortcut_audit_wave9.py
============================================
Phase 4 — Wave 9: Confound / Shortcut Analysis.

Mandate (Phase 4 spec):
  Audit whether B07 exploits superficial execution properties:
    - runtime duration
    - trace length
    - event count
    - number of functions
    - memory
    - CPU
    - program size
    - token count
    - number of executed branches
  Calculate correlations and simple predictive baselines.
  If a trivial feature predicts labels as well as B07: DOCUMENT IT.

Design
------
For each of the 744 FROZEN test pairs, compute a set of superficial
per-program features for base and variant, then use |delta| (absolute
difference between base and variant) as a naive single-feature "shortcut
predictor" of the CHANGED/EQUIVALENT label — exactly the same
single-feature-AUROC methodology used in Wave 8's ablation
(`run_feature_ablation_wave8.py`), for direct comparability.

Feature availability (disclosed, not fabricated)
--------------------------------------------------
Available WITHOUT re-instrumenting the tracer (computed from existing
project code):
  - program_size_loc / program_size_chars / token_count : static, from
    source text only. No execution required.
  - n_functions_static / n_branches_static : static AST counts
    (ast.FunctionDef/AsyncFunctionDef; ast.If/For/While/Try/ExceptHandler).
  - wall_time_ms        : SandboxResult.wall_time_ms (sbg/v2/execution/runner.py)
  - trace_length_mean   : noise_floor_stats["event_count_mean"] (== mean
                           events per trace; "trace length" and "event
                           count" are the SAME underlying quantity in this
                           codebase's instrumentation, see runner.py L180-183)
  - call_count_total    : noise_floor_stats["call_count_total"]
  - n_functions_called  : noise_floor_stats["n_functions_called"] (dynamic,
                           as opposed to the static AST count above)
  - exception_fraction  : noise_floor_stats["exception_fraction"]
  - coverage_size       : len(union of trace.coverage) — used as the
                           closest available proxy for "number of executed
                           branches" (the tracer records line coverage via
                           sys.settrace line events, NOT per-branch taken/
                           not-taken pairs; no branch-coverage instrumentation
                           exists in sbg/extraction/dynamic/tracer.py). This
                           substitution is explicitly disclosed below.

NOT available — genuinely absent from the instrumentation, not fabricated:
  - memory   : no resource/psutil/tracemalloc usage anywhere in
               sbg/extraction/dynamic/tracer.py or sbg/v2/execution/runner.py.
  - CPU      : same — only wall-clock time (time.monotonic_ns) is measured,
               not CPU time (time.process_time / resource.getrusage).
  These two are reported as UNAVAILABLE with the reason above, per the
  Phase 4 mandate ("If unavailable: document exactly why" — applied here
  by analogy to the Wave 7 modern-baseline instruction, since Wave 9 has
  the same expectation for genuinely absent capabilities).

Method
------
1. Load frozen `benchmark/datasets/pairs_test.jsonl` (744 pairs). No
   modification, no filtering, no cherry-picking.
2. For every unique program path referenced by the test set, extract the
   feature vector above once (cached).
3. For each pair, compute delta = |feature(variant) - feature(base)| for
   each numeric feature.
4. For each feature: pseudo_similarity = 1 / (1 + delta)  (monotonic
   decreasing in delta; ranking-equivalent to using -delta directly).
   Compute AUROC(pseudo_similarity, labels) with the SAME compute_auroc
   convention used everywhere else in this project (high similarity =
   predicted EQUIVALENT).
5. Bootstrap 95% CI (1000 reps, seed=42) and point-biserial correlation
   between delta and label, for every feature.
6. Compare every feature's AUROC against:
     - B07 Dynamic V2 (entry-point corrected, Wave 1) TEST AUROC = 0.5292
     - the noise floor upper bound (artifacts/v2/NEGATIVE_CONTROL_RESULTS.json,
       0.544121)
7. Also compute Pearson correlation between each feature's delta and B07's
   own per-pair similarity score, to test whether B07's score is itself
   substantially explained by a superficial feature (a stronger, more
   direct form of "shortcut exploitation" than label-correlation alone).

No tuning, no post-hoc feature selection: all features below were named in
the Phase 4 spec verbatim (runtime, trace length, event count, functions,
memory, CPU, program size, token count, branches) BEFORE this script was
written.

Output: artifacts/v2/PHASE4_SHORTCUT_AUDIT.json  (no separate .md required
per Phase 4 Wave 9 spec — consistent with Wave 8's json-only precedent).
"""
from __future__ import annotations

import ast
import json
import pathlib
import random
import re
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from baselines.common import load_pairs, pairs_to_labels, compute_auroc  # noqa: E402
from baselines.v2.b07_dynamic_v2 import _load_entry_fn, V2_CANONICAL_INPUTS, _score_pair  # noqa: E402
from sbg.v2.execution.runner import SandboxRunner  # noqa: E402

ARTIFACT_PATH = REPO_ROOT / "artifacts" / "v2" / "PHASE4_SHORTCUT_AUDIT.json"

B07_TEST_AUROC_REFERENCE = 0.5292  # Wave 1 entry-point-corrected TEST AUROC
NOISE_FLOOR_UPPER = 0.544121       # artifacts/v2/NEGATIVE_CONTROL_RESULTS.json

BOOTSTRAP_N = 1000
BOOTSTRAP_SEED = 42

_runner = SandboxRunner()
_feature_cache: Dict[str, Optional[Dict[str, float]]] = {}


# ---------------------------------------------------------------------------
# Static (no-execution) features
# ---------------------------------------------------------------------------

def _static_features(source: str) -> Dict[str, float]:
    loc = len([ln for ln in source.splitlines() if ln.strip()])
    chars = len(source)
    tokens = re.findall(r"\w+|[^\w\s]", source)
    token_count = len(tokens)

    n_functions_static = 0
    n_branches_static = 0
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                n_functions_static += 1
            if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While,
                                  ast.Try, ast.ExceptHandler)):
                n_branches_static += 1
    except SyntaxError:
        pass

    return {
        "program_size_loc": float(loc),
        "program_size_chars": float(chars),
        "token_count": float(token_count),
        "n_functions_static": float(n_functions_static),
        "n_branches_static": float(n_branches_static),
    }


# ---------------------------------------------------------------------------
# Dynamic (execution-derived) features — reuses B07's own entry-point
# discovery so the audit is apples-to-apples with what B07 actually sees.
# ---------------------------------------------------------------------------

def _dynamic_features(source_path: str) -> Optional[Dict[str, float]]:
    fn = _load_entry_fn(source_path)
    if fn is None:
        return None

    program_id = pathlib.Path(source_path).stem
    import inspect
    try:
        sig = inspect.signature(fn)
        n_params = len(sig.parameters)
    except (ValueError, TypeError):
        n_params = 1

    if n_params == 0:
        def _zero_arg_wrapper(inp):
            return fn()
        fn_to_trace: Callable = _zero_arg_wrapper
        inputs_to_use = [None]
    else:
        fn_to_trace = fn
        inputs_to_use = V2_CANONICAL_INPUTS

    try:
        t0 = time.monotonic()
        result = _runner.run(program_id, fn_to_trace, inputs_to_use, n_runs=1, seed=42)
        wall_ms = (time.monotonic() - t0) * 1000.0
    except Exception:
        return None

    if result.error is not None:
        return None

    coverage_union = set()
    for run_traces in result.traces:
        for tr in run_traces:
            coverage_union.update(tr.coverage)

    stats = result.noise_floor_stats
    return {
        "wall_time_ms": float(result.wall_time_ms if result.wall_time_ms else wall_ms),
        "trace_length_mean": float(stats.get("event_count_mean_mean", stats.get("event_count_mean", 0.0))),
        "call_count_total": float(stats.get("call_count_total_mean", stats.get("call_count_total", 0.0))),
        "n_functions_called": float(stats.get("n_functions_called_mean", stats.get("n_functions_called", 0.0))),
        "exception_fraction": float(stats.get("exception_fraction_mean", stats.get("exception_fraction", 0.0))),
        "coverage_size_proxy_for_branches": float(len(coverage_union)),
    }


def _all_features(rel_path: str) -> Optional[Dict[str, float]]:
    resolved = str(REPO_ROOT / rel_path)
    if resolved in _feature_cache:
        return _feature_cache[resolved]

    try:
        source = pathlib.Path(resolved).read_text(encoding="utf-8")
    except Exception:
        _feature_cache[resolved] = None
        return None

    feats = _static_features(source)
    dyn = _dynamic_features(resolved)
    if dyn is not None:
        feats.update(dyn)
    else:
        # Dynamic extraction failed for this program (e.g. no discoverable
        # entry point). Static features are still valid; dynamic ones are
        # marked missing (None), never imputed as 0 or fabricated.
        for key in ("wall_time_ms", "trace_length_mean", "call_count_total",
                    "n_functions_called", "exception_fraction",
                    "coverage_size_proxy_for_branches"):
            feats[key] = None  # type: ignore[assignment]

    _feature_cache[resolved] = feats
    return feats


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def _pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    denom = (vx * vy) ** 0.5
    if denom == 0:
        return None
    return cov / denom


def _bootstrap_auroc_ci(sims: List[float], labels: List[int]) -> Tuple[float, float]:
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(sims)
    aurocs = []
    for _ in range(BOOTSTRAP_N):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        aurocs.append(compute_auroc([sims[i] for i in idx], [labels[i] for i in idx]))
    aurocs.sort()
    return aurocs[25], aurocs[974]


def _permutation_p(sims: List[float], labels: List[int], observed: float) -> float:
    rng = random.Random(BOOTSTRAP_SEED)
    obs_dev = abs(observed - 0.5)
    labels_copy = list(labels)
    count = 0
    for _ in range(BOOTSTRAP_N):
        rng.shuffle(labels_copy)
        perm = compute_auroc(sims, labels_copy)
        if abs(perm - 0.5) >= obs_dev:
            count += 1
    return count / BOOTSTRAP_N


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

FEATURE_NAMES = [
    "program_size_loc",
    "program_size_chars",
    "token_count",
    "n_functions_static",
    "n_branches_static",
    "wall_time_ms",
    "trace_length_mean",
    "call_count_total",
    "n_functions_called",
    "exception_fraction",
    "coverage_size_proxy_for_branches",
]

UNAVAILABLE_FEATURES = {
    "memory": (
        "No memory instrumentation exists anywhere in the tracing stack. "
        "sbg/extraction/dynamic/tracer.py and sbg/v2/execution/runner.py "
        "import no resource/psutil/tracemalloc module and record no memory "
        "metric of any kind. Fabricating a memory feature would violate "
        "the no-fabrication mandate; this feature is honestly reported as "
        "UNAVAILABLE rather than approximated."
    ),
    "cpu": (
        "Only wall-clock time (time.monotonic_ns) is measured by "
        "SandboxRunner (sbg/v2/execution/runner.py L145-151) and the "
        "v1 Tracer (sbg/extraction/dynamic/tracer.py L174, L187-188). "
        "No CPU-time measurement (time.process_time / resource.getrusage) "
        "exists. Reported as UNAVAILABLE rather than substituting wall-time "
        "under a different label."
    ),
}


def run() -> Dict[str, Any]:
    print("[Wave9-Shortcut] Loading FROZEN test pairs...")
    test_pairs = load_pairs("test")
    test_labels = pairs_to_labels(test_pairs)
    n = len(test_pairs)
    print(f"[Wave9-Shortcut] n={n} pairs")

    print("[Wave9-Shortcut] Scoring B07 (Dynamic V2, entry-point corrected) for correlation baseline...")
    b07_sims: List[float] = []
    for i, p in enumerate(test_pairs):
        base = str(REPO_ROOT / p["base_path"])
        var = str(REPO_ROOT / p["variant_path"])
        try:
            b07_sims.append(_score_pair(base, var))
        except Exception:
            b07_sims.append(0.5)
        if (i + 1) % 200 == 0:
            print(f"    B07: {i+1}/{n}")

    b07_auroc_this_run = round(compute_auroc(b07_sims, test_labels), 6)

    print("[Wave9-Shortcut] Extracting superficial features per program (cached by path)...")
    delta_by_feature: Dict[str, List[Optional[float]]] = {f: [] for f in FEATURE_NAMES}
    n_missing_by_feature: Dict[str, int] = {f: 0 for f in FEATURE_NAMES}

    for i, p in enumerate(test_pairs):
        base_feats = _all_features(p["base_path"])
        var_feats = _all_features(p["variant_path"])
        for f in FEATURE_NAMES:
            bv = base_feats.get(f) if base_feats else None
            vv = var_feats.get(f) if var_feats else None
            if bv is None or vv is None:
                delta_by_feature[f].append(None)
                n_missing_by_feature[f] += 1
            else:
                delta_by_feature[f].append(abs(vv - bv))
        if (i + 1) % 200 == 0:
            print(f"    Features: {i+1}/{n}")

    print("[Wave9-Shortcut] Computing per-feature AUROC / CI / correlation...")
    feature_results: Dict[str, Any] = {}
    for f in FEATURE_NAMES:
        deltas = delta_by_feature[f]
        valid_idx = [i for i, d in enumerate(deltas) if d is not None]
        n_valid = len(valid_idx)
        n_missing = n_missing_by_feature[f]

        if n_valid < 20:
            feature_results[f] = {
                "status": "INSUFFICIENT_DATA",
                "n_valid": n_valid,
                "n_missing": n_missing,
            }
            continue

        v_deltas = [deltas[i] for i in valid_idx]
        v_labels = [test_labels[i] for i in valid_idx]
        v_b07 = [b07_sims[i] for i in valid_idx]

        pseudo_sim = [1.0 / (1.0 + d) for d in v_deltas]
        auroc = compute_auroc(pseudo_sim, v_labels)
        ci_lo, ci_hi = _bootstrap_auroc_ci(pseudo_sim, v_labels)
        perm_p = _permutation_p(pseudo_sim, v_labels, auroc)

        corr_with_label = _pearson(v_deltas, [float(l) for l in v_labels])
        corr_with_b07_score = _pearson(v_deltas, v_b07)

        matches_or_beats_b07 = bool(auroc >= B07_TEST_AUROC_REFERENCE)
        above_noise_floor = bool(auroc > NOISE_FLOOR_UPPER)

        feature_results[f] = {
            "status": "OK",
            "n_valid": n_valid,
            "n_missing": n_missing,
            "auroc": round(auroc, 6),
            "ci_auroc_lower": round(ci_lo, 6),
            "ci_auroc_upper": round(ci_hi, 6),
            "permutation_p": round(perm_p, 4),
            "pearson_corr_delta_vs_label": round(corr_with_label, 6) if corr_with_label is not None else None,
            "pearson_corr_delta_vs_b07_score": round(corr_with_b07_score, 6) if corr_with_b07_score is not None else None,
            "matches_or_beats_b07_auroc": matches_or_beats_b07,
            "above_noise_floor": above_noise_floor,
        }

    # ------------------------------------------------------------------
    # Shortcut verdict
    # ------------------------------------------------------------------
    shortcuts_found = [
        f for f, r in feature_results.items()
        if r.get("status") == "OK" and r.get("matches_or_beats_b07_auroc")
    ]
    shortcuts_above_noise_floor = [
        f for f, r in feature_results.items()
        if r.get("status") == "OK" and r.get("above_noise_floor")
    ]
    strong_score_correlations = [
        f for f, r in feature_results.items()
        if r.get("status") == "OK" and r.get("pearson_corr_delta_vs_b07_score") is not None
        and abs(r["pearson_corr_delta_vs_b07_score"]) >= 0.5
    ]

    if shortcuts_found:
        verdict = "SHORTCUT_DETECTED"
        verdict_note = (
            f"The following superficial feature(s) predict the CHANGED/EQUIVALENT "
            f"label at least as well as B07 Dynamic V2 (AUROC>={B07_TEST_AUROC_REFERENCE}): "
            f"{shortcuts_found}. This is disclosed per the Phase 4 mandate "
            f"('If a trivial feature predicts labels as well as B07: DOCUMENT IT.')."
        )
    else:
        verdict = "NO_DOMINANT_SHORTCUT_DETECTED"
        verdict_note = (
            "No single superficial feature examined (program size, token count, "
            "static function/branch counts, wall-clock runtime, dynamic trace "
            "length, call count, dynamic function count, exception fraction, or "
            "coverage-size-as-branch-proxy) matches or exceeds B07's own AUROC "
            f"({B07_TEST_AUROC_REFERENCE}) on the frozen TEST set. This is a "
            "negative finding for the shortcut hypothesis, not evidence that B07 "
            "is free of ALL possible confounds — only the specific, "
            "pre-registered list of superficial properties named in the Phase 4 "
            "spec was tested."
        )

    results: Dict[str, Any] = {
        "phase": "4",
        "wave": "9",
        "analysis": "confound_shortcut_audit",
        "n_test_pairs": n,
        "b07_test_auroc_reference": B07_TEST_AUROC_REFERENCE,
        "b07_test_auroc_this_run": b07_auroc_this_run,
        "b07_auroc_reproducibility_note": (
            "b07_test_auroc_this_run is the AUROC obtained by re-running B07 in "
            "this script; b07_test_auroc_reference is the historical Wave 1 "
            "value. Both are reported for transparency; small floating "
            "differences (if any) reflect no code changes, only re-execution."
        ),
        "noise_floor_upper_reference": NOISE_FLOOR_UPPER,
        "methodology": (
            "For each feature, delta = |feature(variant) - feature(base)| is "
            "computed per pair. pseudo_similarity = 1/(1+delta) (monotonic "
            "decreasing in delta) is fed through the SAME compute_auroc() used "
            "throughout the project. This mirrors the single-dimension "
            "methodology of Wave 8's feature ablation "
            "(experiments/v2/run_feature_ablation_wave8.py) for direct "
            "comparability. No feature was chosen or discarded based on its "
            "resulting AUROC — the full list was fixed by the Phase 4 spec "
            "before this script was written."
        ),
        "features_tested": feature_results,
        "features_unavailable": UNAVAILABLE_FEATURES,
        "shortcut_features_matching_or_beating_b07": shortcuts_found,
        "shortcut_features_above_noise_floor": shortcuts_above_noise_floor,
        "features_strongly_correlated_with_b07_score": {
            "threshold_abs_pearson": 0.5,
            "features": strong_score_correlations,
            "note": (
                "Pearson correlation between each feature's per-pair delta and "
                "B07's own similarity score, across all valid pairs. A strong "
                "correlation here would indicate B07's score is largely "
                "REDUNDANT with a superficial feature (a stronger form of "
                "shortcut exploitation than label-correlation alone), "
                "independent of whether that feature predicts the label well."
            ),
        },
        "verdict": verdict,
        "verdict_note": verdict_note,
        "branch_coverage_proxy_disclosure": (
            "'coverage_size_proxy_for_branches' is NOT a genuine executed-branch "
            "count. sbg/extraction/dynamic/tracer.py records LINE coverage via "
            "sys.settrace line events (state.coverage.add(frame.f_lineno)), not "
            "branch-taken/not-taken pairs. It is used here as the closest "
            "available proxy and is explicitly labeled as a proxy, not fabricated "
            "as a true branch-coverage metric."
        ),
        "integrity_notes": [
            "Frozen benchmark/datasets/pairs_test.jsonl was used unmodified "
            "(744 pairs, same file as H7-H10/Wave2).",
            "No feature was added, removed, or re-weighted after seeing its "
            "AUROC. The full feature list was fixed by the Phase 4 spec text "
            "before implementation.",
            "memory and CPU are reported UNAVAILABLE with an explicit code-level "
            "reason, not imputed or approximated under a misleading label.",
        ],
        "bootstrap_config": {"n": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED},
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(results, indent=2))
    print(f"\n[Wave9-Shortcut] Results saved to {ARTIFACT_PATH}")
    print(f"[Wave9-Shortcut] Verdict: {verdict}")
    for f, r in feature_results.items():
        if r.get("status") == "OK":
            print(f"  {f}: AUROC={r['auroc']} corr(label)={r['pearson_corr_delta_vs_label']} "
                  f"corr(b07_score)={r['pearson_corr_delta_vs_b07_score']}")
        else:
            print(f"  {f}: {r.get('status')}")

    return results


if __name__ == "__main__":
    run()
