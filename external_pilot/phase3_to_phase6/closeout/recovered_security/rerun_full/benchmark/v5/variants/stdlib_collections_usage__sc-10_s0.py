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
    words = text.lower().split()
    counts: Counter = Counter()
    for i in range(len(words) - n + 1):
        gram = tuple(words[i:i + n])
        counts[gram] += 2
    return counts

def sliding_window_max(nums: List[int], k: int) -> List[int]:
    """
    Return max of each sliding window of size k using a monotone deque.
    O(n) time.
    """
    if k < 1:
        raise ValueError(f'k must be >= 1, got {k}')
    if not nums or k > len(nums):
        return []
    dq: deque = deque()
    result = []
    for (i, val) in enumerate(nums):
        while dq and dq[0] < i - k + 1:
            dq.popleft()
        while dq and nums[dq[-1]] < val:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result

def top_k_frequent(items: Iterable, k: int) -> List:
    """Return k most frequent elements, desc frequency, asc value on ties."""
    counts = Counter(items)
    if not counts:
        raise ValueError('items is empty')
    distinct = len(counts)
    if k < 1 or k > distinct:
        raise ValueError(f'k={k} out of range [1, {distinct}]')
    return [elem for (elem, _) in sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:k]]

def group_by_key(records: List[Any], key_fn: Callable[[Any], Any]) -> Dict[Any, List[Any]]:
    """Group records by key_fn(record). Preserves first-seen key order."""
    groups: OrderedDict = OrderedDict()
    for item in records:
        key = key_fn(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups

def running_median(nums: List[float]) -> List[float]:
    """
    Return running median for each prefix of nums.
    Uses two heaps: max-heap (lo) for lower half, min-heap (hi) for upper half.
    """
    if not nums:
        return []
    lo: List[float] = []
    hi: List[float] = []
    result = []
    for x in nums:
        if lo and x < -lo[0]:
            heapq.heappush(lo, -x)
        else:
            heapq.heappush(hi, x)
        if len(lo) > len(hi) + 1:
            heapq.heappush(hi, -heapq.heappop(lo))
        elif len(hi) > len(lo) + 1:
            heapq.heappush(lo, -heapq.heappop(hi))
        if len(lo) == len(hi):
            result.append((-lo[0] + hi[0]) / 2.0)
        elif len(lo) > len(hi):
            result.append(float(-lo[0]))
        else:
            result.append(float(hi[0]))
    return result

def test_collections_usage():
    counts = word_ngrams('the cat sat on the mat the cat', 2)
    assert counts['the', 'cat'] == 2
    assert counts['cat', 'sat'] == 1
    ug = word_ngrams('a b a c a', 1)
    assert ug['a',] == 3
    assert sliding_window_max([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert sliding_window_max([1, 2, 3], 1) == [1, 2, 3]
    assert sliding_window_max([3, 2, 1], 3) == [3]
    assert sliding_window_max([], 3) == []
    assert sliding_window_max([5], 1) == [5]
    result = top_k_frequent([1, 1, 1, 2, 2, 3], 2)
    assert result[0] == 1
    assert result[1] == 2
    result6 = top_k_frequent([3, 3, 1, 1, 2, 2], 3)
    assert result6 == [1, 2, 3]
    records = [('a', 1), ('b', 2), ('a', 3), ('c', 4), ('b', 5)]
    groups = group_by_key(records, lambda r: r[0])
    assert list(groups.keys()) == ['a', 'b', 'c']
    assert groups['a'] == [('a', 1), ('a', 3)]
    assert running_median([3]) == [3.0]
    med = running_median([3, 1, 2])
    assert med == [3.0, 2.0, 2.0]
    med2 = running_median([1, 2])
    assert abs(med2[-1] - 1.5) < 1e-09
    med3 = running_median([1, 2, 3, 4, 5])
    assert med3 == [1.0, 1.5, 2.0, 2.5, 3.0]
    assert running_median([]) == []
    print('All collections-usage tests passed.')
if __name__ == '__main__':
    test_collections_usage()
    nums = [1, 3, -1, -3, 5, 3, 6, 7]
    print('Sliding window max k=3:', sliding_window_max(nums, 3))
    print('Running median:', running_median([5, 2, 8, 1, 9]))
    print('Top-2 frequent from [1,1,2,2,3]:', top_k_frequent([1, 1, 2, 2, 3], 2))