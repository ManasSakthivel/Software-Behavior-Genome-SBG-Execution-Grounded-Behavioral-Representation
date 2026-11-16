"""Tests for sbg.statistics — the corrected statistical procedures.

These exist because the procedures they replace were wrong in ways that made
results look stronger than they were: a confidence interval documented as
clustered but computed pair-level, a permutation test that ignored clustering
and could return p = 0 exactly, and a comparison between two predictors made by
eyeballing whether their marginal intervals overlapped.
"""
from __future__ import annotations

import math
import random

import pytest

from sbg.statistics import (
    auroc, cluster_bootstrap_ci, cluster_permutation_p, holm_bonferroni,
    label_shuffle_noise_floor, paired_cluster_bootstrap_delta, wilson_interval,
)
from sbg.v3.metrics import compute_auroc_v3


class TestAuroc:
    def test_perfect_separation(self):
        assert auroc([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]) == 1.0

    def test_perfect_inversion(self):
        assert auroc([0.1, 0.2, 0.8, 0.9], [1, 1, 0, 0]) == 0.0

    def test_all_ties_is_exactly_one_half(self):
        # Every pair tied contributes 0.5. A benchmark where most pairs score 0
        # lands here, which is why the tie handling has to be exact.
        assert auroc([0.5] * 8, [1, 1, 1, 1, 0, 0, 0, 0]) == 0.5

    def test_partial_ties(self):
        # pos {1.0, 0.5}, neg {0.5, 0.0}:
        # (1.0,0.5) win, (1.0,0.0) win, (0.5,0.5) tie, (0.5,0.0) win -> 3.5/4
        assert auroc([1.0, 0.5, 0.5, 0.0], [1, 1, 0, 0]) == pytest.approx(0.875)

    def test_single_class_returns_half(self):
        assert auroc([0.1, 0.9], [1, 1]) == 0.5
        assert auroc([], []) == 0.5

    def test_length_mismatch_returns_half(self):
        assert auroc([0.1, 0.2], [1]) == 0.5

    def test_agrees_with_v3_implementation(self):
        # sbg.v3.metrics takes similarities (1 - distance). Two independent
        # implementations agreeing is the cross-check that neither is inverted.
        rng = random.Random(7)
        for _ in range(20):
            n = rng.randrange(10, 120)
            distances = [rng.random() for _ in range(n)]
            labels = [rng.randrange(2) for _ in range(n)]
            if 0 < sum(labels) < n:
                assert auroc(distances, labels) == pytest.approx(
                    compute_auroc_v3([1 - d for d in distances], labels), abs=1e-12)

    def test_rounding_ties_are_respected(self):
        # Scores rounded to the same value must count as tied, not as ordered
        # by list position.
        assert auroc([0.1000000001, 0.1000000001], [1, 0]) == 0.5


class TestClusterBootstrap:
    def _data(self):
        rng = random.Random(3)
        distances, labels, clusters = [], [], []
        for cluster in range(12):
            for _ in range(20):
                label = rng.randrange(2)
                labels.append(label)
                distances.append(rng.random() + 0.35 * label)
                clusters.append(f"p{cluster}")
        return distances, labels, clusters

    def test_interval_brackets_the_point_estimate(self):
        distances, labels, clusters = self._data()
        low, high, n_effective = cluster_bootstrap_ci(
            distances, labels, clusters, n_bootstrap=400, seed=1)
        point = auroc(distances, labels)
        assert low <= point <= high
        assert n_effective > 0

    def test_clustered_interval_is_not_narrower_than_pair_level(self):
        # The whole point of the correction. Pairs inside a program are
        # correlated, so ignoring the clustering understates the uncertainty.
        rng = random.Random(11)
        distances, labels, clusters = [], [], []
        for cluster in range(8):
            offset = rng.random()          # whole-program effect
            for _ in range(40):
                label = rng.randrange(2)
                labels.append(label)
                distances.append(offset + 0.15 * label + 0.02 * rng.random())
                clusters.append(f"p{cluster}")
        clustered = cluster_bootstrap_ci(distances, labels, clusters,
                                         n_bootstrap=600, seed=2)
        pairwise = cluster_bootstrap_ci(distances, labels,
                                        [str(i) for i in range(len(labels))],
                                        n_bootstrap=600, seed=2)
        assert (clustered[1] - clustered[0]) > (pairwise[1] - pairwise[0])

    def test_deterministic_for_a_fixed_seed(self):
        distances, labels, clusters = self._data()
        first = cluster_bootstrap_ci(distances, labels, clusters, n_bootstrap=200, seed=5)
        second = cluster_bootstrap_ci(distances, labels, clusters, n_bootstrap=200, seed=5)
        assert first == second


