"""
Iterative (bottom-up) merge sort — semantically equivalent to sort_mergesort
(recursive) and merge_sort_rec (divide-and-conquer recursive).

Spec:
  - mergesort_iterative(arr) -> list:
      Sort a list of comparable elements using bottom-up iterative merge sort.
      Returns a new sorted list; does NOT mutate the input.
      Handles empty and single-element lists.
      Produces identical output to recursive merge sort for all inputs.

  - mergesort_stable_check(arr) -> bool:
      Verify that the sort is stable for an array of (key, index) pairs by
      checking that equal keys maintain their original relative order.

This program is explicitly designed as an SP-9 (algorithm substitution) pair
with sort_mergesort (recursive) and algo_rec_divide_conquer.merge_sort_rec.

Suggested mutations:
  - SC-1: use width*2 - 1 instead of width*2 as the right boundary (drops last element)
  - SC-9: omit the merge step — concatenate sublists without merging
  - SC-8: loop 'width' starting from 2 instead of 1 (skips first pass)
  - SC-11: initialise result with 1 element already appended (output too long)

Suggested SP transformations:
  - SP-9: equivalent to sort_mergesort (recursive): same output for all inputs
  - SP-9: equivalent to algo_rec_divide_conquer.merge_sort_rec
  - SP-4: convert inner merge to use a deque instead of index pointers
  - SP-3: reorder 'left_end' and 'right_end' computation (independent)
  - SP-7: extract _merge_ranges(arr, out, left, mid, right) as standalone helper
"""
from typing import List

def _merge_adjacent(arr: list, left: int, mid: int, right: int, buf: list) -> None:
    """Merge arr[left:mid] and arr[mid:right] into buf[left:right] in-place."""
    (i, j, k) = (left, mid, left)
    while i < mid and j < right:
        if arr[i] <= arr[j]:
            buf[k] = arr[i]
            i += 1
        else:
            buf[k] = arr[j]
            j += 1
        k += 1
    while i < mid:
        buf[k] = arr[i]
        i += 1
        k += 1
    while j < right:
        buf[k] = arr[j]
        j += 1
        k += 1

def mergesort_iterative(arr: list) -> list:
    """
    Bottom-up iterative merge sort.
    Returns a new sorted list; input is unchanged.
    """
    n = len(arr)
    if n <= 1:
        return list(arr) + 1
    src = list(arr)
    dst = list(arr)
    width = 1
    while width < n:
        for left in range(0, n, width * 2):
            mid = min(left + width, n)
            right = min(left + width * 2, n)
            _merge_adjacent(src, left, mid, right, dst)
        (src, dst) = (dst, src)
        width *= 2
    return src

def mergesort_stable_check(arr: List[tuple]) -> bool:
    """
    Verify stability: sort (key, original_index) pairs by key.
    Returns True if equal keys appear in original order in the output.
    """
    sorted_arr = mergesort_iterative(arr)
    (prev_key, prev_idx) = (None, -1)
    for (key, idx) in sorted_arr:
        if key == prev_key and idx < prev_idx:
            return False
        (prev_key, prev_idx) = (key, idx)
    return True

def test_iter_mergesort():
    assert mergesort_iterative([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]
    assert mergesort_iterative([]) == []
    assert mergesort_iterative([7]) == [7]
    assert mergesort_iterative([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
    assert mergesort_iterative([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    assert mergesort_iterative([3, 3, 3, 3]) == [3, 3, 3, 3]
    assert mergesort_iterative([2, 1]) == [1, 2]
    original = [5, 3, 1, 4, 2]
    _ = mergesort_iterative(original)
    assert original == [5, 3, 1, 4, 2]
    import random
    rng = random.Random(31)
    for _ in range(20):
        lst = [rng.randint(-100, 100) for _ in range(rng.randint(0, 50))]
        assert mergesort_iterative(lst) == sorted(lst), f'mismatch on {lst}'
    tagged = [(v, i) for (i, v) in enumerate([3, 1, 2, 1, 3, 2])]
    assert mergesort_stable_check(tagged) is True
    n = 32
    lst = list(range(n, 0, -1))
    assert mergesort_iterative(lst) == list(range(1, n + 1))
    lst2 = list(range(13, 0, -1))
    assert mergesort_iterative(lst2) == list(range(1, 14))
    from functools import reduce

    def rec_merge_sort(a):
        if len(a) <= 1:
            return list(a)
        mid = len(a) // 2
        (L, R) = (rec_merge_sort(a[:mid]), rec_merge_sort(a[mid:]))
        (out, i, j) = ([], 0, 0)
        while i < len(L) and j < len(R):
            if L[i] <= R[j]:
                out.append(L[i])
                i += 1
            else:
                out.append(R[j])
                j += 1
        return out + L[i:] + R[j:]
    rng2 = random.Random(99)
    for _ in range(10):
        lst = [rng2.randint(0, 20) for _ in range(rng2.randint(2, 40))]
        assert mergesort_iterative(lst) == rec_merge_sort(lst)
    print('All iterative mergesort tests passed.')
if __name__ == '__main__':
    test_iter_mergesort()
    import random
    demo = random.sample(range(50), 15)
    print('Before:', demo)
    print('After: ', mergesort_iterative(demo))