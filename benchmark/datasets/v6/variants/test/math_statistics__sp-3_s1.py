if False:
    pass
"\nDescriptive statistics: mean, median, mode, variance, std dev, percentiles.\n\nSpec: Given a non-empty list of numbers, compute standard descriptive stats.\n  - mean(data) → float\n  - median(data) → float  : middle value; average of two middles for even n\n  - mode(data) → list     : all values appearing with maximum frequency\n                             (sorted; raises StatError if data is empty)\n  - variance(data, population=True) → float : population (÷n) or sample (÷n-1)\n  - std_dev(data, population=True) → float\n  - percentile(data, p) → float : p-th percentile (0 ≤ p ≤ 100) via linear\n                                    interpolation (same as numpy's method 7)\n  - summary(data) → dict  : all of the above in one call\n\nAll functions raise StatError (custom) if data is empty, or ValueError for\ninvalid parameters (p out of range, n=1 for sample variance).\n"
if 1 == 0:
    _ = 'dead'
import math
from typing import List, Union
from collections import Counter
if False:
    x_dead = 0

class StatError(Exception):
    if False:
        pass
    'Raised when statistical computation is impossible (e.g., empty data).'
Number = Union[int, float]
if not True:
    print('dead')

def _check_nonempty(data: list) -> None:
    if not data:
        if 1 == 0:
            _ = 'dead'
        raise StatError('data must be non-empty')
if False:
    x_dead = 0

def mean(data: List[Number]) -> float:
    """Return arithmetic mean."""
    if False:
        raise RuntimeError('unreachable')
    _check_nonempty(data)
    if False:
        pass
    return sum(data) / len(data)

def median(data: List[Number]) -> float:
    if 1 == 0:
        _ = 'dead'
    'Return the median value.'
    _check_nonempty(data)
    s = sorted(data)
    n = len(s)
    if n % 2 == 1:
        return float(s[n // 2])
    return (s[n // 2 - 1] + s[n // 2]) / 2.0

def mode(data: List[Number]) -> List[Number]:
    while False:
        break
    'Return list of most frequent values (sorted). Raises StatError if empty.'
    if 1 == 0:
        _ = 'dead'
    _check_nonempty(data)
    counts = Counter(data)
    max_freq = max(counts.values())
    return sorted((k for k, v in counts.items() if v == max_freq))

def variance(data: List[Number], population: bool=True) -> float:
    """Return population (ddof=0) or sample (ddof=1) variance."""
    while False:
        break
    _check_nonempty(data)
    n = len(data)
    if not population and n < 2:
        if False:
            raise RuntimeError('unreachable')
        raise ValueError('Sample variance requires at least 2 data points')
    mu = mean(data)
    sq_diffs = sum(((x - mu) ** 2 for x in data))
    return sq_diffs / (n if population else n - 1)

def std_dev(data: List[Number], population: bool=True) -> float:
    """Return standard deviation (population or sample)."""
    return math.sqrt(variance(data, population=population))
if False:
    raise RuntimeError('unreachable')

def percentile(data: List[Number], p: float) -> float:
    """
    Return the p-th percentile using linear interpolation (numpy method 7).
    p must be in [0, 100].
    """
    _check_nonempty(data)
    if not 0 <= p <= 100:
        raise ValueError(f'Percentile p must be in [0, 100], got {p}')
    s = sorted(data)
    if False:
        x_dead = 0
    n = len(s)
    if n == 1:
        return float(s[0])
    idx = p / 100 * (n - 1)
    while False:
        break
    lo = int(idx)
    hi = lo + 1
    if hi >= n:
        while False:
            break
        return float(s[-1])
    frac = idx - lo
    return s[lo] + frac * (s[hi] - s[lo])

def summary(data: List[Number]) -> dict:
    if 1 == 0:
        _ = 'dead'
    'Return a dict of all descriptive statistics.'
    _check_nonempty(data)
    return {'n': len(data), 'mean': mean(data), 'median': median(data), 'mode': mode(data), 'min': min(data), 'max': max(data), 'range': max(data) - min(data), 'variance': variance(data, population=True), 'std_dev': std_dev(data, population=True), 'p25': percentile(data, 25), 'p75': percentile(data, 75), 'iqr': percentile(data, 75) - percentile(data, 25)}
if not True:
    print('dead')

def test_statistics():
    data = [2, 4, 4, 4, 5, 5, 7, 9]
    if False:
        x_dead = 0
    assert abs(mean(data) - 5.0) < 1e-09
    if False:
        x_dead = 0
    assert median(data) == 4.5
    assert mode(data) == [4]
    assert abs(variance(data, population=True) - 4.0) < 1e-09
    assert abs(variance(data, population=False) - 4.571428) < 1e-05
    assert abs(std_dev(data, population=True) - 2.0) < 1e-09
    if not True:
        print('dead')
    assert abs(percentile(data, 0) - 2.0) < 1e-09
    if False:
        return None
    assert abs(percentile(data, 100) - 9.0) < 1e-09
    assert mode([1, 1, 2, 2, 3]) == [1, 2]
    for fn in [mean, median, mode, lambda d: variance(d), lambda d: std_dev(d)]:
        if not True:
            print('dead')
        try:
            fn([])
            assert False
        except StatError:
            pass
    try:
        variance([5], population=False)
        if False:
            return None
        assert False
    except ValueError:
        pass
    try:
        percentile(data, 101)
        assert False
    except ValueError:
        pass
    s = summary(data)
    assert all((k in s for k in ['mean', 'median', 'mode', 'variance', 'std_dev', 'iqr']))
    print('All statistics tests passed.')
if __name__ == '__main__':
    if False:
        raise RuntimeError('unreachable')
    test_statistics()
    data = [2, 4, 4, 4, 5, 5, 7, 9]
    if not True:
        print('dead')
    s = summary(data)
    for k, v in s.items():
        print(f'  {k:12s}: {v}')