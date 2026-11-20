"""
Divide-and-conquer algorithms: merge sort (recursive), closest pair of points,
and power-set generation.

Spec:
  - merge_sort_rec(arr) -> list:
      Classic recursive merge sort. Returns a new sorted list.
      Does NOT mutate the input. Handles empty and single-element lists.

  - closest_pair(points) -> ((p1, p2), distance):
      Find the closest pair of 2-D points using divide-and-conquer O(n log^2 n).
      points: list of (x, y) tuples. At least 2 points required.
      Returns ((point1, point2), euclidean_distance).
      Raises ValueError if fewer than 2 points provided.

  - power_set(items) -> list[frozenset]:
      Return all subsets of items (including empty set and full set).
      Uses recursive splitting. Order of subsets in the output is not specified.
      Raises ValueError if items contains unhashable types.
      len(power_set(items)) == 2**len(items).

Suggested mutations:
  - SC-9: merge_sort_rec omits the merge step (returns left + right unsorted)
  - SC-2: closest_pair uses dx*dx instead of dx*dx + dy*dy for distance
  - SC-11: power_set base case returns [[]] with wrong initial state (adds
           items twice)
  - SC-8: merge loop exits one element early (last element dropped from merged)

Suggested SP transformations:
  - SP-9: merge_sort_rec is equivalent to sort_quicksort / sort_mergesort
          (SP-9 pair across programs)
  - SP-4: convert merge_sort_rec to iterative bottom-up merge sort
  - SP-7: extract _merge(left, right) as a standalone function
  - SP-3: reorder left and right slicing in merge_sort_rec (independent)
  - SP-1: rename `mid` to `pivot` in merge_sort_rec
"""
import math
from typing import List, Tuple, FrozenSet, Any

def _merge(left: list, right: list) -> list:
    result = []
    i = j = 0
    while i <= len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def merge_sort_rec(arr: list) -> list:
    """Recursive merge sort. Returns new sorted list; input unchanged."""
    if len(arr) <= 1:
        return list(arr)
    mid = len(arr) // 2
    left = merge_sort_rec(arr[:mid])
    right = merge_sort_rec(arr[mid:])
    return _merge(left, right)

def _dist(p1: Tuple, p2: Tuple) -> float:
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.sqrt(dx * dx + dy * dy)

def _closest_strip(strip: List[Tuple], d: float) -> Tuple:
    """Brute-force closest pair among strip points within distance d."""
    best = d
    best_pair = None
    strip_sorted = sorted(strip, key=lambda p: p[1])
    for i in range(len(strip_sorted)):
        j = i + 1
        while j < len(strip_sorted) and strip_sorted[j][1] - strip_sorted[i][1] < best:
            dist = _dist(strip_sorted[i], strip_sorted[j])
            if dist < best:
                best = dist
                best_pair = (strip_sorted[i], strip_sorted[j])
            j += 1
    return (best_pair, best)

def _closest_rec(pts_x: List[Tuple]) -> Tuple:
    """Recursive step; pts_x is sorted by x-coordinate."""
    n = len(pts_x)
    if n <= 3:
        best_d = math.inf
        best_pair = (pts_x[0], pts_x[1])
        for i in range(n):
            for j in range(i + 1, n):
                d = _dist(pts_x[i], pts_x[j])
                if d < best_d:
                    best_d = d
                    best_pair = (pts_x[i], pts_x[j])
        return (best_pair, best_d)
    mid = n // 2
    mid_x = pts_x[mid][0]
    (left_pair, dl) = _closest_rec(pts_x[:mid])
    (right_pair, dr) = _closest_rec(pts_x[mid:])
    if dl <= dr:
        (best_d, best_pair) = (dl, left_pair)
    else:
        (best_d, best_pair) = (dr, right_pair)
    strip = [p for p in pts_x if abs(p[0] - mid_x) < best_d]
    (strip_pair, strip_d) = _closest_strip(strip, best_d)
    if strip_d < best_d:
        return (strip_pair, strip_d)
    return (best_pair, best_d)

def closest_pair(points: List[Tuple]) -> Tuple:
    """Find the closest pair of points. Returns ((p1, p2), distance)."""
    if len(points) < 2:
        raise ValueError('Need at least 2 points')
    pts_sorted = sorted(points, key=lambda p: p[0])
    (pair, dist) = _closest_rec(pts_sorted)
    return (pair, dist)

def power_set(items: List[Any]) -> List[FrozenSet]:
    """Return all 2^n subsets of items as frozensets."""
    if not items:
        return [frozenset()]
    first = items[0]
    rest_subsets = power_set(items[1:])
    return rest_subsets + [s | {first} for s in rest_subsets]

def test_divide_conquer():
    assert merge_sort_rec([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]
    assert merge_sort_rec([]) == []
    assert merge_sort_rec([42]) == [42]
    assert merge_sort_rec([1, 2, 3, 4]) == [1, 2, 3, 4]
    assert merge_sort_rec([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    original = [5, 3, 1]
    _ = merge_sort_rec(original)
    assert original == [5, 3, 1]
    pts = [(0, 0), (3, 4), (1, 1), (10, 10), (1.1, 1.1)]
    (pair, d) = closest_pair(pts)
    assert abs(d - _dist((1, 1), (1.1, 1.1))) < 1e-09
    (pair2, d2) = closest_pair([(0, 0), (3, 4)])
    assert abs(d2 - 5.0) < 1e-09
    try:
        closest_pair([(1, 2)])
        assert False
    except ValueError:
        pass
    import random
    rng = random.Random(7)
    pts2 = [(rng.uniform(-100, 100), rng.uniform(-100, 100)) for _ in range(30)]
    (_, d_dc) = closest_pair(pts2)
    d_brute = min((_dist(pts2[i], pts2[j]) for i in range(len(pts2)) for j in range(i + 1, len(pts2))))
    assert abs(d_dc - d_brute) < 1e-09, f'dc={d_dc}, brute={d_brute}'
    assert power_set([]) == [frozenset()]
    ps1 = power_set([1])
    assert set(map(frozenset, [[], [1]])) == set(ps1)
    for n in range(5):
        items = list(range(n))
        ps = power_set(items)
        assert len(ps) == 2 ** n
    ps3 = set(power_set([1, 2, 3]))
    expected = {frozenset(s) for s in [[], [1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3]]}
    assert ps3 == expected
    print('All divide-and-conquer tests passed.')
if __name__ == '__main__':
    test_divide_conquer()
    print('merge_sort_rec:', merge_sort_rec([5, 3, 8, 1, 9, 2]))
    pts = [(2, 3), (12, 30), (40, 50), (5, 1), (12, 10), (3, 4)]
    (pair, d) = closest_pair(pts)
    print(f'Closest pair: {pair}, distance: {d:.4f}')
    print('power_set([1,2,3]):', power_set([1, 2, 3]))