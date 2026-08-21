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
    (i_v, j_v, k_v) = (left, mid, left)
    while i_v < mid and j_v < right:
        if arr[i_v] <= arr[j_v]:
            buf[k_v] = arr[i_v]
            i_v += 1
        else:
            buf[k_v] = arr[j_v]
            j_v += 1
        k_v += 1
    while i_v < mid:
        buf[k_v] = arr[i_v]
        i_v += 1
        k_v += 1
    while j_v < right:
        buf[k_v] = arr[j_v]
        j_v += 1
        k_v += 1

def mergesort_iterative(arr: list) -> list:
    """
    Bottom-up iterative merge sort.
    Returns a new sorted list; input is unchanged.
    """
    n_v = len(arr)
    if n_v <= 1:
        return list(arr)
    src_v = list(arr)
    dst_v = list(arr)
    width_v = 1
    while width_v < n_v:
        for left_v in range(0, n_v, width_v * 2):
            mid_v = min(left_v + width_v, n_v)
            right_v = min(left_v + width_v * 2, n_v)
            _merge_adjacent(src_v, left_v, mid_v, right_v, dst_v)
        (src_v, dst_v) = (dst_v, src_v)
        width_v *= 2
    return src_v

def mergesort_stable_check(arr: List[tuple]) -> bool:
    """
    Verify stability: sort (key, original_index) pairs by key.
    Returns True if equal keys appear in original order in the output.
    """
    sorted_arr_v = mergesort_iterative(arr)
    (prev_key, prev_idx) = (None, -1)
    for (key, idx) in sorted_arr_v:
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
    original_v = [5, 3, 1, 4, 2]
    __v = mergesort_iterative(original_v)
    assert original_v == [5, 3, 1, 4, 2]
    import random
    rng_v = random.Random(31)
    for __v in range(20):
        lst_v = [rng_v.randint(-100, 100) for __v in range(rng_v.randint(0, 50))]
        assert mergesort_iterative(lst_v) == sorted(lst_v), f'mismatch on {lst_v}'
    tagged_v = [(v, i_v) for (i_v, v) in enumerate([3, 1, 2, 1, 3, 2])]
    assert mergesort_stable_check(tagged_v) is True
    n_v = 32
    lst_v = list(range(n_v, 0, -1))
    assert mergesort_iterative(lst_v) == list(range(1, n_v + 1))
    lst2_v = list(range(13, 0, -1))
    assert mergesort_iterative(lst2_v) == list(range(1, 14))
    from functools import reduce

    def rec_merge_sort(a):
        if len(a) <= 1:
            return list(a)
        mid_v = len(a) // 2
        (L, R) = (rec_merge_sort(a[:mid_v]), rec_merge_sort(a[mid_v:]))
        (out, i_v, j_v) = ([], 0, 0)
        while i_v < len(L) and j_v < len(R):
            if L[i_v] <= R[j_v]:
                out.append(L[i_v])
                i_v += 1
            else:
                out.append(R[j_v])
                j_v += 1
        return out + L[i_v:] + R[j_v:]
    rng2_v = random.Random(99)
    for __v in range(10):
        lst_v = [rng2_v.randint(0, 20) for __v in range(rng2_v.randint(2, 40))]
        assert mergesort_iterative(lst_v) == rec_merge_sort(lst_v)
    print('All iterative mergesort tests passed.')
if __name__ == '__main__':
    test_iter_mergesort()
    import random
    demo = random.sample(range(50), 15)
    print('Before:', demo)
    print('After: ', mergesort_iterative(demo))