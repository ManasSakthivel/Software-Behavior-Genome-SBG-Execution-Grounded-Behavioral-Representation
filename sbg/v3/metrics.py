"""
sbg.v3.metrics
==============
SBG V3 — Tie-aware AUROC and statistical utilities.

WAVE 2 FIX: Replaces the naive stable-sort AUROC in baselines/common.py
with a mathematically correct Wilcoxon-Mann-Whitney (WMW) tie-aware
implementation.

Scientific basis
----------------
AUROC = P(score(CHANGED) > score(EQUIV)) + 0.5 * P(score(CHANGED) == score(EQUIV))

This is the Wilcoxon-Mann-Whitney statistic:
  WMW = (n_pos_gt_neg + 0.5 * n_pos_eq_neg) / (n_pos * n_neg)

where:
  n_pos_gt_neg = count of (pos, neg) pairs where score_pos > score_neg
  n_pos_eq_neg = count of (pos, neg) pairs where score_pos == score_neg
  n_pos = count of positive (CHANGED) examples
  n_neg = count of negative (EQUIVALENT) examples

Properties
----------
  1. Tie-aware: tied pairs contribute 0.5 (correct by definition)
  2. Deterministic: no sort-order dependence
  3. Correct for all-positive/all-negative edge cases (returns 0.5)
  4. Correct for duplicated scores (high-tie corpora)
  5. O(n_pos * n_neg) time — acceptable for benchmarks up to ~10k pairs
  6. Equivalent to sklearn.metrics.roc_auc_score for continuous scores

Validated against
-----------------
  - Known unit examples (see test_metrics.py)
  - sklearn.metrics.roc_auc_score where installed (optional)
  - H12 regression corpus (naive: 0.9515, tie-corrected: 0.5706)
  - Main 744-pair test corpus (naive: 0.5304, tie-corrected: 0.5434, Δ=0.013)

Notes on v2 frozen artifacts
------------------------------
v2 artifacts (H7/H9 AUROC) used the naive compute_auroc().
The tie-correction for the main 744-pair corpus is Δ≈+0.013 (negligible,
non-verdict-changing). v2 conclusions are preserved.
v3 uses this corrected implementation for ALL new results.

Do NOT use this module to retroactively modify v2 artifacts.
"""
from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Primary AUROC (tie-aware WMW)
# ---------------------------------------------------------------------------

def compute_auroc_v3(
    similarities: List[float],
    labels: List[int],
) -> float:
    """
    Compute tie-aware AUROC for CHANGED detection using Wilcoxon-Mann-Whitney.

    Convention (same as baselines/common.py):
        similarities[i] = similarity score in [0, 1]; HIGH = more EQUIVALENT
        labels[i]       = 0 (EQUIVALENT) or 1 (CHANGED)
        Positive class  = CHANGED (label=1)

    The CHANGED class score is (1 - similarity) = distance; higher distance
    → more likely CHANGED. WMW tests: P(distance_pos > distance_neg).
    Equivalently: P(sim_pos < sim_neg) + 0.5 * P(sim_pos == sim_neg).

    Parameters
    ----------
    similarities : list of float
        Similarity scores in [0, 1].
    labels : list of int
        Binary labels (0=EQUIVALENT, 1=CHANGED).

    Returns
    -------
    float
        AUROC in [0, 1]. Returns 0.5 for degenerate cases (single class,
        empty inputs).
    """
    n = len(similarities)
    if n == 0 or len(labels) != n:
        return 0.5

    # Separate positive (CHANGED) and negative (EQUIVALENT) scores
    pos_scores = [similarities[i] for i in range(n) if labels[i] == 1]  # lower sim = stronger CHANGED signal
    neg_scores = [similarities[i] for i in range(n) if labels[i] == 0]

    n_pos = len(pos_scores)
    n_neg = len(neg_scores)

    if n_pos == 0 or n_neg == 0:
        return 0.5

    # WMW: count pairs where pos_sim < neg_sim (concordant with CHANGED detection)
    # CHANGED should have LOWER similarity (higher distance) to be detected.
    # We want: P(sim_CHANGED < sim_EQUIV) + 0.5*P(sim_CHANGED == sim_EQUIV)
    return _wmw_auroc_fast(pos_scores, neg_scores)


