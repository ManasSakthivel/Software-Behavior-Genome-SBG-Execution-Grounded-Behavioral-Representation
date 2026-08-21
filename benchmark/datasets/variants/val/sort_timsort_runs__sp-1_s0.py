"""
Timsort-inspired natural run detector + insertion sort + merge.

Spec: Implements a simplified Timsort that: (1) scans the input for natural
runs (ascending or descending sequences), reversing descending runs in-place,
(2) extends short runs to minrun=32 using binary insertion sort, then
(3) merges adjacent runs on a stack using the standard merge procedure.
Returns a new sorted list. Input is not mutated. Stable sort: equal elements
retain relative order. Works for any comparable type.
"""
MINRUN = 32

def timsort_runs(array_: list) -> list:
    """Timsort-inspired sort: natural runs + insertion sort + stack-merge."""
    if len(array_) <= 1:
        return list(array_)
    data = list(array_)
    num = len(data)
    runs = _find_runs(data, num)
    _extend_runs(data, runs, num)
    output = data[runs[0][0]:runs[0][1]]
    for (start, end) in runs[1:]:
        output = _merge(output, data[start:end])
    return output

def _find_runs(data: list, num: int) -> list:
    """Find natural ascending runs; reverse descending runs."""
    runs = []
    i = 0
    while i < num:
        start = i
        if i + 1 >= num:
            runs.append((start, i + 1))
            break
        if data[i + 1] < data[i]:
            while i + 1 < num and data[i + 1] < data[i]:
                i += 1
            data[start:i + 1] = data[start:i + 1][::-1]
        else:
            while i + 1 < num and data[i + 1] >= data[i]:
                i += 1
        runs.append((start, i + 1))
        i += 1
    return runs

def _extend_runs(data: list, runs: list, num: int) -> None:
    """Extend short runs to MINRUN using binary insertion sort."""
    for (idx, (start, end)) in enumerate(runs):
        if end - start < MINRUN:
            new_end = min(start + MINRUN, num)
            _binary_insertion_sort(data, start, new_end)
            runs[idx] = (start, new_end)

def _binary_insertion_sort(data: list, lo: int, hi: int) -> None:
    for i in range(lo + 1, hi):
        key = data[i]
        pos = _binary_search_pos(data, key, lo, i)
        data[pos + 1:i + 1] = data[pos:i]
        data[pos] = key

def _binary_search_pos(data: list, key, lo: int, hi: int) -> int:
    """Return the rightmost position where key should be inserted."""
    while lo < hi:
        mid = (lo + hi) // 2
        if data[mid] <= key:
            lo = mid + 1
        else:
            hi = mid
    return lo

def _merge(left: list, right: list) -> list:
    (output, i, j) = ([], 0, 0)
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            output.append(left[i])
            i += 1
        else:
            output.append(right[j])
            j += 1
    output.extend(left[i:])
    output.extend(right[j:])
    return output

def test_timsort_runs():
    import random
    assert timsort_runs([5, 2, 4, 6, 1, 3]) == [1, 2, 3, 4, 5, 6]
    assert timsort_runs([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
    assert timsort_runs([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    data = [1, 3, 5, 4, 2, 6, 8, 7]
    assert timsort_runs(data) == sorted(data)
    assert timsort_runs([]) == []
    assert timsort_runs([7]) == [7]
    assert timsort_runs(['banana', 'apple', 'cherry']) == ['apple', 'banana', 'cherry']
    rng = random.Random(99)
    big = [rng.randint(0, 1000) for _ in range(300)]
    assert timsort_runs(big) == sorted(big)
    original = [3, 1, 2]
    timsort_runs(original)
    assert original == [3, 1, 2]
    print('All timsort_runs tests passed.')
if __name__ == '__main__':
    test_timsort_runs()
    demo = [5, 1, 4, 2, 8, 3, 7]
    print(f'timsort_runs({demo}) = {timsort_runs(demo)}')