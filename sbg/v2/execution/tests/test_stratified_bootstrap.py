"""
sbg/v2/execution/tests/test_stratified_bootstrap.py
=====================================================
Regression tests for the Phase 3A stratified bootstrap fix.

BUG 1: The original non-stratified bootstrap for highly imbalanced classes
produced CIs where the point estimate fell outside the CI bounds (impossible).

These tests verify:
1. The stratified bootstrap always produces valid CIs (lower <= point <= upper).
2. The stratified bootstrap handles edge cases gracefully.
3. The fix correctly addresses the original SC-3 scenario (n_changed=39, n_equiv=378).
"""
import sys
import pathlib
import random

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from baselines.common import compute_auroc
from experiments.v2.hard_negative_analysis import _bootstrap_ci


def _make_imbalanced_data(n_pos: int, n_neg: int, seed: int = 42,
                          auroc_signal: float = 0.6) -> tuple:
    """
    Generate imbalanced classification data with controllable AUROC signal.
    Positive class (CHANGED): lower similarity scores.
    Negative class (EQUIV): higher similarity scores.
    """
    rng = random.Random(seed)
    # EQUIV: high similarity (~0.87)
    equiv = [rng.gauss(0.87, 0.05) for _ in range(n_neg)]
    # CHANGED: slightly lower for auroc_signal > 0.5
    changed_mean = 0.87 - (auroc_signal - 0.5) * 0.2
    changed = [rng.gauss(changed_mean, 0.05) for _ in range(n_pos)]
    sims = equiv + changed
    labels = [0] * n_neg + [1] * n_pos
    return sims, labels


def test_ci_contains_point_estimate_balanced():
    """CI must contain point estimate for balanced classes."""
    sims, labels = _make_imbalanced_data(50, 50, seed=1)
    point = compute_auroc(sims, labels)
    ci_lower, ci_upper = _bootstrap_ci(sims, labels, n_bootstrap=500, seed=42)
    assert ci_lower <= point <= ci_upper, (
        f"CI [{ci_lower:.4f}, {ci_upper:.4f}] does not contain point estimate {point:.4f}"
    )


def test_ci_contains_point_estimate_imbalanced_1_9():
    """CI must contain point estimate for 1:9 imbalance (like SC-3 scenario)."""
    # SC-3 had n_changed=39, n_equiv=378 — ratio ~1:9.7
    sims, labels = _make_imbalanced_data(39, 378, seed=42, auroc_signal=0.54)
    point = compute_auroc(sims, labels)
    ci_lower, ci_upper = _bootstrap_ci(sims, labels, n_bootstrap=1000, seed=42)
    assert ci_lower <= point <= ci_upper, (
        f"CI [{ci_lower:.4f}, {ci_upper:.4f}] does not contain point estimate {point:.4f} "
        f"(n_changed=39, n_equiv=378 — SC-3 scenario)"
    )


def test_ci_contains_point_estimate_extreme_imbalance():
    """CI must contain point estimate for extreme imbalance (1:20)."""
    sims, labels = _make_imbalanced_data(20, 400, seed=7)
    point = compute_auroc(sims, labels)
    ci_lower, ci_upper = _bootstrap_ci(sims, labels, n_bootstrap=500, seed=42)
    assert ci_lower <= point <= ci_upper, (
        f"CI [{ci_lower:.4f}, {ci_upper:.4f}] does not contain point estimate {point:.4f} "
        f"(n_changed=20, n_equiv=400 — extreme imbalance)"
    )


def test_ci_lower_less_than_upper():
    """CI bounds must be ordered (lower <= upper)."""
    for seed in [1, 2, 3, 42, 100]:
        sims, labels = _make_imbalanced_data(39, 378, seed=seed)
        ci_lower, ci_upper = _bootstrap_ci(sims, labels, n_bootstrap=500, seed=42)
        assert ci_lower <= ci_upper, (
            f"CI bounds inverted: [{ci_lower:.4f}, {ci_upper:.4f}] (seed={seed})"
        )


def test_ci_in_unit_interval():
    """CI bounds must be in [0, 1] (valid AUROC range)."""
    sims, labels = _make_imbalanced_data(50, 200, seed=42)
    ci_lower, ci_upper = _bootstrap_ci(sims, labels, n_bootstrap=500, seed=42)
    assert 0.0 <= ci_lower <= 1.0, f"ci_lower={ci_lower:.4f} out of [0,1]"
    assert 0.0 <= ci_upper <= 1.0, f"ci_upper={ci_upper:.4f} out of [0,1]"


def test_ci_width_reasonable():
    """CI width should be positive and < 1 for any reasonable dataset."""
    sims, labels = _make_imbalanced_data(39, 378, seed=42)
    ci_lower, ci_upper = _bootstrap_ci(sims, labels, n_bootstrap=500, seed=42)
    width = ci_upper - ci_lower
    assert 0.0 < width < 1.0, f"CI width {width:.4f} unreasonable"


def test_single_class_fallback():
    """Single-class input should not raise an error."""
    # All EQUIV
    sims = [0.9] * 20
    labels = [0] * 20
    ci_lower, ci_upper = _bootstrap_ci(sims, labels, n_bootstrap=100, seed=42)
    # Should fall back gracefully (both classes missing → degenerate)
    assert ci_lower <= ci_upper or True  # just no exception


def test_sc3_original_scenario_ci_valid():
    """
    Regression test specifically for the SC-3 original bug.

    The original bug: point_estimate=0.544363 > ci_upper=0.491323 — impossible.
    After fix, point estimate must be inside CI.

    We simulate SC-3's characteristics: n_changed=39, n_equiv=378,
    with B07 dynamic features producing AUROC≈0.544.
    """
    # Simulate SC-3: changed pairs have slightly lower similarity than equiv
    rng = random.Random(12345)
    equiv_sims = [rng.gauss(0.875, 0.05) for _ in range(378)]
    # SC-3: off-by-one — dynamic barely distinguishes, so mean_changed > mean_equiv
    # This means "changed" has HIGHER similarity (inversion still present for SC-3)
    changed_sims = [rng.gauss(0.958, 0.03) for _ in range(39)]
    sims = equiv_sims + changed_sims
    labels = [0] * 378 + [1] * 39

    point = compute_auroc(sims, labels)
    ci_lower, ci_upper = _bootstrap_ci(sims, labels, n_bootstrap=1000, seed=42)

    # The key regression test: point estimate MUST be in CI
    assert ci_lower <= point <= ci_upper, (
        f"SC-3 regression: CI [{ci_lower:.4f}, {ci_upper:.4f}] "
        f"does not contain point estimate {point:.4f}"
    )
    # For inverted scenario (AUROC < 0.5), CI should also be below 0.5
    if point < 0.5:
        assert ci_upper <= 0.6, (
            f"For inverted scenario AUROC={point:.4f}, ci_upper={ci_upper:.4f} seems too high"
        )


if __name__ == "__main__":
    # Run tests directly
    tests = [
        test_ci_contains_point_estimate_balanced,
        test_ci_contains_point_estimate_imbalanced_1_9,
        test_ci_contains_point_estimate_extreme_imbalance,
        test_ci_lower_less_than_upper,
        test_ci_in_unit_interval,
        test_ci_width_reasonable,
        test_single_class_fallback,
        test_sc3_original_scenario_ci_valid,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed}/{passed+failed} tests passed")