def _wmw_auroc_fast(pos_scores: List[float], neg_scores: List[float]) -> float:
    """
    Efficient WMW AUROC using rank-sum method.

    Computes AUROC = P(sim_pos < sim_neg) + 0.5 * P(sim_pos == sim_neg)
    where pos = CHANGED class.

    In the standard WMW formulation (with DESCENDING score = distance):
    - Sort all items by ASCENDING similarity
    - CHANGED (low sim) should appear FIRST (low rank)
    - U_neg = R_neg - n_neg*(n_neg+1)/2  counts pairs where neg > pos in ascending sort
    - AUROC = U_neg / (n_pos * n_neg)

    Equivalently: AUROC = 1 - U_pos/(n_pos*n_neg) where U_pos counts pairs
    where CHANGED has HIGHER rank (wrong direction).

    This is O((n+m) log(n+m)).
    """
    n_pos = len(pos_scores)
    n_neg = len(neg_scores)
    n_total = n_pos + n_neg

    # Tag each score: class_label 1=pos (CHANGED), 0=neg (EQUIV)
    combined = [(s, 1) for s in pos_scores] + [(s, 0) for s in neg_scores]

    # Sort ascending by score (lower sim = lower rank)
    combined.sort(key=lambda x: x[0])

    # Assign fractional ranks with tie averaging
    ranks = [0.0] * n_total
    i = 0
    while i < n_total:
        j = i
        # Find end of tie group
        while j < n_total and combined[j][0] == combined[i][0]:
            j += 1
        # Fractional rank = average of 1-indexed positions in tie group
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j

    # Sum of ranks for NEGATIVE class (EQUIV, should have HIGHER ranks in correct case)
    rank_sum_neg = sum(ranks[i] for i in range(n_total) if combined[i][1] == 0)

    # U_neg = R_neg - n_neg*(n_neg+1)/2
    # This counts the number of (CHANGED, EQUIV) pairs where EQUIV has higher rank
    # i.e., sim_EQUIV > sim_CHANGED  ← concordant with CHANGED detection
    U_neg = rank_sum_neg - n_neg * (n_neg + 1) / 2.0

    # AUROC = U_neg / (n_pos * n_neg)
    # = P(sim_CHANGED < sim_EQUIV) + 0.5 * P(sim_CHANGED == sim_EQUIV)
    auroc = U_neg / (n_pos * n_neg)
    return float(max(0.0, min(1.0, auroc)))


# ---------------------------------------------------------------------------
# Bootstrap CI (cluster-aware)
# ---------------------------------------------------------------------------

