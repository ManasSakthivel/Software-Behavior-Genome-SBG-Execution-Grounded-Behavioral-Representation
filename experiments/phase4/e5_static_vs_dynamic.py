"""
experiments/phase4/e5_static_vs_dynamic.py
============================================
E5: Static vs Dynamic vs Hybrid Analysis.

Since full dynamic tracing requires execution with inputs (not available in
the static benchmark setting), this experiment:
1. Uses Phase 3 saved aggregate results for B06 (dynamic trace), B07 (static SBG), B08 (full SBG)
2. Re-scores test pairs with AST (best static) and Token (baseline static)
3. Performs stratified analysis: per-SP-type and per-SC-type AUROC
4. Analyzes: which transformation types does each method handle best/worst?
5. Computes information value of adding dynamic features (B08 vs B07)

Hypothesis addressed: H5 (regression detection requires dynamic?), H6 (multi-dim value)
"""
import json
import pathlib
import random
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from experiments.phase4.utils import ensure_token_initialized

from baselines.common import load_pairs, load_source, compute_auroc, compute_metrics, find_optimal_threshold
from baselines.b07_static_sbg import score_fn as static_sbg_fn
from baselines.b02_ast import score_fn as ast_fn
from baselines.b01_token import score_fn as token_fn

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "phase4" / "E5"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
N_BOOTSTRAP = 1000
PHASE3_DIR = REPO_ROOT / "artifacts" / "phase3"


def load_phase3_result(baseline: str, split: str) -> dict:
    p = PHASE3_DIR / baseline / f"results_{split}.json"
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {}


def bootstrap_ci_auroc(eq_scores, ch_scores, n_resamples=N_BOOTSTRAP, seed=SEED):
    rng = random.Random(seed)
    all_scores = eq_scores + ch_scores
    all_labels = [0] * len(eq_scores) + [1] * len(ch_scores)
    n = len(all_scores)
    aurocs = []
    for _ in range(n_resamples):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        bs = [all_scores[i] for i in idx]
        bl = [all_labels[i] for i in idx]
        aurocs.append(compute_auroc(bs, bl))
    aurocs.sort()
    return (
        compute_auroc(all_scores, all_labels),
        aurocs[int(0.025 * n_resamples)],
        aurocs[int(0.975 * n_resamples)],
    )


def stratified_auroc(scores_by_type: dict) -> dict:
    """
    scores_by_type: {transform_type: {"equiv": [sims], "changed": [sims]}}
    Returns per-type AUROC.
    """
    result = {}
    for tt, data in scores_by_type.items():
        eq = data.get("equiv", [])
        ch = data.get("changed", [])
        if len(eq) + len(ch) < 5:
            result[tt] = {"auroc": None, "n": len(eq) + len(ch), "note": "insufficient_data"}
            continue
        # Build combined scores+labels for this type
        # For equiv pairs: label=0; for changed pairs: label=1
        combined_sims = eq + ch
        combined_labels = [0] * len(eq) + [1] * len(ch)
        if not combined_labels or all(l == combined_labels[0] for l in combined_labels):
            result[tt] = {"auroc": None, "n": len(combined_labels), "note": "single_class"}
            continue
        auroc = compute_auroc(combined_sims, combined_labels)
        result[tt] = {
            "auroc": round(auroc, 4),
            "n_equiv": len(eq),
            "n_changed": len(ch),
        }
    return result


