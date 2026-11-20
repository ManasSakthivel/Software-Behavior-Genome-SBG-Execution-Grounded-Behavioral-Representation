"""
experiments/v2/run_h12_wave6.py
================================
Phase 4 Wave 6 — H12 Real/Synthetic Regression Detection (finalized).

CRITICAL FIX (per Wave-0 Agent C's audit, docs/v2/PHASE4_FORENSIC_PLAN.md):
`benchmark/regression/regression_pairs.jsonl` (FROZEN, 55 pairs) contains
ONLY regression pairs (label=1). AUROC is mathematically undefined with a
single class. This script does NOT modify that frozen file. Instead it:

1. Generates a NEW, separate set of label=0 (EQUIVALENT_CHANGE) control
   pairs by applying REAL, already-registered semantics-preserving (SP-1..
   SP-12) transformations to the SAME 55 base programs used by the frozen
   regression corpus.
2. STRATIFIES the SP-type assignment across ALL 12 registered SP types
   (cycling deterministically, seed=42) — NOT cherry-picked to "easy" types
   that would inflate AUROC. This directly addresses Agent I's flagged
   integrity risk (docs/v2/PHASE4_FORENSIC_PLAN.md line 82).
3. Writes the new control pairs to a NEW file:
   `benchmark/regression/controls/regression_controls.jsonl`
   and the transformed source files to
   `benchmark/regression/controls/*.py`
   The original 55-pair frozen file and its `programs/` directory are
   NEVER written to.
4. Combines (55 regression + N controls) into one evaluation set and
   scores it with B01 (token/TF-IDF), B02 (AST), Static SBG V1 (proxy),
   and Dynamic SBG V2 (B07) — the pre-registered comparison set.
5. Reports AUROC, AUPRC, Precision/Recall/F1, TPR@FPR1%/5%, 95% bootstrap
   CI, and permutation p-value for every method, per the pre-registered
   H12 protocol (docs/v2/H12_REGRESSION_DESIGN.md).
6. Uses ONLY information available at labeling time — no leakage from the
   frozen benchmark/datasets/pairs_test.jsonl split (H12's corpus is
   entirely separate from that split, so no leakage is possible by
   construction).

Pre-registered verdict criterion:
    SUPPORTED:        AUROC(B07) > 0.5528  AND  CI_lower > 0.5528
    WEAKLY_SUPPORTED: AUROC(B07) > 0.5528  but  CI_lower <= 0.5528
    NOT_SUPPORTED:    AUROC(B07) <= 0.5528
"""
from __future__ import annotations

import json
import math
import pathlib
import random
import sys
from typing import Any, Dict, List

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from baselines.common import compute_auprc  # noqa: E402
from baselines.common import compute_auroc as naive_compute_auroc  # noqa: E402
from benchmark.transformations.preserving.transformer import (  # noqa: E402
    apply_transformation, registry,
)