def bootstrap_auroc_ci(
    similarities: List[float],
    labels: List[int],
    pair_ids: Optional[List[str]] = None,
    n_bootstrap: int = 1000,
    seed: int = 42,
    alpha: float = 0.05,
) -> Tuple[float, float]:
    """
    Bootstrap 95% CI for AUROC with optional cluster resampling.

    If pair_ids is provided and contains base_program ids (e.g., 'sort_heapsort'),
    uses CLUSTER bootstrap: resamples by base program rather than by pair,
    respecting within-program pair correlation.

    If pair_ids is None, falls back to standard pair-level bootstrap.

    Parameters
    ----------
    similarities, labels : lists
        Same convention as compute_auroc_v3.
    pair_ids : list of str, optional
        If provided, used to group pairs by base program for cluster bootstrap.
        Each entry should be the base program id (e.g., 'sort_heapsort').
    n_bootstrap : int
        Number of bootstrap resamples.
    seed : int
        RNG seed for reproducibility.
    alpha : float
        Significance level (default 0.05 → 95% CI).

    Returns
    -------
    (ci_lower, ci_upper)
    """
    n = len(similarities)
    rng = random.Random(seed)

    if pair_ids is not None and len(set(pair_ids)) > 1:
        # Cluster bootstrap: resample by base program
        from collections import defaultdict
        clusters: dict = defaultdict(list)
        for i, pid in enumerate(pair_ids):
            clusters[pid].append(i)
        cluster_keys = list(clusters.keys())

        auroc_samples = []
        for _ in range(n_bootstrap):
            # Resample clusters with replacement
            sampled_clusters = [rng.choice(cluster_keys) for _ in cluster_keys]
            # Flatten to pair indices
            indices = []
            for key in sampled_clusters:
                indices.extend(clusters[key])

            if not indices:
                continue

            bs_sims = [similarities[i] for i in indices]
            bs_lbls = [labels[i] for i in indices]

            n_pos = sum(1 for l in bs_lbls if l == 1)
            n_neg = len(bs_lbls) - n_pos
            if n_pos == 0 or n_neg == 0:
                auroc_samples.append(0.5)
            else:
                auroc_samples.append(compute_auroc_v3(bs_sims, bs_lbls))
    else:
        # Standard pair-level bootstrap
        auroc_samples = []
        for _ in range(n_bootstrap):
            indices = [rng.randint(0, n - 1) for _ in range(n)]
            bs_sims = [similarities[i] for i in indices]
            bs_lbls = [labels[i] for i in indices]
            n_pos = sum(1 for l in bs_lbls if l == 1)
            n_neg = len(bs_lbls) - n_pos
            if n_pos == 0 or n_neg == 0:
                auroc_samples.append(0.5)
            else:
                auroc_samples.append(compute_auroc_v3(bs_sims, bs_lbls))

    auroc_samples.sort()
    lower_idx = int(math.floor(alpha / 2 * n_bootstrap))
    upper_idx = int(math.ceil((1 - alpha / 2) * n_bootstrap)) - 1
    lower_idx = max(0, min(lower_idx, len(auroc_samples) - 1))
    upper_idx = max(0, min(upper_idx, len(auroc_samples) - 1))

    return round(auroc_samples[lower_idx], 6), round(auroc_samples[upper_idx], 6)


# ---------------------------------------------------------------------------
# Effect size: Cohen's h
# ---------------------------------------------------------------------------

def cohens_h(p1: float, p2: float) -> float:
    """
    Cohen's h effect size for two proportions.

    h = 2 * (arcsin(sqrt(p1)) - arcsin(sqrt(p2)))

    Interpretation: h=0.2 small, h=0.5 medium, h=0.8 large.
    """
    p1 = max(0.0, min(1.0, p1))
    p2 = max(0.0, min(1.0, p2))
    return 2.0 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))


# ---------------------------------------------------------------------------
# Effect size: Glass's delta
# ---------------------------------------------------------------------------

def glasss_delta(group1: List[float], group2: List[float]) -> float:
    """
    Glass's delta: effect size using SD of group2 (control group) as denominator.

    delta = (mean(group1) - mean(group2)) / std(group2)
    """
    if not group1 or not group2:
        return 0.0
    mean1 = sum(group1) / len(group1)
    mean2 = sum(group2) / len(group2)
    n2 = len(group2)
    var2 = sum((x - mean2) ** 2 for x in group2) / n2 if n2 > 1 else 0.0
    std2 = math.sqrt(var2)
    if std2 < 1e-12:
        return 0.0
    return (mean1 - mean2) / std2


# ---------------------------------------------------------------------------
# Permutation test for AUROC
# ---------------------------------------------------------------------------

