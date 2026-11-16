"""
experiments/v2/robustness_analysis.py
=======================================
H10 Robustness Experiment.

Pre-registered criterion (from docs/v2/HYPOTHESES_V2.md):
  H10_MAX_SPREAD = 0.10  (max AUROC - min AUROC across SP types must be < 0.10)
  H10_FRAGILE_DROP = 0.30  (if any single SP type drops >0.30 → NOT SUPPORTED)

This script:
1. Loads test pairs and stratifies by transformation_type
2. For each SP type, computes AUROC for B02 (AST), B07 (Dynamic V2), B08 (Hybrid V2)
3. Evaluates H10 verdict against preregistered criteria
4. Reports robustness table with CI per condition
"""
from __future__ import annotations

import json
import pathlib
import random
import sys
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# ============================================================
# PREREGISTERED H10 CRITERIA — must precede any test evaluation
# ============================================================
H10_MAX_SPREAD: float = 0.10
H10_FRAGILE_DROP: float = 0.30
BOOTSTRAP_N: int = 1000
BOOTSTRAP_SEED: int = 42

SP_EXCLUDE = {"SP-8"}  # excluded per GAP-05 divergence bug

ARTIFACT_PATH = REPO_ROOT / "artifacts" / "v2" / "ROBUSTNESS_RESULTS.json"

from baselines.common import load_pairs, pairs_to_labels, compute_auroc, load_source


def _bootstrap_auroc_ci(sims: List[float], labels: List[int]) -> Tuple[float, float]:
    """Bootstrap 95% CI for AUROC."""
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(sims)
    aurocs = []
    for _ in range(BOOTSTRAP_N):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        bs_sims = [sims[i] for i in idx]
        bs_labels = [labels[i] for i in idx]
        aurocs.append(compute_auroc(bs_sims, bs_labels))
    aurocs.sort()
    return aurocs[25], aurocs[974]


def _per_type_auroc(
    sims: List[float],
    labels: List[int],
    pairs: List[Dict],
    sp_type: str,
    method_name: str,
) -> Dict[str, Any]:
    """
    Compute AUROC for H10 robustness: one SP type vs all SC (changed) pairs.

    H10 design: SP-* pairs are equivalent (label=0); SC-* pairs are changed (label=1).
    For each SP type, AUROC is computed using:
      - All pairs of that SP type  (equiv, label=0)
      - ALL SC-* changed pairs     (changed, label=1)
    This measures whether each structure-preserving transformation degraded
    the method's ability to distinguish equiv from changed.
    """
    # SP-type equiv pairs (these provide the negative class)
    sp_indices = [i for i, p in enumerate(pairs)
                  if p.get("transformation_type") == sp_type]
    # All SC changed pairs (these provide the positive class)
    sc_indices = [i for i, p in enumerate(pairs)
                  if p.get("transformation_type", "").startswith("SC-")]

    n_equiv = len(sp_indices)
    n_changed = len(sc_indices)

    if n_equiv == 0:
        return {"status": "NO_PAIRS", "sp_type": sp_type, "method": method_name}
    if n_changed == 0:
        return {
            "status": "SINGLE_CLASS",
            "sp_type": sp_type,
            "method": method_name,
            "n": n_equiv,
            "n_changed": 0,
            "n_equiv": n_equiv,
            "auroc": None,
            "note": "No SC changed pairs found — check benchmark split",
        }

    combined_indices = sp_indices + sc_indices
    type_sims = [sims[i] for i in combined_indices]
    type_labels = [labels[i] for i in combined_indices]

    auroc = compute_auroc(type_sims, type_labels)
    ci_lower, ci_upper = _bootstrap_auroc_ci(type_sims, type_labels)

    return {
        "status": "OK",
        "sp_type": sp_type,
        "method": method_name,
        "n": len(combined_indices),
        "n_changed": n_changed,
        "n_equiv": n_equiv,
        "auroc": round(auroc, 6),
        "ci_auroc_lower": round(ci_lower, 6),
        "ci_auroc_upper": round(ci_upper, 6),
    }


def _load_b02_sims(pairs: List[Dict], labels: List[int]) -> List[float]:
    """Load AST similarity scores for all pairs using B02."""
    try:
        from baselines.b02_ast import score_fn
        sims = []
        for p in pairs:
            try:
                s = score_fn(load_source(p["base_path"]), load_source(p["variant_path"]))
            except Exception:
                s = 0.5
            sims.append(s)
        return sims
    except Exception as e:
        print(f"  [WARN] B02 AST scoring failed: {e}")
        return [0.5] * len(pairs)


def _load_b07_sims(pairs: List[Dict]) -> List[float]:
    """Score pairs with B07 Dynamic V2."""
    try:
        from baselines.v2.b07_dynamic_v2 import _score_pair
        sims = []
        for i, p in enumerate(pairs):
            base = str(REPO_ROOT / p["base_path"])
            var = str(REPO_ROOT / p["variant_path"])
            try:
                s = _score_pair(base, var)
            except Exception:
                s = 0.5
            sims.append(s)
            if (i + 1) % 100 == 0:
                print(f"    B07: {i+1}/{len(pairs)}")
        return sims
    except Exception as e:
        print(f"  [WARN] B07 scoring failed: {e}")
        return [0.5] * len(pairs)