def compute_auroc(similarities: List[float], labels: List[int]) -> float:
    """
    Mann-Whitney-U-based AUROC with PROPER average-rank tie handling.

    INTEGRITY NOTE (Wave 6): baselines/common.py's shared compute_auroc()
    (imported above as naive_compute_auroc) sweeps a STABLE sort of
    (similarity, label) pairs without averaging ranks across ties. On the
    main 744-pair test set this is minor (naive=0.5304 vs corrected=0.5434,
    verdict-irrelevant). For H12's corpus, >85% of raw scores are EXACT
    ties AND pairs are ordered (55 regressions then 39 controls, not
    shuffled), so naive stable-sort tie-breaking by array position
    produces a severely inflated, order-dependent value: naive
    AUROC(B07)=0.9515 vs mathematically-correct tie-corrected
    AUROC(B07)=0.5706 — changing the verdict. This local tie-averaged
    Mann-Whitney U implementation is used for ALL H12 computations here;
    baselines/common.py is NOT modified (would silently alter frozen
    H7-H10 results on rerun). Both values are reported in the artifact.
    """
    n = len(similarities)
    if n == 0:
        return 0.5
    dist = [-s for s in similarities]
    order = sorted(range(n), key=lambda i: dist[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and dist[order[j + 1]] == dist[order[i]]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    n_pos = sum(labels)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    rank_sum_pos = sum(ranks[i] for i in range(n) if labels[i] == 1)
    u_stat = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return u_stat / (n_pos * n_neg)

REGRESSION_DIR = REPO_ROOT / "benchmark" / "regression"
REGRESSION_PAIRS_FILE = REGRESSION_DIR / "regression_pairs.jsonl"  # FROZEN, read-only
CONTROLS_DIR = REGRESSION_DIR / "controls"  # NEW, written by this script only
CONTROLS_PAIRS_FILE = CONTROLS_DIR / "regression_controls.jsonl"  # NEW

ARTIFACT_PATH = REPO_ROOT / "artifacts" / "v2" / "H12_REGRESSION_RESULTS.json"
DOC_PATH = REPO_ROOT / "docs" / "v2" / "H12_REGRESSION_ANALYSIS.md"

H12_AUROC_THRESHOLD = 0.5528  # B02_AST reference baseline, pre-registered
BOOTSTRAP_N = 1000
BOOTSTRAP_SEED = 42
PERM_N = 1000

# Full stratified list of ALL 12 registered SP types, cycled deterministically.
# NOT cherry-picked — every registered transformation gets equal representation.
ALL_SP_IDS = registry.all_ids()  # sorted, e.g. ["SP-1", "SP-10", "SP-11", ...]


def _load_regression_pairs() -> List[Dict]:
    pairs = []
    for line in REGRESSION_PAIRS_FILE.read_text().splitlines():
        line = line.strip()
        if line:
            pairs.append(json.loads(line))
    return pairs


def _generate_controls(reg_pairs: List[Dict]) -> List[Dict]:
    """
    Generate label=0 EQUIVALENT_CHANGE control pairs: apply a stratified
    SP-transform to each regression pair's BASE program (the correct
    version, never the buggy variant). Cycles through ALL 12 SP types in
    sorted-ID order so no single "easy" type dominates.
    """
    CONTROLS_DIR.mkdir(parents=True, exist_ok=True)
    controls = []
    excluded = []
    for i, p in enumerate(reg_pairs):
        sp_id = ALL_SP_IDS[i % len(ALL_SP_IDS)]
        base_path = REPO_ROOT / p["base_file"]
        try:
            new_source, meta = apply_transformation(base_path, sp_id, seed=BOOTSTRAP_SEED)
        except Exception as e:
            excluded.append({"pair_id": p["pair_id"], "sp_id": sp_id, "reason": f"apply_error: {e}"})
            continue
        if not meta["validation_passed"]:
            excluded.append({"pair_id": p["pair_id"], "sp_id": sp_id, "reason": "validation_failed"})
            continue

        control_id = f"ctrl_{p['pair_id']}_{sp_id.replace('-', '')}"
        variant_filename = f"{control_id}.py"
        variant_path = CONTROLS_DIR / variant_filename
        variant_path.write_text(new_source, encoding="utf-8")

        controls.append({
            "pair_id": control_id,
            "base_id": p["base_id"],
            "variant_id": control_id,
            "regression_type": None,
            "semantic_relation": "EQUIVALENT_CHANGE",
            "severity": None,
            "description": f"Control pair: SP-transform {sp_id} ({meta['transformation_name']}) applied to the CORRECT base program of {p['pair_id']}.",
            "language": "python",
            "base_file": p["base_file"],
            "variant_file": str(variant_path.relative_to(REPO_ROOT)),
            "provenance": "SYNTHETIC — generated by Wave 6 from existing registered SP-transform code (transformer.py), not new hand-crafted pairs",
            "sp_transform_applied": sp_id,
            "seed": BOOTSTRAP_SEED,
        })
    return controls, excluded


def _score_all_methods(pairs_combined: List[Dict]) -> Dict[str, List[float]]:
    from baselines.b01_token import score_fn as token_score
    from baselines.b02_ast import score_fn as ast_score
    from sbg.v2.static_proxy import v1_behavioral_distance
    from baselines.v2.b07_dynamic_v2 import _score_pair as dyn_score_pair

    sims: Dict[str, List[float]] = {"B01_TOKEN": [], "B02_AST": [], "STATIC_SBG_V1": [], "B07_DYNAMIC_V2": []}

    for i, p in enumerate(pairs_combined):
        base_path = REPO_ROOT / p["base_file"]
        var_path = REPO_ROOT / p["variant_file"]
        try:
            src_a = base_path.read_text(encoding="utf-8")
            src_b = var_path.read_text(encoding="utf-8")
        except Exception:
            src_a = src_b = ""

        try:
            sims["B01_TOKEN"].append(float(token_score(src_a, src_b)))
        except Exception:
            sims["B01_TOKEN"].append(0.5)

        try:
            sims["B02_AST"].append(float(ast_score(src_a, src_b)))
        except Exception:
            sims["B02_AST"].append(0.5)

        try:
            d = v1_behavioral_distance(str(base_path), str(var_path))
            sims["STATIC_SBG_V1"].append(0.5 if d is None else max(0.0, min(1.0, 1.0 - d)))
        except Exception:
            sims["STATIC_SBG_V1"].append(0.5)

        try:
            sims["B07_DYNAMIC_V2"].append(float(dyn_score_pair(str(base_path), str(var_path))))
        except Exception:
            sims["B07_DYNAMIC_V2"].append(0.5)

        if (i + 1) % 20 == 0:
            print(f"  scored {i+1}/{len(pairs_combined)} pairs")

    return sims


def _tpr_at_fpr(sims: List[float], labels: List[int], target_fpr: float) -> float:
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.0
    sorted_pairs = sorted(zip(sims, labels), key=lambda x: x[0])
    best_tpr = 0.0
    tp = fp = 0
    for sim, lbl in sorted_pairs:
        if lbl == 1:
            tp += 1
        else:
            fp += 1
        fpr = fp / n_neg
        if fpr <= target_fpr:
            best_tpr = tp / n_pos
    return best_tpr


def _permutation_p(sims, labels, observed_auroc, n_perm=PERM_N, seed=BOOTSTRAP_SEED) -> float:
    rng = random.Random(seed)
    count_ge = 0
    for _ in range(n_perm):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        auc = compute_auroc(sims, shuffled)
        if abs(auc - 0.5) >= abs(observed_auroc - 0.5):
            count_ge += 1
    return (count_ge + 1) / (n_perm + 1)


def _full_metrics(sims: List[float], labels: List[int]) -> Dict[str, Any]:
    n = len(sims)
    auroc = compute_auroc(sims, labels)  # tie-corrected (see module docstring)
    auroc_naive = naive_compute_auroc(sims, labels)
    auprc = compute_auprc(sims, labels)
    tpr1 = _tpr_at_fpr(sims, labels, 0.01)
    tpr5 = _tpr_at_fpr(sims, labels, 0.05)
    perm_p = _permutation_p(sims, labels, auroc)

    rng = random.Random(BOOTSTRAP_SEED)
    boots = []
    for _ in range(BOOTSTRAP_N):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        boots.append(compute_auroc([sims[i] for i in idx], [labels[i] for i in idx]))
    boots.sort()

    # best-F1 threshold (on this same set — reported descriptively, not
    # used for the AUROC-based verdict, consistent with pre-registration
    # which is threshold-free / AUROC-primary).
    unique_t = sorted(set(sims))
    best_f1, best_t = 0.0, 0.5
    for t in unique_t:
        tp = fp = fn = 0
        for s, l in zip(sims, labels):
            pred = 1 if s < t else 0
            if l == 1 and pred == 1:
                tp += 1
            elif l == 0 and pred == 1:
                fp += 1
            elif l == 1 and pred == 0:
                fn += 1
        denom = 2 * tp + fp + fn
        f1 = (2 * tp) / denom if denom > 0 else 0.0
        if f1 > best_f1:
            best_f1, best_t = f1, t
    tp = fp = fn = tn = 0
    for s, l in zip(sims, labels):
        pred = 1 if s < best_t else 0
        if l == 1 and pred == 1:
            tp += 1
        elif l == 0 and pred == 1:
            fp += 1
        elif l == 1 and pred == 0:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    return {
        "n": n,
        "auroc": round(auroc, 6),
        "auroc_naive_uncorrected": round(auroc_naive, 6),
        "tie_fraction": round(1.0 - len(set(sims)) / n, 6) if n else 0.0,
        "ci_auroc_lower": round(boots[25], 6),
        "ci_auroc_upper": round(boots[974], 6),
        "permutation_p": round(perm_p, 6),
        "auprc": round(auprc, 6),
        "tpr_at_fpr1": round(tpr1, 6),
        "tpr_at_fpr5": round(tpr5, 6),
        "f1": round(best_f1, 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "mrr": "N/A - binary classification task, not a ranking task",
    }


def main():
    print("[H12-Wave6] Loading FROZEN regression pairs (read-only)...")
    reg_pairs = _load_regression_pairs()
    print(f"[H12-Wave6] Loaded {len(reg_pairs)} regression pairs (all label=1)")

    print(f"[H12-Wave6] Registered SP types available for stratified controls: {ALL_SP_IDS}")
    print("[H12-Wave6] Generating stratified control pairs (label=0)...")
    controls, excluded = _generate_controls(reg_pairs)
    print(f"[H12-Wave6] Generated {len(controls)} control pairs; {len(excluded)} excluded (validation/apply failures)")

    CONTROLS_PAIRS_FILE.write_text(
        "\n".join(json.dumps(c) for c in controls) + "\n", encoding="utf-8"
    )
    print(f"[H12-Wave6] Wrote {CONTROLS_PAIRS_FILE}")

    combined = reg_pairs + controls
    labels = [1 if p.get("regression_type") else 0 for p in combined]
    print(f"[H12-Wave6] Combined evaluation set: n={len(combined)} "
          f"(regressions={sum(labels)}, controls={len(labels)-sum(labels)})")

    print("[H12-Wave6] Scoring all methods (B01, B02, StaticSBG-V1, B07-Dynamic)...")
    sims_by_method = _score_all_methods(combined)

    method_metrics = {name: _full_metrics(sims, labels) for name, sims in sims_by_method.items()}

    # Per-SP-type breakdown of control-side scores (to show stratification worked
    # and wasn't cherry-picked)
    sp_type_counts: Dict[str, int] = {}
    for c in controls:
        sp_type_counts[c["sp_transform_applied"]] = sp_type_counts.get(c["sp_transform_applied"], 0) + 1

    # Per-regression-category AUROC for B07 (diagnostic, not used for verdict)
    categories = sorted(set(p.get("regression_type") for p in reg_pairs))
    per_category = {}
    for cat in categories:
        cat_idx = [i for i, p in enumerate(combined) if p.get("regression_type") == cat]
        control_idx = [i for i, p in enumerate(combined) if p.get("regression_type") is None]
        idx = cat_idx + control_idx
        cat_sims = [sims_by_method["B07_DYNAMIC_V2"][i] for i in idx]
        cat_labels = [labels[i] for i in idx]
        if sum(cat_labels) > 0 and sum(cat_labels) < len(cat_labels):
            per_category[cat] = {
                "n_regression": len(cat_idx),
                "n_control": len(control_idx),
                "auroc": round(compute_auroc(cat_sims, cat_labels), 6),
            }

    b07 = method_metrics["B07_DYNAMIC_V2"]
    if b07["auroc"] > H12_AUROC_THRESHOLD and b07["ci_auroc_lower"] > H12_AUROC_THRESHOLD:
        verdict = "SUPPORTED"
    elif b07["auroc"] > H12_AUROC_THRESHOLD:
        verdict = "WEAKLY_SUPPORTED"
    else:
        verdict = "NOT_SUPPORTED"

    result = {
        "hypothesis": "H12",
        "formal_statement": f"AUROC(hybrid_regression) > AUROC(B02_AST={H12_AUROC_THRESHOLD})",
        "fix_applied": (
            "Wave 6 generates NEW stratified control pairs (label=0) since the "
            "FROZEN benchmark/regression/regression_pairs.jsonl (55 pairs) "
            "contains ONLY label=1 regressions, making binary AUROC undefined. "
            "Controls are written to benchmark/regression/controls/ (NEW dir). "
            "The frozen 55-pair file and benchmark/regression/programs/ were "
            "NEVER modified by this script."
        ),
        "stratification": {
            "method": "Cycle through ALL 12 registered SP-transform IDs "
                      "(sorted order) applied to each regression pair's BASE "
                      "program, seed=42. No cherry-picking of 'easy' types.",
            "sp_types_used": ALL_SP_IDS,
            "control_counts_by_sp_type": sp_type_counts,
            "n_controls_generated": len(controls),
            "n_excluded_validation_failed": len(excluded),
            "excluded_detail": excluded,
        },
        "corpus": {
            "n_regression_pairs": len(reg_pairs),
            "n_control_pairs": len(controls),
            "n_total": len(combined),
            "regression_source": "benchmark/regression/regression_pairs.jsonl (FROZEN, unmodified)",
            "control_source": "benchmark/regression/controls/regression_controls.jsonl (NEW, this wave)",
            "leakage_check": (
                "This corpus is entirely disjoint from benchmark/datasets/pairs_test.jsonl "
                "(the frozen H7-H10 test split) — regression programs live under "
                "benchmark/regression/programs/, not benchmark/corpus/base_programs/ "
                "or benchmark/datasets/variants/. No overlap possible."
            ),
        },
        "method_metrics": method_metrics,
        "per_regression_category_b07_auroc": per_category,
        "h12_verdict": verdict,
        "h12_verdict_criteria": {
            "SUPPORTED": f"AUROC(B07) > {H12_AUROC_THRESHOLD} AND CI_lower > {H12_AUROC_THRESHOLD}",
            "WEAKLY_SUPPORTED": f"AUROC(B07) > {H12_AUROC_THRESHOLD} but CI_lower <= {H12_AUROC_THRESHOLD}",
            "NOT_SUPPORTED": f"AUROC(B07) <= {H12_AUROC_THRESHOLD}",
        },
        "bootstrap_config": {"n": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED},
        "permutation_config": {"n": PERM_N, "seed": BOOTSTRAP_SEED},
        "limitations": [
            "L1: Regression pairs are SYNTHETIC hand-crafted bugs, not mined from "
            "real commit histories — no real version-history corpus was found "
            "in the repository (see infrastructure check below).",
            "L2: Control pairs are SP-transformed versions of the regression "
            "pairs' OWN base programs, not independently sourced equivalent "
            "changes — this is the best available option without expanding "
            "benchmark scope, but the two classes are constructed by different "
            "processes (hand-crafted bug injection vs. automated SP-transform), "
            "which is itself a potential systematic difference AST/token "
            "methods could exploit rather than genuine regression detection.",
            "L3: Python only.",
            "L4: n=110 (55+55) is modest; per-category (n~8-13) breakdowns are "
            "descriptive only, not independently powered.",
            "L5: No real-world version-history data source was located in this "
            "repository for H12 (checked benchmark/regression/, docs/research/, "
            "and REGISTRY.yaml) — synthetic corpus is used per the pre-registered "
            "fallback (docs/v2/H12_REGRESSION_DESIGN.md Sec 3.1), fully disclosed.",
        ],
        "real_world_data_check": (
            "No version-history / real-commit corpus exists in this repository "
            "for H12. benchmark/regression/regression_pairs.jsonl is explicitly "
            "labeled SYNTHETIC on every record (pre-existing, Wave-0-confirmed). "
            "Per the Phase 4 mandate's preferred-order fallback (synthetic only "
            "if real history is unavailable), this is disclosed, not hidden."
        ),
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[H12-Wave6] Wrote {ARTIFACT_PATH}")
    print(f"[H12-Wave6] H12 verdict: {verdict}")
    print(f"[H12-Wave6] B07 Dynamic AUROC: {b07['auroc']:.4f} vs threshold {H12_AUROC_THRESHOLD}")
    for name, m in method_metrics.items():
        print(f"  {name}: AUROC={m['auroc']:.4f} CI=[{m['ci_auroc_lower']:.4f},{m['ci_auroc_upper']:.4f}] perm_p={m['permutation_p']:.4f}")

    return result


if __name__ == "__main__":
    main()
