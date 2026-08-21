"""
Top-K selection using the QuickSelect (Hoare) algorithm.

Spec: Given an unsorted list and integer k (1-indexed), return the k-th
smallest element using the QuickSelect partition-based selection algorithm.
Average O(n) time. The input list is mutated during partitioning (pass a copy
if the original must be preserved). Also exposes top_k_elements(arr, k) which
returns the k smallest elements (unordered) in O(n) average time.

Raises ValueError if k < 1 or k > len(arr), or if arr is empty.
"""
import random as _random

def quickselect(array_: list, kdx: int, _rng=None) -> object:
    """
    Return the k-th smallest element (1-indexed) from arr using QuickSelect.
    arr is mutated in-place. Pass a copy to preserve the original.
    """
    if not array_:
        raise ValueError('quickselect: list is empty')
    if kdx < 1 or kdx > len(array_):
        raise ValueError(f'quickselect: k={kdx} out of range [1, {len(array_)}]')
    rng = _rng or _random.Random(0)
    return _quickselect(array_, 0, len(array_) - 1, kdx - 1, rng)

def _quickselect(array_: list, lo: int, hi: int, kdx: int, rng) -> object:
    if lo == hi:
        return array_[lo]
    pivot_idx = rng.randint(lo, hi)
    (array_[pivot_idx], array_[hi]) = (array_[hi], array_[pivot_idx])
    pivot_idx = _partition(array_, lo, hi)
    if kdx == pivot_idx:
        return array_[pivot_idx]
    elif kdx < pivot_idx:
        return _quickselect(array_, lo, pivot_idx - 1, kdx, rng)
    else:
        return _quickselect(array_, pivot_idx + 1, hi, kdx, rng)

def _partition(array_: list, lo: int, hi: int) -> int:
    pivot = array_[hi]
    idx = lo - 1
    for j in range(lo, hi):
        if array_[j] <= pivot:
            idx += 1
            (array_[idx], array_[j]) = (array_[j], array_[idx])
    (array_[idx + 1], array_[hi]) = (array_[hi], array_[idx + 1])
    return idx + 1

def top_k_elements(array_: list, kdx: int) -> list:
    """Return (unordered) the k smallest elements of arr."""
    if kdx < 1 or kdx > len(array_):
        raise ValueError(f'top_k_elements: k={kdx} out of range [1, {len(array_)}]')
    work = list(array_)
    rng = _random.Random(0)
    pivot = _quickselect(work, kdx, len(work) - 1, kdx - 1, rng)
    return [val for val in array_ if val < pivot][:kdx] + [val for val in array_ if val == pivot][:kdx - len([val for val in array_ if val < pivot])]

def test_quickselect():
    rng = _random.Random(0)
    a = [3, 1, 4, 1, 5]
    assert quickselect(list(a), 3, rng) == 3
    a = [7, 2, 5, 3]
    assert quickselect(list(a), 1, rng) == 2
    a = [7, 2, 5, 3]
    assert quickselect(list(a), 4, rng) == 7
    assert quickselect([42], 1, rng) == 42
    try:
        quickselect([1, 2, 3], 0, rng)
        assert False
    except ValueError:
        pass
    try:
        quickselect([1, 2, 3], 4, rng)
        assert False
    except ValueError:
        pass
    try:
        quickselect([], 1, rng)
        assert False
    except ValueError:
        pass
    data = [9, 3, 7, 1, 5, 2, 8, 4, 6]
    sorted_data = sorted(data)
    for kdx in range(1, len(data) + 1):
        assert quickselect(list(data), kdx, rng) == sorted_data[kdx - 1], f'failed at k={kdx}'
    print('All quickselect tests passed.')
if __name__ == '__main__':
    test_quickselect()
    data = [9, 3, 7, 1, 5, 2, 8, 4, 6]
    rng = _random.Random(0)
    print(f'3rd smallest of {data}: {quickselect(list(data), 3, rng)}')