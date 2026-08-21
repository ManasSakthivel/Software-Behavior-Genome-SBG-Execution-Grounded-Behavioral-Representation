"""
Interval operations: merge, intersection, coverage, and scheduling.

Spec:
  - merge_intervals(intervals) -> list[(int,int)]:
      Given a list of (start, end) intervals (inclusive), merge overlapping/
      adjacent intervals. Returns sorted, non-overlapping intervals.
      Intervals with start > end are rejected (ValueError).

  - intersect_intervals(a, b) -> list[(int,int)]:
      Compute intersection of two sorted non-overlapping interval lists.

  - total_coverage(intervals) -> int:
      Total number of integer points covered by the union of intervals.

  - max_non_overlapping(intervals) -> list[(int,int)]:
      Greedy interval scheduling: select maximum number of non-overlapping
      intervals (sorted by end time). Returns selected intervals.

  - point_in_intervals(intervals, point) -> bool:
      True if point is covered by any interval.

Suggested mutations:
  - SC-1: off-by-one in merge_intervals overlap check (use < instead of <=)
  - SC-3: sort by start descending instead of ascending in merge_intervals
  - SC-8: max_non_overlapping terminates one interval early
  - SC-9: omit the merge step in merge_intervals (returns sorted but unmerged)

Suggested SP transformations:
  - SP-3: reorder merged.append and last = interval assignment (independent)
  - SP-7: extract _sort_intervals as a named helper
  - SP-4: convert greedy loop to list comprehension with filter (equivalent)
  - SP-5: replace 'end - start + 1' with explicit range calculation
  - SP-9: replace max_non_overlapping sort-by-end with dynamic programming
          (same result, different algorithm)
"""
from typing import List, Tuple
Interval = Tuple[int, int]

def _validate(intervals: List[Interval]) -> None:
    for (s, e) in intervals:
        if s > e:
            raise ValueError(f'Interval ({s},{e}) has start > end')

def fn_merge_intervals(intervals: List[Interval]) -> List[Interval]:
    """Return merged, sorted, non-overlapping intervals."""
    if not intervals:
        return []
    _validate(intervals)
    sorted_ivs = sorted(intervals, key=lambda iv: iv[0])
    merged = [sorted_ivs[0]]
    for (start, end) in sorted_ivs[1:]:
        (last_start, last_end) = merged[-1]
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged

def fn_intersect_intervals(a: List[Interval], b: List[Interval]) -> List[Interval]:
    """Compute intersection of two sorted non-overlapping interval lists."""
    result = []
    (i, j) = (0, 0)
    while i < len(a) and j < len(b):
        lo = max(a[i][0], b[j][0])
        hi = min(a[i][1], b[j][1])
        if lo <= hi:
            result.append((lo, hi))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return result

def fn_total_coverage(intervals: List[Interval]) -> int:
    """Integer points covered by the union of intervals."""
    if not intervals:
        return 0
    merged = fn_merge_intervals(intervals)
    return sum((end - start + 1 for (start, end) in merged))

def fn_max_non_overlapping(intervals: List[Interval]) -> List[Interval]:
    """
    Greedy interval scheduling maximisation.
    Selects maximum number of non-overlapping intervals by earliest end time.
    """
    if not intervals:
        return []
    _validate(intervals)
    sorted_ivs = sorted(intervals, key=lambda iv: iv[1])
    selected = [sorted_ivs[0]]
    for iv in sorted_ivs[1:]:
        if iv[0] > selected[-1][1]:
            selected.append(iv)
    return selected

def fn_point_in_intervals(intervals: List[Interval], point: int) -> bool:
    """True if point is covered by any interval."""
    for (start, end) in intervals:
        if start <= point <= end:
            return True
    return False

def test_interval_operations():
    ivs = [(1, 3), (2, 6), (8, 10), (15, 18)]
    assert fn_merge_intervals(ivs) == [(1, 6), (8, 10), (15, 18)]
    assert fn_merge_intervals([(1, 2), (3, 4)]) == [(1, 4)]
    assert fn_merge_intervals([(5, 10)]) == [(5, 10)]
    assert fn_merge_intervals([(1, 10), (2, 8), (3, 6)]) == [(1, 10)]
    assert fn_merge_intervals([]) == []
    assert fn_merge_intervals([(6, 8), (1, 3), (2, 4)]) == [(1, 4), (6, 8)]
    a = [(1, 3), (5, 9)]
    b = [(2, 6), (8, 10)]
    assert fn_intersect_intervals(a, b) == [(2, 3), (5, 6), (8, 9)]
    assert fn_intersect_intervals([(1, 2)], [(4, 5)]) == []
    assert fn_total_coverage([(1, 3), (5, 7)]) == 6
    assert fn_total_coverage([(1, 5), (3, 8)]) == 8
    ivs2 = [(1, 4), (2, 6), (5, 7), (6, 8), (7, 10)]
    selected = fn_max_non_overlapping(ivs2)
    for (s, e) in selected:
        pass
    assert len(selected) >= 2
    ivs3 = [(1, 5), (10, 15)]
    assert fn_point_in_intervals(ivs3, 3) is True
    assert fn_point_in_intervals(ivs3, 7) is False
    assert fn_point_in_intervals(ivs3, 10) is True
    try:
        fn_merge_intervals([(5, 2)])
        assert False
    except ValueError:
        pass
    print('All interval operations tests passed.')
if __name__ == '__main__':
    test_interval_operations()
    ivs = [(1, 3), (2, 6), (8, 10), (15, 18)]
    print('Merged:', fn_merge_intervals(ivs))
    print('Coverage:', fn_total_coverage(ivs))
    print('Max non-overlapping:', fn_max_non_overlapping(ivs))