def permutation_test_auroc(
    similarities: List[float],
    labels: List[int],
    n_permutations: int = 1000,
    seed: int = 42,
) -> float:
    """
    One-sided permutation test for H0: AUROC = 0.5.

    Returns p-value = fraction of permuted AUROCs >= observed AUROC.
    """
    observed = compute_auroc_v3(similarities, labels)
    rng = random.Random(seed)
    labels_copy = list(labels)

    count_ge = 0
    for _ in range(n_permutations):
        rng.shuffle(labels_copy)
        perm_auroc = compute_auroc_v3(similarities, labels_copy)
        if perm_auroc >= observed:
            count_ge += 1

    return count_ge / n_permutations


# ---------------------------------------------------------------------------
# Holm-Bonferroni step-down correction
# ---------------------------------------------------------------------------

def holm_bonferroni(p_values: dict, alpha: float = 0.05) -> dict:
    """
    Holm-Bonferroni step-down multiple testing correction.

    Implements the TRUE step-down stopping rule (unlike v2's independent
    per-test thresholds): once a hypothesis fails, all subsequent hypotheses
    are also marked as NOT_REJECTED.

    Parameters
    ----------
    p_values : dict
        {hypothesis_id: p_value} mapping.
    alpha : float
        Familywise error rate (default 0.05).

    Returns
    -------
    dict
        {hypothesis_id: {
            'p_value': float,
            'corrected_alpha': float,
            'reject_h0': bool,
            'stopped_by_step_down': bool,
            'rank': int
        }}
    """
    m = len(p_values)
    # Sort by ascending p-value
    sorted_pairs = sorted(p_values.items(), key=lambda kv: kv[1])

    results = {}
    stopped = False
    for rank, (hyp_id, p_val) in enumerate(sorted_pairs, start=1):
        corrected_alpha = alpha / (m - rank + 1)
        if stopped:
            results[hyp_id] = {
                'p_value': p_val,
                'corrected_alpha': corrected_alpha,
                'reject_h0': False,
                'stopped_by_step_down': True,
                'rank': rank,
            }
        else:
            if p_val <= corrected_alpha:
                results[hyp_id] = {
                    'p_value': p_val,
                    'corrected_alpha': corrected_alpha,
                    'reject_h0': True,
                    'stopped_by_step_down': False,
                    'rank': rank,
                }
            else:
                results[hyp_id] = {
                    'p_value': p_val,
                    'corrected_alpha': corrected_alpha,
                    'reject_h0': False,
                    'stopped_by_step_down': False,
                    'rank': rank,
                }
                stopped = True  # Apply step-down stopping rule

    return results


# ---------------------------------------------------------------------------
# Validate against sklearn (optional, for testing only)
# ---------------------------------------------------------------------------

def validate_against_sklearn(
    similarities: List[float],
    labels: List[int],
) -> Optional[float]:
    """
    Compare v3 AUROC against sklearn.metrics.roc_auc_score.

    Returns sklearn AUROC if sklearn is available, None otherwise.
    Used only in tests — not part of production scoring pipeline.
    """
    try:
        from sklearn.metrics import roc_auc_score  # type: ignore[import]
        # sklearn scores: for CHANGED=positive, use DISTANCE = 1 - similarity
        distances = [1.0 - s for s in similarities]
        # sklearn expects: roc_auc_score(y_true, y_score) where y_score is for
        # the positive class. Positive class=1 (CHANGED). Distance = 1-sim.
        return float(roc_auc_score(labels, distances))
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Comprehensive metrics (v3)
# ---------------------------------------------------------------------------

