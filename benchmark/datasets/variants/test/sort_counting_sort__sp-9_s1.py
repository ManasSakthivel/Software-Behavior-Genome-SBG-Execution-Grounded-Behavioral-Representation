"""
Counting sort with support for arbitrary integer ranges.

Spec: Given a list of integers all within [min_val, max_val], return a new
list sorted in ascending order using counting sort. The range is either
inferred automatically or specified explicitly. Time O(n + k) where k is
the range size. Returns a new list; does not mutate input. Stable.
Raises ValueError if any element is outside the specified range, or if the
list is non-integer. Also provides a frequency map as a secondary output.
"""
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
    if not arr:
        return []
    lo = min_val if min_val is not None else min(arr)
    hi = max_val if max_val is not None else max(arr)
    for x in arr:
        if not isinstance(x, int):
            raise ValueError(f'counting_sort: non-integer element {x!r}')
        if x < lo or x > hi:
            raise ValueError(f'counting_sort: element {x} outside range [{lo}, {hi}]')
    counts = [0] * (hi - lo + 1)
    for x in arr:
        counts[x - lo] += 1
    result = []
    for (offset, count) in enumerate(counts):
        result.extend([lo + offset] * count)
    return result

def counting_sort_with_freq(arr: List[int]) -> Tuple[List[int], dict]:
    """Return (sorted_list, frequency_dict)."""
    sorted_arr = counting_sort(arr)
    freq = {}
    for x in arr:
        freq[x] = freq.get(x, 0) + 1
    return (sorted_arr, freq)

def test_counting_sort():
    assert counting_sort([4, 2, 2, 8, 3, 3, 1]) == [1, 2, 2, 3, 3, 4, 8]
    assert counting_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
    assert counting_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    assert counting_sort([]) == []
    assert counting_sort([7]) == [7]
    assert counting_sort([-3, -1, -2, 0, 2]) == [-3, -2, -1, 0, 2]
    try:
        counting_sort([1, 5, 10], min_val=1, max_val=8)
        assert False, 'Should have raised ValueError'
    except ValueError:
        pass
    (sorted_arr, freq) = counting_sort_with_freq([3, 1, 2, 1, 3])
    assert sorted_arr == [1, 1, 2, 3, 3]
    assert freq == {3: 2, 1: 2, 2: 1}
    try:
        counting_sort([1, 'a', 3])
        assert False
    except ValueError:
        pass
    original = [3, 1, 2]
    counting_sort(original)
    assert original == [3, 1, 2]
    print('All counting_sort tests passed.')
if __name__ == '__main__':
    test_counting_sort()
    data = [4, 2, 2, 8, 3, 3, 1]
    print(f'counting_sort({data}) = {counting_sort(data)}')
    (sorted_arr, freq) = counting_sort_with_freq(data)
    print(f'freq = {freq}')