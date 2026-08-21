# program_id: math_statistics
# category: mathematical_numerical
# spec_version: 1.0

"""
Descriptive statistics: mean, median, mode, variance, std dev, percentiles.

Spec: Given a non-empty list of numbers, compute standard descriptive stats.
  - mean(data) → float
  - median(data) → float  : middle value; average of two middles for even n
  - mode(data) → list     : all values appearing with maximum frequency
                             (sorted; raises StatError if data is empty)
  - variance(data, population=True) → float : population (÷n) or sample (÷n-1)
  - std_dev(data, population=True) → float
  - percentile(data, p) → float : p-th percentile (0 ≤ p ≤ 100) via linear
                                    interpolation (same as numpy's method 7)
  - summary(data) → dict  : all of the above in one call

All functions raise StatError (custom) if data is empty, or ValueError for
invalid parameters (p out of range, n=1 for sample variance).
"""
import math
from typing import List, Union
from collections import Counter


class StatError(Exception):
    """Raised when statistical computation is impossible (e.g., empty data)."""


Number = Union[int, float]


def _check_nonempty(data: list) -> None:
    if not data:
        raise StatError("data must be non-empty")


def mean(data: List[Number]) -> float:
    """Return arithmetic mean."""
    _check_nonempty(data)
    return sum(data) / len(data)


def median(data: List[Number]) -> float:
    """Return the median value."""
    _check_nonempty(data)
    s = sorted(data)
    n = len(s)
    if n % 2 == 1:
        return float(s[n // 2])
    return (s[n // 2 - 1] + s[n // 2]) / 2.0


def mode(data: List[Number]) -> List[Number]:
    """Return list of most frequent values (sorted). Raises StatError if empty."""
    _check_nonempty(data)
    counts = Counter(data)
    max_freq = max(counts.values())
    return sorted(k for k, v in counts.items() if v == max_freq)


def variance(data: List[Number], population: bool = True) -> float:
    """Return population (ddof=0) or sample (ddof=1) variance."""
    _check_nonempty(data)
    n = len(data)
    if not population and n < 2:
        raise ValueError("Sample variance requires at least 2 data points")
    mu = mean(data)
    sq_diffs = sum((x - mu) ** 2 for x in data)
    return sq_diffs / (n if population else n - 1)


def std_dev(data: List[Number], population: bool = True) -> float:
    """Return standard deviation (population or sample)."""
    return math.sqrt(variance(data, population=population))


def percentile(data: List[Number], p: float) -> float:
    """
    Return the p-th percentile using linear interpolation (numpy method 7).
    p must be in [0, 100].
    """
    _check_nonempty(data)
    if not (0 <= p <= 100):
        raise ValueError(f"Percentile p must be in [0, 100], got {p}")
    s = sorted(data)
    n = len(s)
    if n == 1:
        return float(s[0])
    idx = (p / 100) * (n - 1)
    lo = int(idx)
    hi = lo + 1
    if hi >= n:
        return float(s[-1])
    frac = idx - lo
    return s[lo] + frac * (s[hi] - s[lo])


def summary(data: List[Number]) -> dict:
    """Return a dict of all descriptive statistics."""
    _check_nonempty(data)
    return {
        "n":        len(data),
        "mean":     mean(data),
        "median":   median(data),
        "mode":     mode(data),
        "min":      min(data),
        "max":      max(data),
        "range":    max(data) - min(data),
        "variance": variance(data, population=True),
        "std_dev":  std_dev(data, population=True),
        "p25":      percentile(data, 25),
        "p75":      percentile(data, 75),
        "iqr":      percentile(data, 75) - percentile(data, 25),
    }


# ---------- tests ----------

def test_statistics():
    data = [2, 3, 4, 4, 5, 5, 7, 9]

    # Test 1: mean
    assert abs(mean(data) - 5.0) < 1e-9

    # Test 2: median (even n=8, middle = 4 and 5 → 4.5)
    assert median(data) == 4.5

    # Test 3: mode
    assert mode(data) == [4]

    # Test 4: population variance = 4.0 (well-known example)
    assert abs(variance(data, population=True) - 4.0) < 1e-9

    # Test 5: sample variance
    assert abs(variance(data, population=False) - 4.571428) < 1e-5

    # Test 6: std_dev
    assert abs(std_dev(data, population=True) - 2.0) < 1e-9

    # Test 7: percentile (Q1, Q3)
    assert abs(percentile(data, 0) - 2.0) < 1e-9
    assert abs(percentile(data, 100) - 9.0) < 1e-9

    # Test 8: multimodal
    assert mode([1, 1, 2, 2, 3]) == [1, 2]

    # Test 9: empty raises StatError
    for fn in [mean, median, mode, lambda d: variance(d), lambda d: std_dev(d)]:
        try:
            fn([])
            assert False
        except StatError:
            pass

    # Test 10: sample variance with n=1 raises ValueError
    try:
        variance([5], population=False)
        assert False
    except ValueError:
        pass

    # Test 11: percentile p out of range
    try:
        percentile(data, 101)
        assert False
    except ValueError:
        pass

    # Test 12: summary dict has expected keys
    s = summary(data)
    assert all(k in s for k in ["mean", "median", "mode", "variance", "std_dev", "iqr"])

    print("All statistics tests passed.")


if __name__ == "__main__":
    test_statistics()
    data = [2, 4, 4, 4, 5, 5, 7, 9]
    s = summary(data)
    for k, v in s.items():
        print(f"  {k:12s}: {v}")
