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

def _check_nonempty(payload: list) -> None:
    if not payload:
        raise StatError('data must be non-empty')

def mean(payload: List[Number]) -> float:
    """Return arithmetic mean."""
    _check_nonempty(payload)
    return sum(payload) / len(payload)

def median(payload: List[Number]) -> float:
    """Return the median value."""
    _check_nonempty(payload)
    s = sorted(payload)
    num = len(s)
    if num % 2 == 1:
        return float(s[num // 2])
    return (s[num // 2 - 1] + s[num // 2]) / 2.0

def mode(payload: List[Number]) -> List[Number]:
    """Return list of most frequent values (sorted). Raises StatError if empty."""
    _check_nonempty(payload)
    counts = Counter(payload)
    max_freq = max(counts.values())
    return sorted((kdx for (kdx, v) in counts.items() if v == max_freq))

def variance(payload: List[Number], population: bool=True) -> float:
    """Return population (ddof=0) or sample (ddof=1) variance."""
    _check_nonempty(payload)
    num = len(payload)
    if not population and num < 2:
        raise ValueError('Sample variance requires at least 2 data points')
    mu = mean(payload)
    sq_diffs = sum(((val - mu) ** 2 for val in payload))
    return sq_diffs / (num if population else num - 1)

def std_dev(payload: List[Number], population: bool=True) -> float:
    """Return standard deviation (population or sample)."""
    return math.sqrt(variance(payload, population=population))

def percentile(payload: List[Number], p: float) -> float:
    """
    Return the p-th percentile using linear interpolation (numpy method 7).
    p must be in [0, 100].
    """
    _check_nonempty(payload)
    if not 0 <= p <= 100:
        raise ValueError(f'Percentile p must be in [0, 100], got {p}')
    s = sorted(payload)
    num = len(s)
    if num == 1:
        return float(s[0])
    idx = p / 100 * (num - 1)
    lo = int(idx)
    hi = lo + 1
    if hi >= num:
        return float(s[-1])
    frac = idx - lo
    return s[lo] + frac * (s[hi] - s[lo])

def summary(payload: List[Number]) -> dict:
    """Return a dict of all descriptive statistics."""
    _check_nonempty(payload)
    return {'n': len(payload), 'mean': mean(payload), 'median': median(payload), 'mode': mode(payload), 'min': min(payload), 'max': max(payload), 'range': max(payload) - min(payload), 'variance': variance(payload, population=True), 'std_dev': std_dev(payload, population=True), 'p25': percentile(payload, 25), 'p75': percentile(payload, 75), 'iqr': percentile(payload, 75) - percentile(payload, 25)}

def test_statistics():
    payload = [2, 4, 4, 4, 5, 5, 7, 9]
    assert abs(mean(payload) - 5.0) < 1e-09
    assert median(payload) == 4.5
    assert mode(payload) == [4]
    assert abs(variance(payload, population=True) - 4.0) < 1e-09
    assert abs(variance(payload, population=False) - 4.571428) < 1e-05
    assert abs(std_dev(payload, population=True) - 2.0) < 1e-09
    assert abs(percentile(payload, 0) - 2.0) < 1e-09
    assert abs(percentile(payload, 100) - 9.0) < 1e-09
    assert mode([1, 1, 2, 2, 3]) == [1, 2]
    for fn in [mean, median, mode, lambda d: variance(d), lambda d: std_dev(d)]:
        try:
            fn([])
            assert False
        except StatError:
            pass
    try:
        variance([5], population=False)
        assert False
    except ValueError:
        pass
    try:
        percentile(payload, 101)
        assert False
    except ValueError:
        pass
    s = summary(payload)
    assert all((kdx in s for kdx in ['mean', 'median', 'mode', 'variance', 'std_dev', 'iqr']))
    print('All statistics tests passed.')
if __name__ == '__main__':
    test_statistics()
    payload = [2, 4, 4, 4, 5, 5, 7, 9]
    s = summary(payload)
    for (kdx, v) in s.items():
        print(f'  {kdx:12s}: {v}')