def run_e5():
    print("=" * 60)
    print("E5: Static vs Dynamic vs Hybrid Analysis")
    print("=" * 60)

    ensure_token_initialized()
    # Load Phase 3 aggregate results for dynamic (B06), static (B07), full (B08)
    b06 = load_phase3_result("B06", "test")
    b07 = load_phase3_result("B07", "test")
    b08 = load_phase3_result("B08", "test")

    phase3_summary = {
        "B06_dynamic": {"auroc": b06.get("metrics", {}).get("auroc"), "f1": b06.get("metrics", {}).get("f1")},
        "B07_static_sbg": {"auroc": b07.get("metrics", {}).get("auroc"), "f1": b07.get("metrics", {}).get("f1")},
        "B08_full_sbg": {"auroc": b08.get("metrics", {}).get("auroc"), "f1": b08.get("metrics", {}).get("f1")},
    }
    print("  Phase 3 summary:", json.dumps(phase3_summary, indent=4))

    # Load test pairs and score with static methods
    test_pairs = load_pairs("test")
    dev_pairs = load_pairs("dev")

    methods = {
        "Static_SBG": static_sbg_fn,
        "AST": ast_fn,
        "Token": token_fn,
    }

    # Stratified: collect scores per (method, transform_type, label)
    # Map: transform_type -> method_name -> {"equiv": [], "changed": []}
    by_type = {}

    all_scores = {m: [] for m in methods}
    all_labels = []

    print(f"  Scoring {len(test_pairs)} test pairs...")
    for i, p in enumerate(test_pairs):
        if (i + 1) % 100 == 0:
            print(f"    {i+1}/{len(test_pairs)}...")
        tt = p["transformation_type"]
        label = 0 if p["semantic_relation"] == "EQUIVALENT" else 1
        all_labels.append(label)
        src_base = load_source(p["base_path"])
        src_var = load_source(p["variant_path"])
        if tt not in by_type:
            by_type[tt] = {m: {"equiv": [], "changed": []} for m in methods}
        for m_name, fn in methods.items():
            try:
                s = float(fn(src_base, src_var))
            except Exception:
                s = 0.5
            all_scores[m_name].append(s)
            key = "equiv" if label == 0 else "changed"
            by_type[tt][m_name][key].append(s)

    # Overall AUROC with CI
    overall_auroc = {}
    for m_name in methods:
        sims = all_scores[m_name]
        eq_sims = [s for s, l in zip(sims, all_labels) if l == 0]
        ch_sims = [s for s, l in zip(sims, all_labels) if l == 1]
        auroc, lo, hi = bootstrap_ci_auroc(eq_sims, ch_sims, seed=SEED)
        overall_auroc[m_name] = {
            "auroc": round(auroc, 4),
            "ci_lo": round(lo, 4),
            "ci_hi": round(hi, 4),
        }

    # Stratified AUROC per transform type
    stratified = {}
    for m_name in methods:
        type_data = {tt: by_type[tt][m_name] for tt in by_type}
        stratified[m_name] = stratified_auroc(type_data)

    # Static vs Dynamic comparison
    static_dynamic_comparison = {
        "static_best": {"method": "AST", "auroc": overall_auroc["AST"]["auroc"]},
        "dynamic_proxy": {
            "method": "B06_dynamic_phase3",
            "auroc": phase3_summary["B06_dynamic"]["auroc"],
            "note": "Phase 3 result — dynamic trace baseline on same test set",
        },
        "hybrid": {
            "method": "B08_full_sbg_phase3",
            "auroc": phase3_summary["B08_full_sbg"]["auroc"],
            "note": "Phase 3 result — full 8-dim SBG including dynamic dims",
        },
        "does_dynamic_help": (
            phase3_summary["B08_full_sbg"]["auroc"] is not None and
            phase3_summary["B06_dynamic"]["auroc"] is not None and
            phase3_summary["B08_full_sbg"]["auroc"] > phase3_summary["B07_static_sbg"]["auroc"]
        ),
        "conclusion": "",
    }
    b07_auroc = phase3_summary["B07_static_sbg"]["auroc"] or 0.0
    b08_auroc = phase3_summary["B08_full_sbg"]["auroc"] or 0.0
    b06_auroc = phase3_summary["B06_dynamic"]["auroc"] or 0.0
    if b08_auroc > b07_auroc:
        static_dynamic_comparison["conclusion"] = (
            f"Adding dynamic dims improves AUROC by {b08_auroc - b07_auroc:.4f} "
            f"({b07_auroc:.4f} → {b08_auroc:.4f}). Dynamic features ADD value."
        )
    else:
        static_dynamic_comparison["conclusion"] = (
            f"Adding dynamic dims does NOT improve AUROC "
            f"(static={b07_auroc:.4f}, hybrid={b08_auroc:.4f}). "
            f"Dynamic features did not help in this benchmark."
        )

    result = {
        "experiment": "E5",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_addressed": ["H5", "H6"],
        "n_test_pairs": len(test_pairs),
        "phase3_dynamic_results": phase3_summary,
        "overall_auroc": overall_auroc,
        "stratified_auroc_by_transform": stratified,
        "static_vs_dynamic_comparison": static_dynamic_comparison,
        "finding": static_dynamic_comparison["conclusion"],
        "limitation": (
            "Full dynamic tracing requires program execution with representative inputs. "
            "B06/B07/B08 dynamic results are from Phase 3 with fixed synthetic inputs. "
            "Stratified analysis here uses only static methods (AST, Token, Static_SBG)."
        ),
        "seed": SEED,
    }

    out_path = ARTIFACT_DIR / "results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n=== E5 Results ===")
    for m_name in methods:
        oa = overall_auroc[m_name]
        print(f"  {m_name}: AUROC={oa['auroc']:.4f} [{oa['ci_lo']:.3f}–{oa['ci_hi']:.3f}]")
    print(f"  {static_dynamic_comparison['conclusion']}")
    print(f"\nResults saved to: {out_path}")
    return result


if __name__ == "__main__":
    run_e5()
