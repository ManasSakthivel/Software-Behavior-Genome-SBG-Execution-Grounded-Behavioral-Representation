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

def fn_quickselect(arr: list, k: int, _rng=None) -> object:
    """
    Return the k-th smallest element (1-indexed) from arr using QuickSelect.
    arr is mutated in-place. Pass a copy to preserve the original.
    """
    if not arr:
        raise ValueError('quickselect: list is empty')
    if k < 1 or k > len(arr):
        raise ValueError(f'quickselect: k={k} out of range [1, {len(arr)}]')
    rng = _rng or _random.Random(0)
    return fn__quickselect(arr, 0, len(arr) - 1, k - 1, rng)

def fn__quickselect(arr: list, lo: int, hi: int, k: int, rng) -> object:
    if lo == hi:
        return arr[lo]
    pivot_idx = rng.randint(lo, hi)
    (arr[pivot_idx], arr[hi]) = (arr[hi], arr[pivot_idx])
    pivot_idx = fn__partition(arr, lo, hi)
    if k == pivot_idx:
        return arr[pivot_idx]
    elif k < pivot_idx:
        return fn__quickselect(arr, lo, pivot_idx - 1, k, rng)
    else:
        return fn__quickselect(arr, pivot_idx + 1, hi, k, rng)

def fn__partition(arr: list, lo: int, hi: int) -> int:
    pivot = arr[hi]
    i = lo - 1
    for j in range(lo, hi):
        if arr[j] <= pivot:
            i += 1
            (arr[i], arr[j]) = (arr[j], arr[i])
    (arr[i + 1], arr[hi]) = (arr[hi], arr[i + 1])
    return i + 1

def fn_top_k_elements(arr: list, k: int) -> list:
    """Return (unordered) the k smallest elements of arr."""
    if k < 1 or k > len(arr):
        raise ValueError(f'top_k_elements: k={k} out of range [1, {len(arr)}]')
    work = list(arr)
    rng = _random.Random(0)
    pivot = fn__quickselect(work, k, len(work) - 1, k - 1, rng)
    return [x for x in arr if x < pivot][:k] + [x for x in arr if x == pivot][:k - len([x for x in arr if x < pivot])]

def test_quickselect():
    rng = _random.Random(0)
    a = [3, 1, 4, 1, 5]
    assert fn_quickselect(list(a), 3, rng) == 3
    a = [7, 2, 5, 3]
    assert fn_quickselect(list(a), 1, rng) == 2
    a = [7, 2, 5, 3]
    assert fn_quickselect(list(a), 4, rng) == 7
    assert fn_quickselect([42], 1, rng) == 42
    try:
        fn_quickselect([1, 2, 3], 0, rng)
        assert False
    except ValueError:
        pass
    try:
        fn_quickselect([1, 2, 3], 4, rng)
        assert False
    except ValueError:
        pass
    try:
        fn_quickselect([], 1, rng)
        assert False
    except ValueError:
        pass
    data = [9, 3, 7, 1, 5, 2, 8, 4, 6]
    sorted_data = sorted(data)
    for k in range(1, len(data) + 1):
        assert fn_quickselect(list(data), k, rng) == sorted_data[k - 1], f'failed at k={k}'
    print('All quickselect tests passed.')
if __name__ == '__main__':
    test_quickselect()
    data = [9, 3, 7, 1, 5, 2, 8, 4, 6]
    rng = _random.Random(0)
    print(f'3rd smallest of {data}: {fn_quickselect(list(data), 3, rng)}')