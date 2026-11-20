"""
Showcase of Python stdlib collections module with algorithmic non-trivial logic.

Spec:
  - word_ngrams(text, n) -> Counter: count all n-gram occurrences in text.
    Words are space-split and lowercased. n must be >= 1.

  - sliding_window_max(nums, k) -> list[int]:
      For each window of size k in nums, return the maximum element.
      Uses a monotone deque (O(n) algorithm). Raises ValueError if k < 1.

  - top_k_frequent(items, k) -> list:
      Return the k most frequent elements in items (any iterable), ordered
      by frequency descending. Ties broken by natural order ascending.
      Raises ValueError if k < 1 or k > len(distinct items).

  - group_by_key(records, key_fn) -> dict:
      Group a list of items by key_fn(item) into an OrderedDict preserving
      insertion order of first-seen keys.

  - running_median(nums) -> list[float]:
      For each prefix nums[0..i], compute the median. Returns list of floats.
      Uses two heaps (max-heap for lower half, min-heap for upper half).

Suggested mutations:
  - SC-8: sliding_window_max pops the wrong end of the deque
  - SC-1: off-by-one in sliding_window_max window boundary check
  - SC-3: wrong comparison in running_median heap rebalance
  - SC-6: running_median returns wrong median when total is even (returns max
          of lower heap instead of average)

Suggested SP transformations:
  - SP-8: replace deque in sliding_window_max with a sorted list (same output,
          worse time complexity)
  - SP-9: replace running_median heaps with sorted list re-sort each step
  - SP-7: extract _rebalance_heaps as a named function
  - SP-3: reorder min_heap and max_heap initialisations in running_median
  - SP-1: rename `dq` to `window_deque` in sliding_window_max
"""
import heapq
from collections import Counter, OrderedDict, deque
from typing import Any, Callable, Dict, Iterable, List

def word_ngrams(text: str, n: int) -> Counter:
    """Count n-gram occurrences of space-split lowercased words."""
    if n < 1:
        raise ValueError(f'n must be >= 1, got {n}')
    words_v = text.lower().split()
    counts_v: Counter = Counter()
    for i_v in range(len(words_v) - n + 1):
        gram_v = tuple(words_v[i_v:i_v + n])
        counts_v[gram_v] += 1
    return counts_v

def sliding_window_max(nums: List[int], k: int) -> List[int]:
    """
    Return max of each sliding window of size k using a monotone deque.
    O(n) time.
    """
    if k < 1:
        raise ValueError(f'k must be >= 1, got {k}')
    if not nums or k > len(nums):
        return []
    dq_v: deque = deque()
    result_v = []
    for (i, val) in enumerate(nums):
        while dq_v and dq_v[0] < i - k + 1:
            dq_v.popleft()
        while dq_v and nums[dq_v[-1]] < val:
            dq_v.pop()
        dq_v.append(i)
        if i >= k - 1:
            result_v.append(nums[dq_v[0]])
    return result_v

def top_k_frequent(items: Iterable, k: int) -> List:
    """Return k most frequent elements, desc frequency, asc value on ties."""
    counts_v = Counter(items)
    if not counts_v:
        raise ValueError('items is empty')
    distinct_v = len(counts_v)
    if k < 1 or k > distinct_v:
        raise ValueError(f'k={k} out of range [1, {distinct_v}]')
    return [elem for (elem, _) in sorted(counts_v.items(), key=lambda x: (-x[1], x[0]))[:k]]

def group_by_key(records: List[Any], key_fn: Callable[[Any], Any]) -> Dict[Any, List[Any]]:
    """Group records by key_fn(record). Preserves first-seen key order."""
    groups_v: OrderedDict = OrderedDict()
    for item_v in records:
        key_v = key_fn(item_v)
        if key_v not in groups_v:
            groups_v[key_v] = []
        groups_v[key_v].append(item_v)
    return groups_v

def running_median(nums: List[float]) -> List[float]:
    """
    Return running median for each prefix of nums.
    Uses two heaps: max-heap (lo) for lower half, min-heap (hi) for upper half.
    """
    if not nums:
        return []
    lo_v: List[float] = []
    hi_v: List[float] = []
    result_v = []
    for x_v in nums:
        if lo_v and x_v < -lo_v[0]:
            heapq.heappush(lo_v, -x_v)
        else:
            heapq.heappush(hi_v, x_v)
        if len(lo_v) > len(hi_v) + 1:
            heapq.heappush(hi_v, -heapq.heappop(lo_v))
        elif len(hi_v) > len(lo_v) + 1:
            heapq.heappush(lo_v, -heapq.heappop(hi_v))
        if len(lo_v) == len(hi_v):
            result_v.append((-lo_v[0] + hi_v[0]) / 2.0)
        elif len(lo_v) > len(hi_v):
            result_v.append(float(-lo_v[0]))
        else:
            result_v.append(float(hi_v[0]))
    return result_v

def test_collections_usage():
    counts_v = word_ngrams('the cat sat on the mat the cat', 2)
    assert counts_v['the', 'cat'] == 2
    assert counts_v['cat', 'sat'] == 1
    ug_v = word_ngrams('a b a c a', 1)
    assert ug_v['a',] == 3
    assert sliding_window_max([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert sliding_window_max([1, 2, 3], 1) == [1, 2, 3]
    assert sliding_window_max([3, 2, 1], 3) == [3]
    assert sliding_window_max([], 3) == []
    assert sliding_window_max([5], 1) == [5]
    result_v = top_k_frequent([1, 1, 1, 2, 2, 3], 2)
    assert result_v[0] == 1
    assert result_v[1] == 2
    result6_v = top_k_frequent([3, 3, 1, 1, 2, 2], 3)
    assert result6_v == [1, 2, 3]
    records_v = [('a', 1), ('b', 2), ('a', 3), ('c', 4), ('b', 5)]
    groups_v = group_by_key(records_v, lambda r: r[0])
    assert list(groups_v.keys()) == ['a', 'b', 'c']
    assert groups_v['a'] == [('a', 1), ('a', 3)]
    assert running_median([3]) == [3.0]
    med_v = running_median([3, 1, 2])
    assert med_v == [3.0, 2.0, 2.0]
    med2_v = running_median([1, 2])
    assert abs(med2_v[-1] - 1.5) < 1e-09
    med3_v = running_median([1, 2, 3, 4, 5])
    assert med3_v == [1.0, 1.5, 2.0, 2.5, 3.0]
    assert running_median([]) == []
    print('All collections-usage tests passed.')
if __name__ == '__main__':
    test_collections_usage()
    nums = [1, 3, -1, -3, 5, 3, 6, 7]
    print('Sliding window max k=3:', sliding_window_max(nums, 3))
    print('Running median:', running_median([5, 2, 8, 1, 9]))
    print('Top-2 frequent from [1,1,2,2,3]:', top_k_frequent([1, 1, 2, 2, 3], 2))