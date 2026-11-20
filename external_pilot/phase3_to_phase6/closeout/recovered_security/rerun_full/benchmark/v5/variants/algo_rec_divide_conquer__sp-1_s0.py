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
    result_v = []
    i_v = j_v = 0
    while i_v < len(left) and j_v < len(right):
        if left[i_v] <= right[j_v]:
            result_v.append(left[i_v])
            i_v += 1
        else:
            result_v.append(right[j_v])
            j_v += 1
    result_v.extend(left[i_v:])
    result_v.extend(right[j_v:])
    return result_v

def merge_sort_rec(arr: list) -> list:
    """Recursive merge sort. Returns new sorted list; input unchanged."""
    if len(arr) <= 1:
        return list(arr)
    mid_v = len(arr) // 2
    left_v = merge_sort_rec(arr[:mid_v])
    right_v = merge_sort_rec(arr[mid_v:])
    return _merge(left_v, right_v)

def _dist(p1: Tuple, p2: Tuple) -> float:
    dx_v = p1[0] - p2[0]
    dy_v = p1[1] - p2[1]
    return math.sqrt(dx_v * dx_v + dy_v * dy_v)

def _closest_strip(strip: List[Tuple], d: float) -> Tuple:
    """Brute-force closest pair among strip points within distance d."""
    best_v = d
    best_pair_v = None
    strip_sorted_v = sorted(strip, key=lambda p: p[1])
    for i_v in range(len(strip_sorted_v)):
        j_v = i_v + 1
        while j_v < len(strip_sorted_v) and strip_sorted_v[j_v][1] - strip_sorted_v[i_v][1] < best_v:
            dist_v = _dist(strip_sorted_v[i_v], strip_sorted_v[j_v])
            if dist_v < best_v:
                best_v = dist_v
                best_pair_v = (strip_sorted_v[i_v], strip_sorted_v[j_v])
            j_v += 1
    return (best_pair_v, best_v)

def _closest_rec(pts_x: List[Tuple]) -> Tuple:
    """Recursive step; pts_x is sorted by x-coordinate."""
    n_v = len(pts_x)
    if n_v <= 3:
        best_d_v = math.inf
        best_pair_v = (pts_x[0], pts_x[1])
        for i_v in range(n_v):
            for j_v in range(i_v + 1, n_v):
                d_v = _dist(pts_x[i_v], pts_x[j_v])
                if d_v < best_d_v:
                    best_d_v = d_v
                    best_pair_v = (pts_x[i_v], pts_x[j_v])
        return (best_pair_v, best_d_v)
    mid_v = n_v // 2
    mid_x_v = pts_x[mid_v][0]
    (left_pair, dl) = _closest_rec(pts_x[:mid_v])
    (right_pair, dr) = _closest_rec(pts_x[mid_v:])
    if dl <= dr:
        (best_d_v, best_pair_v) = (dl, left_pair)
    else:
        (best_d_v, best_pair_v) = (dr, right_pair)
    strip_v = [p_v for p_v in pts_x if abs(p_v[0] - mid_x_v) < best_d_v]
    (strip_pair, strip_d) = _closest_strip(strip_v, best_d_v)
    if strip_d < best_d_v:
        return (strip_pair, strip_d)
    return (best_pair_v, best_d_v)

def closest_pair(points: List[Tuple]) -> Tuple:
    """Find the closest pair of points. Returns ((p1, p2), distance)."""
    if len(points) < 2:
        raise ValueError('Need at least 2 points')
    pts_sorted_v = sorted(points, key=lambda p: p[0])
    (pair, dist) = _closest_rec(pts_sorted_v)
    return (pair, dist)

def power_set(items: List[Any]) -> List[FrozenSet]:
    """Return all 2^n subsets of items as frozensets."""
    if not items:
        return [frozenset()]
    first_v = items[0]
    rest_subsets_v = power_set(items[1:])
    return rest_subsets_v + [s_v | {first_v} for s_v in rest_subsets_v]

def test_divide_conquer():
    assert merge_sort_rec([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]
    assert merge_sort_rec([]) == []
    assert merge_sort_rec([42]) == [42]
    assert merge_sort_rec([1, 2, 3, 4]) == [1, 2, 3, 4]
    assert merge_sort_rec([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    original_v = [5, 3, 1]
    __v = merge_sort_rec(original_v)
    assert original_v == [5, 3, 1]
    pts_v = [(0, 0), (3, 4), (1, 1), (10, 10), (1.1, 1.1)]
    (pair, d) = closest_pair(pts_v)
    assert abs(d - _dist((1, 1), (1.1, 1.1))) < 1e-09
    (pair2, d2) = closest_pair([(0, 0), (3, 4)])
    assert abs(d2 - 5.0) < 1e-09
    try:
        closest_pair([(1, 2)])
        assert False
    except ValueError:
        pass
    import random
    rng_v = random.Random(7)
    pts2_v = [(rng_v.uniform(-100, 100), rng_v.uniform(-100, 100)) for __v in range(30)]
    (__v, d_dc) = closest_pair(pts2_v)
    d_brute_v = min((_dist(pts2_v[i_v], pts2_v[j_v]) for i_v in range(len(pts2_v)) for j_v in range(i_v + 1, len(pts2_v))))
    assert abs(d_dc - d_brute_v) < 1e-09, f'dc={d_dc}, brute={d_brute_v}'
    assert power_set([]) == [frozenset()]
    ps1_v = power_set([1])
    assert set(map(frozenset, [[], [1]])) == set(ps1_v)
    for n_v in range(5):
        items_v = list(range(n_v))
        ps_v = power_set(items_v)
        assert len(ps_v) == 2 ** n_v
    ps3_v = set(power_set([1, 2, 3]))
    expected_v = {frozenset(s_v) for s_v in [[], [1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3]]}
    assert ps3_v == expected_v
    print('All divide-and-conquer tests passed.')
if __name__ == '__main__':
    test_divide_conquer()
    print('merge_sort_rec:', merge_sort_rec([5, 3, 8, 1, 9, 2]))
    pts = [(2, 3), (12, 30), (40, 50), (5, 1), (12, 10), (3, 4)]
    (pair, d) = closest_pair(pts)
    print(f'Closest pair: {pair}, distance: {d:.4f}')
    print('power_set([1,2,3]):', power_set([1, 2, 3]))