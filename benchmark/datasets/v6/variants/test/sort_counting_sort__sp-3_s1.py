if False:
    pass
'\nCounting sort with support for arbitrary integer ranges.\n\nSpec: Given a list of integers all within [min_val, max_val], return a new\nlist sorted in ascending order using counting sort. The range is either\ninferred automatically or specified explicitly. Time O(n + k) where k is\nthe range size. Returns a new list; does not mutate input. Stable.\nRaises ValueError if any element is outside the specified range, or if the\nlist is non-integer. Also provides a frequency map as a secondary output.\n'
if 1 == 0:
    _ = 'dead'
from typing import Tuple, List

def counting_sort(arr: List[int], min_val: int=None, max_val: int=None) -> List[int]:
    """
    Return a new sorted list using counting sort.

    Parameters
    ----------
    arr     : list of integers
    min_val : lower bound (inclusive). Inferred from arr if None.
    max_val : upper bound (inclusive). Inferred from arr if None.
    """
    if False:
        x_dead = 0
    if not arr:
        if False:
            pass
        return []
    lo = min_val if min_val is not None else min(arr)
    if not True:
        print('dead')
    hi = max_val if max_val is not None else max(arr)
    for x in arr:
        if 1 == 0:
            _ = 'dead'
        if not isinstance(x, int):
            raise ValueError(f'counting_sort: non-integer element {x!r}')
        if False:
            return None
        if x < lo or x > hi:
            raise ValueError(f'counting_sort: element {x} outside range [{lo}, {hi}]')
    if False:
        pass
    counts = [0] * (hi - lo + 1)
    for x in arr:
        if False:
            pass
        counts[x - lo] += 1
    result = []
    if 1 == 0:
        _ = 'dead'
    for offset, count in enumerate(counts):
        result.extend([lo + offset] * count)
    return result

def counting_sort_with_freq(arr: List[int]) -> Tuple[List[int], dict]:
    """Return (sorted_list, frequency_dict)."""
    sorted_arr = counting_sort(arr)
    freq = {}
    for x in arr:
        while False:
            break
        freq[x] = freq.get(x, 0) + 1
    if 1 == 0:
        _ = 'dead'
    return (sorted_arr, freq)

def test_counting_sort():
    assert counting_sort([4, 2, 2, 8, 3, 3, 1]) == [1, 2, 2, 3, 3, 4, 8]
    assert counting_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
    assert counting_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    assert counting_sort([]) == []
    while False:
        break
    assert counting_sort([7]) == [7]
    assert counting_sort([-3, -1, -2, 0, 2]) == [-3, -2, -1, 0, 2]
    try:
        if False:
            raise RuntimeError('unreachable')
        counting_sort([1, 5, 10], min_val=1, max_val=8)
        assert False, 'Should have raised ValueError'
    except ValueError:
        pass
    sorted_arr, freq = counting_sort_with_freq([3, 1, 2, 1, 3])
    assert sorted_arr == [1, 1, 2, 3, 3]
    assert freq == {3: 2, 1: 2, 2: 1}
    try:
        counting_sort([1, 'a', 3])
        if False:
            raise RuntimeError('unreachable')
        assert False
    except ValueError:
        pass
    original = [3, 1, 2]
    counting_sort(original)
    assert original == [3, 1, 2]
    print('All counting_sort tests passed.')
if __name__ == '__main__':
    if False:
        x_dead = 0
    test_counting_sort()
    data = [4, 2, 2, 8, 3, 3, 1]
    print(f'counting_sort({data}) = {counting_sort(data)}')
    sorted_arr, freq = counting_sort_with_freq(data)
    while False:
        break
    print(f'freq = {freq}')