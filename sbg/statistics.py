"""
sbg.statistics
==============
Corrected statistical procedures for the SBG evaluation.

Why this module exists
----------------------
``sbg.v3.metrics`` provides a correct tie-aware AUROC, but three procedures
around it were either unused or anti-conservative in the V5 experiment scripts:

1. ``bootstrap_auroc_ci`` performs a cluster bootstrap only when ``pair_ids`` is
   passed. ``baselines/v5/b07_dynamic_v5.py`` never passed it, so the published
   V5 confidence interval was a pair-level bootstrap while the artifact's
   ``methodology`` field claimed ``cluster_by_base_program``. Benchmark pairs
   that share a base program are strongly correlated, so the pair-level
   interval is too narrow.

2. ``permutation_test_auroc`` shuffles labels across the whole sample, which
   breaks the clustering in the same way and yields anti-conservative p-values.

3. It returns ``count_ge / n_permutations``, which can be exactly 0. A Monte
   Carlo p-value must be ``(count_ge + 1) / (n_permutations + 1)``; the
   smallest reportable value is then 1/(m+1), not 0.

This module fixes all three and adds a clustered *paired* bootstrap for the
difference between two predictors evaluated on the same pairs — the comparison
the research question actually needs, and one that overlapping marginal
confidence intervals cannot answer.

Score convention
----------------
Every function here takes ``distances``: higher = more likely CHANGED
(label 1). This is the natural direction for a behavioural distance and avoids
the similarity/distance inversion that the V3 helpers carry.

``sbg.v3.metrics`` is left untouched so previously frozen artifacts remain
reproducible exactly as published.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# AUROC
# ---------------------------------------------------------------------------

def auroc(distances: Sequence[float], labels: Sequence[int]) -> float:
    """Tie-aware Wilcoxon-Mann-Whitney AUROC.

    AUROC = P(d_pos > d_neg) + 0.5 * P(d_pos == d_neg)

    Returns 0.5 for degenerate input (empty, mismatched, or single-class).
    """
    n = len(distances)
    if n == 0 or len(labels) != n:
        return 0.5

    combined = sorted(zip(distances, labels), key=lambda t: t[0])
    n_pos = sum(1 for _, y in combined if y == 1)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5

    # Mid-ranks over ascending distance.
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and combined[j][0] == combined[i][0]:
            j += 1
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg
        i = j

    rank_sum_pos = sum(ranks[k] for k in range(n) if combined[k][1] == 1)
    u_pos = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return float(max(0.0, min(1.0, u_pos / (n_pos * n_neg))))


# ---------------------------------------------------------------------------
# Clustered bootstrap confidence interval
# ---------------------------------------------------------------------------

def cluster_bootstrap_ci(
    distances: Sequence[float],
    labels: Sequence[int],
    clusters: Sequence[str],
    n_bootstrap: int = 2000,
    seed: int = 42,
    alpha: float = 0.05,
) -> Tuple[float, float, int]:
    """Percentile bootstrap CI resampling whole clusters with replacement.

    ``clusters[i]`` is the unit of independence for pair ``i`` — for this
    benchmark, the base program id. Resampling clusters (not pairs) is what
    makes the interval honest about within-program correlation.

    Returns ``(lower, upper, n_effective)`` where ``n_effective`` is the number
    of bootstrap resamples that contained both classes and so produced a
    defined AUROC. Degenerate resamples are discarded rather than pinned to
    0.5, which would shrink the interval toward the null.
    """
    by_cluster: Dict[str, List[int]] = defaultdict(list)
    for index, key in enumerate(clusters):
        by_cluster[key].append(index)
    keys = sorted(by_cluster)
    if len(keys) < 2:
        point = auroc(distances, labels)
        return point, point, 0

    rng = random.Random(seed)
    samples: List[float] = []
    for _ in range(n_bootstrap):
        indices: List[int] = []
        for _ in keys:
            indices.extend(by_cluster[keys[rng.randrange(len(keys))]])
        bs_labels = [labels[i] for i in indices]
        if 0 < sum(bs_labels) < len(bs_labels):
            samples.append(auroc([distances[i] for i in indices], bs_labels))

    if not samples:
        point = auroc(distances, labels)
        return point, point, 0

    samples.sort()
    lower = samples[max(0, int(math.floor(alpha / 2 * len(samples))))]
    upper = samples[min(len(samples) - 1,
                        int(math.ceil((1 - alpha / 2) * len(samples))) - 1)]
    return round(lower, 6), round(upper, 6), len(samples)


# ---------------------------------------------------------------------------
# Clustered permutation test
# ---------------------------------------------------------------------------

def cluster_permutation_p(
    distances: Sequence[float],
    labels: Sequence[int],
    clusters: Sequence[str],
    n_permutations: int = 2000,
    seed: int = 42,
) -> float:
    """One-sided Monte Carlo p-value for H0: AUROC = 0.5.

    Labels are permuted *within* each cluster, which preserves both the
    per-cluster class balance and the cluster structure. The returned value
    uses the ``(b + 1) / (m + 1)`` estimator, so the smallest reportable
    p-value is ``1 / (n_permutations + 1)`` and never exactly zero.
    """
    observed = auroc(distances, labels)
    by_cluster: Dict[str, List[int]] = defaultdict(list)
    for index, key in enumerate(clusters):
        by_cluster[key].append(index)

    rng = random.Random(seed)
    permuted_labels = list(labels)
    count_ge = 0
    for _ in range(n_permutations):
        for indices in by_cluster.values():
            pool = [labels[i] for i in indices]
            rng.shuffle(pool)
            for slot, value in zip(indices, pool):
                permuted_labels[slot] = value
        if auroc(distances, permuted_labels) >= observed:
            count_ge += 1
    return (count_ge + 1) / (n_permutations + 1)


# ---------------------------------------------------------------------------
# Paired clustered bootstrap for a difference of AUROCs
# ---------------------------------------------------------------------------

def paired_cluster_bootstrap_delta(
    distances_a: Sequence[float],
    distances_b: Sequence[float],
    labels: Sequence[int],
    clusters: Sequence[str],
    n_bootstrap: int = 2000,
    seed: int = 42,
    alpha: float = 0.05,
) -> Dict[str, float]:
    """CI and two-sided p-value for AUROC(a) - AUROC(b) on the same pairs.

    Both predictors are recomputed on each resampled cluster set, so the
    resampling is paired and the correlation between the two predictors is
    carried through. Comparing two marginal confidence intervals for overlap
    is not a test of their difference; this is.
    """
    if not (len(distances_a) == len(distances_b) == len(labels) == len(clusters)):
        raise ValueError("all inputs must have the same length")

    observed = auroc(distances_a, labels) - auroc(distances_b, labels)

    by_cluster: Dict[str, List[int]] = defaultdict(list)
    for index, key in enumerate(clusters):
        by_cluster[key].append(index)
    keys = sorted(by_cluster)

    rng = random.Random(seed)
    deltas: List[float] = []
    for _ in range(n_bootstrap):
        indices: List[int] = []
        for _ in keys:
            indices.extend(by_cluster[keys[rng.randrange(len(keys))]])
        bs_labels = [labels[i] for i in indices]
        if not (0 < sum(bs_labels) < len(bs_labels)):
            continue
        deltas.append(
            auroc([distances_a[i] for i in indices], bs_labels)
            - auroc([distances_b[i] for i in indices], bs_labels)
        )

    if not deltas:
        return {"delta": round(observed, 6), "ci_lower": None, "ci_upper": None,
                "p_two_sided": None, "n_effective": 0}

    deltas.sort()
    lower = deltas[max(0, int(math.floor(alpha / 2 * len(deltas))))]
    upper = deltas[min(len(deltas) - 1,
                       int(math.ceil((1 - alpha / 2) * len(deltas))) - 1)]
    # Two-sided bootstrap p-value: proportion of resamples on the far side of 0,
    # doubled, with the (b + 1) / (m + 1) correction.
    n_le = sum(1 for d in deltas if d <= 0.0)
    n_ge = sum(1 for d in deltas if d >= 0.0)
    m = len(deltas)
    p_two = min(1.0, 2.0 * min(n_le + 1, n_ge + 1) / (m + 1))
    return {"delta": round(observed, 6), "ci_lower": round(lower, 6),
            "ci_upper": round(upper, 6), "p_two_sided": round(p_two, 6),
            "n_effective": m}


# ---------------------------------------------------------------------------
# Label-shuffle noise floor
# ---------------------------------------------------------------------------

def label_shuffle_noise_floor(
    distances: Sequence[float],
    labels: Sequence[int],
    clusters: Sequence[str],
    n_shuffles: int = 500,
    seed: int = 42,
) -> Dict[str, float]:
    """Distribution of AUROC under within-cluster label shuffling.

    The 95th percentile is the AUROC a predictor can reach on this sample by
    chance alone; a result below it is not evidence of signal.
    """
    by_cluster: Dict[str, List[int]] = defaultdict(list)
    for index, key in enumerate(clusters):
        by_cluster[key].append(index)

    rng = random.Random(seed)
    shuffled = list(labels)
    values: List[float] = []
    for _ in range(n_shuffles):
        for indices in by_cluster.values():
            pool = [labels[i] for i in indices]
            rng.shuffle(pool)
            for slot, value in zip(indices, pool):
                shuffled[slot] = value
        values.append(auroc(distances, shuffled))

    values.sort()
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1)
    return {
        "mean": round(mean, 6),
        "std": round(math.sqrt(var), 6),
        "p95": round(values[min(len(values) - 1, int(0.95 * len(values)))], 6),
        "n_shuffles": len(values),
    }


# ---------------------------------------------------------------------------
# Multiple comparison correction
# ---------------------------------------------------------------------------

def holm_bonferroni(p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, dict]:
    """Holm step-down correction. Returns per-key adjusted p and reject flag."""
    ordered = sorted(p_values.items(), key=lambda kv: kv[1])
    m = len(ordered)
    out: Dict[str, dict] = {}
    running_max = 0.0
    still_rejecting = True
    for rank, (key, p) in enumerate(ordered):
        adjusted = min(1.0, (m - rank) * p)
        running_max = max(running_max, adjusted)   # enforce monotonicity
        if running_max > alpha:
            still_rejecting = False
        out[key] = {
            "p_raw": round(p, 6),
            "p_adjusted": round(running_max, 6),
            "reject_at_alpha": bool(still_rejecting and running_max <= alpha),
            "rank": rank + 1,
            "n_comparisons": m,
        }
    return out


# ---------------------------------------------------------------------------
# Binomial proportion CI (Wilson)
# ---------------------------------------------------------------------------

def wilson_interval(successes: int, total: int, z: float = 1.959963985) -> Tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Preferred over the normal approximation for the small detection-rate
    denominators used in the hard-negative and regression experiments, where
    the normal interval can run outside [0, 1] or collapse to zero width at
    0 or 1 successes.
    """
    if total <= 0:
        return (0.0, 1.0)
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return (round(max(0.0, centre - half), 6), round(min(1.0, centre + half), 6))