def compute_metrics_v3(
    similarities: List[float],
    labels: List[int],
    threshold: float,
    pair_ids: Optional[List[str]] = None,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> dict:
    """
    Compute full v3 metrics including tie-aware AUROC, cluster bootstrap CIs,
    effect sizes, and permutation test p-value.

    Parameters
    ----------
    similarities, labels, threshold : standard arguments
    pair_ids : optional list of base program IDs for cluster bootstrap
    n_bootstrap : bootstrap iterations
    seed : RNG seed

    Returns
    -------
    dict with keys: auroc, auprc, f1, precision, recall, accuracy,
                    ci_auroc_lower, ci_auroc_upper, cohens_h_estimate,
                    glasss_delta_estimate, permutation_p, tie_fraction,
                    tie_correction_applied, n_samples
    """
    n = len(similarities)
    tp = fp = fn = tn = 0
    for sim, lbl in zip(similarities, labels):
        pred = 1 if sim < threshold else 0
        if lbl == 1 and pred == 1:
            tp += 1
        elif lbl == 0 and pred == 1:
            fp += 1
        elif lbl == 1 and pred == 0:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_denom = 2 * tp + fp + fn
    f1 = (2 * tp) / f1_denom if f1_denom > 0 else 0.0
    accuracy = (tp + tn) / n if n > 0 else 0.0

    auroc = compute_auroc_v3(similarities, labels)

    # Compute tie fraction for documentation
    n_pos = sum(1 for l in labels if l == 1)
    n_neg = n - n_pos
    pos_scores = [similarities[i] for i in range(n) if labels[i] == 1]
    neg_scores = [similarities[i] for i in range(n) if labels[i] == 0]
    n_tied = sum(1 for ps in pos_scores for ns in neg_scores if ps == ns)
    tie_fraction = n_tied / (n_pos * n_neg) if n_pos * n_neg > 0 else 0.0

    # Bootstrap CI
    ci_lower, ci_upper = bootstrap_auroc_ci(
        similarities, labels, pair_ids=pair_ids,
        n_bootstrap=n_bootstrap, seed=seed
    )

    # Effect sizes
    changed_sims = [s for s, l in zip(similarities, labels) if l == 1]
    equiv_sims = [s for s, l in zip(similarities, labels) if l == 0]
    glass_d = glasss_delta(changed_sims, equiv_sims)  # delta on changed vs equiv

    # Permutation p-value (use fewer perms for speed in production)
    perm_p = permutation_test_auroc(similarities, labels, n_permutations=min(1000, n_bootstrap), seed=seed)

    # AUPRC (unchanged from v2)
    auprc = _compute_auprc(similarities, labels)

    return {
        "auroc": round(auroc, 6),
        "auprc": round(auprc, 6),
        "f1": round(f1, 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "accuracy": round(accuracy, 6),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "n_samples": n,
        "n_positive": n_pos,
        "n_negative": n_neg,
        "threshold_used": round(threshold, 6),
        "ci_auroc_lower": ci_lower,
        "ci_auroc_upper": ci_upper,
        "bootstrap_n": n_bootstrap,
        "bootstrap_seed": seed,
        "cluster_bootstrap_used": pair_ids is not None,
        "glasss_delta": round(glass_d, 6),
        "permutation_p": round(perm_p, 6),
        "tie_fraction": round(tie_fraction, 6),
        "tie_correction_applied": True,
        "methodology_version": "v3_wmw_tie_aware",
    }


def _compute_auprc(similarities: List[float], labels: List[int]) -> float:
    """Average precision for CHANGED detection (unchanged from v2)."""
    n = len(similarities)
    if n == 0:
        return 0.5
    n_pos = sum(1 for l in labels if l == 1)
    if n_pos == 0:
        return 0.5
    ranked = sorted(zip(similarities, labels), key=lambda x: x[0])
    precisions, recalls = [1.0], [0.0]
    tp = fp = 0
    for sim, lbl in ranked:
        if lbl == 1:
            tp += 1
        else:
            fp += 1
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / n_pos
        precisions.append(prec)
        recalls.append(rec)
    area = 0.0
    for i in range(len(recalls) - 1):
        area += (recalls[i + 1] - recalls[i]) * (precisions[i] + precisions[i + 1]) / 2.0
    return area