class TestPermutation:
    def test_p_value_is_never_zero(self):
        # (b + 1) / (m + 1): the floor is 1/(m+1), never 0. Reporting p = 0.0
        # from a Monte Carlo test overstates the evidence.
        distances = [float(i) for i in range(60)]
        labels = [0] * 30 + [1] * 30
        clusters = ["only"] * 60
        p = cluster_permutation_p(distances, labels, clusters,
                                  n_permutations=100, seed=0)
        assert p >= 1 / 101
        assert p > 0.0

    def test_random_scores_are_not_significant(self):
        rng = random.Random(13)
        n = 200
        distances = [rng.random() for _ in range(n)]
        labels = [rng.randrange(2) for _ in range(n)]
        clusters = [f"p{i % 10}" for i in range(n)]
        p = cluster_permutation_p(distances, labels, clusters,
                                  n_permutations=400, seed=4)
        assert p > 0.05

    def test_strong_signal_is_significant(self):
        n = 200
        labels = [i % 2 for i in range(n)]
        distances = [0.9 if label else 0.1 for label in labels]
        clusters = [f"p{i // 20}" for i in range(n)]   # each cluster holds both classes
        p = cluster_permutation_p(distances, labels, clusters,
                                  n_permutations=400, seed=4)
        assert p < 0.01

    def test_single_class_clusters_have_no_power(self):
        # Within-cluster permutation cannot move a label when every pair in the
        # cluster carries the same one, so the test correctly reports no
        # evidence. The benchmark avoids this: every base program contributes
        # both semantics-preserving and semantics-changing pairs.
        n = 100
        labels = [i % 2 for i in range(n)]
        distances = [0.9 if label else 0.1 for label in labels]
        clusters = [f"p{i % 2}" for i in range(n)]     # cluster == label
        p = cluster_permutation_p(distances, labels, clusters,
                                  n_permutations=200, seed=4)
        assert p == 1.0


class TestPairedComparison:
    def test_identical_predictors_give_zero_delta(self):
        rng = random.Random(21)
        n = 150
        distances = [rng.random() for _ in range(n)]
        labels = [rng.randrange(2) for _ in range(n)]
        clusters = [f"p{i % 8}" for i in range(n)]
        result = paired_cluster_bootstrap_delta(distances, distances, labels,
                                                clusters, n_bootstrap=200, seed=1)
        assert result["delta"] == 0.0
        assert result["ci_lower"] == 0.0 and result["ci_upper"] == 0.0

    def test_detects_a_real_difference(self):
        n = 240
        labels = [i % 2 for i in range(n)]
        clusters = [f"p{i % 12}" for i in range(n)]
        strong = [0.9 if label else 0.1 for label in labels]
        rng = random.Random(2)
        weak = [rng.random() for _ in range(n)]
        result = paired_cluster_bootstrap_delta(strong, weak, labels, clusters,
                                                n_bootstrap=400, seed=3)
        assert result["delta"] > 0.2
        assert result["ci_lower"] > 0.0
        assert result["p_two_sided"] < 0.05

    def test_rejects_mismatched_lengths(self):
        with pytest.raises(ValueError):
            paired_cluster_bootstrap_delta([0.1], [0.1, 0.2], [1], ["a"])


class TestNoiseFloor:
    def test_shuffled_labels_centre_on_one_half(self):
        rng = random.Random(9)
        n = 300
        distances = [rng.random() for _ in range(n)]
        labels = [rng.randrange(2) for _ in range(n)]
        clusters = [f"p{i % 10}" for i in range(n)]
        floor = label_shuffle_noise_floor(distances, labels, clusters,
                                          n_shuffles=200, seed=6)
        assert abs(floor["mean"] - 0.5) < 0.03
        assert floor["p95"] > floor["mean"]


class TestHolmBonferroni:
    def test_single_hypothesis_is_unadjusted(self):
        out = holm_bonferroni({"a": 0.02})
        assert out["a"]["p_adjusted"] == pytest.approx(0.02)
        assert out["a"]["reject_at_alpha"] is True

    def test_step_down_order_and_monotonicity(self):
        out = holm_bonferroni({"a": 0.001, "b": 0.04, "c": 0.3})
        assert out["a"]["p_adjusted"] == pytest.approx(0.003)
        assert out["b"]["p_adjusted"] == pytest.approx(0.08)
        assert out["a"]["reject_at_alpha"] is True
        assert out["b"]["reject_at_alpha"] is False
        assert out["c"]["reject_at_alpha"] is False
        adjusted = [out[k]["p_adjusted"] for k in ("a", "b", "c")]
        assert adjusted == sorted(adjusted)

    def test_adjusted_p_never_exceeds_one(self):
        out = holm_bonferroni({k: 0.9 for k in "abcde"})
        assert all(v["p_adjusted"] <= 1.0 for v in out.values())


class TestWilsonInterval:
    def test_zero_successes_has_positive_upper_bound(self):
        # The normal approximation collapses to [0, 0] here, which would claim
        # certainty from 0/8. The hard-negative and regression experiments both
        # report detection rates at these denominators.
        low, high = wilson_interval(0, 8)
        assert low == 0.0
        assert 0.0 < high < 1.0

    def test_all_successes_has_upper_bound_of_one(self):
        low, high = wilson_interval(8, 8)
        assert high == 1.0
        assert 0.0 < low < 1.0

    def test_interval_contains_the_proportion(self):
        for successes, total in ((3, 15), (7, 15), (5, 12), (1, 7)):
            low, high = wilson_interval(successes, total)
            assert low <= successes / total <= high

    def test_empty_denominator_is_uninformative(self):
        assert wilson_interval(0, 0) == (0.0, 1.0)