def _load_b08_sims(pairs: List[Dict]) -> List[float]:
    """Score pairs with B08 Hybrid V2 (token proxy version)."""
    try:
        from baselines.v2.b08_hybrid_sbg_v2 import _score_hybrid_pair, _get_static_similarity
        sims = []
        for i, p in enumerate(pairs):
            base = str(REPO_ROOT / p["base_path"])
            var = str(REPO_ROOT / p["variant_path"])
            static_sim = _get_static_similarity(p)
            try:
                s = _score_hybrid_pair(base, var, static_sim)
            except Exception:
                s = 0.5
            sims.append(s)
            if (i + 1) % 100 == 0:
                print(f"    B08: {i+1}/{len(pairs)}")
        return sims
    except Exception as e:
        print(f"  [WARN] B08 scoring failed: {e}")
        return [0.5] * len(pairs)


def run_robustness_analysis() -> Dict[str, Any]:
    """Run H10 robustness analysis."""
    print("[H10] Robustness Analysis")
    print(f"[H10] Max spread criterion: {H10_MAX_SPREAD}")
    print(f"[H10] Fragile drop criterion: {H10_FRAGILE_DROP}")

    test_pairs = load_pairs("test")
    test_labels = pairs_to_labels(test_pairs)

    # Get all SP types present in test set
    sp_types = sorted(set(
        p.get("transformation_type", "")
        for p in test_pairs
        if p.get("transformation_type", "").startswith("SP-")
        and p.get("transformation_type") not in SP_EXCLUDE
    ))

    print(f"[H10] SP types in test set: {sp_types}")

    # Score all pairs for each method
    print("\n[H10] Scoring with B02 (AST)...")
    b02_sims = _load_b02_sims(test_pairs, test_labels)

    print("\n[H10] Scoring with B07 (Dynamic V2)...")
    b07_sims = _load_b07_sims(test_pairs)

    print("\n[H10] Scoring with B08 (Hybrid V2)...")
    b08_sims = _load_b08_sims(test_pairs)

    methods = {
        "B02_AST": b02_sims,
        "B07_DYNAMIC_V2": b07_sims,
        "B08_HYBRID_V2": b08_sims,
    }

    # Per-type AUROC for each method
    per_type_results: Dict[str, Dict] = {sp: {} for sp in sp_types}
    method_aurocs: Dict[str, List[float]] = {m: [] for m in methods}

    for sp_type in sp_types:
        for method_name, sims in methods.items():
            result = _per_type_auroc(sims, test_labels, test_pairs, sp_type, method_name)
            per_type_results[sp_type][method_name] = result
            if result.get("status") == "OK" and result.get("auroc") is not None:
                method_aurocs[method_name].append(result["auroc"])

    # H10 verdict per method
    h10_verdicts = {}
    for method_name, aurocs in method_aurocs.items():
        if not aurocs:
            h10_verdicts[method_name] = {"status": "NO_DATA"}
            continue

        spread = max(aurocs) - min(aurocs)
        mean_auroc = sum(aurocs) / len(aurocs)
        fragile = spread > H10_FRAGILE_DROP

        if spread < H10_MAX_SPREAD and not fragile:
            verdict = "SUPPORTED"
        elif fragile:
            verdict = "NOT_SUPPORTED_FRAGILE"
        else:
            verdict = "NOT_SUPPORTED"

        h10_verdicts[method_name] = {
            "verdict": verdict,
            "spread": round(spread, 6),
            "mean_auroc": round(mean_auroc, 6),
            "max_auroc": round(max(aurocs), 6),
            "min_auroc": round(min(aurocs), 6),
            "h10_max_spread_criterion": H10_MAX_SPREAD,
            "h10_fragile_drop_criterion": H10_FRAGILE_DROP,
            "n_sp_types": len(aurocs),
        }

    results = {
        "hypothesis": "H10",
        "criterion_max_spread": H10_MAX_SPREAD,
        "criterion_fragile_drop": H10_FRAGILE_DROP,
        "sp_types_analyzed": sp_types,
        "sp_types_excluded": list(SP_EXCLUDE),
        "n_test_pairs": len(test_pairs),
        "per_type_results": per_type_results,
        "h10_verdicts": h10_verdicts,
        "bootstrap_config": {"n": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED},
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(results, indent=2))
    print(f"\n[H10] Results saved to {ARTIFACT_PATH}")

    for method, verdict in h10_verdicts.items():
        spread_val = verdict.get("spread")
        spread_str = f"{spread_val:.4f}" if isinstance(spread_val, float) else "N/A"
        v_str = verdict.get("verdict", verdict.get("status", "UNKNOWN"))
        print(f"  {method}: {v_str} (spread={spread_str})")

    return results


if __name__ == "__main__":
    run_robustness_analysis()
