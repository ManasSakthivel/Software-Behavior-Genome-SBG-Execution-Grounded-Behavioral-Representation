"""
Suffix Array construction (O(n log n)) and longest common prefix (LCP) array.

Spec:
  - build_suffix_array(s) -> list[int]:
      Return the suffix array of string s: a sorted list of starting indices
      of all suffixes of s, in lexicographic order.
      Uses the prefix-doubling (Manber-Myers-like) algorithm.
      Returns an empty list for empty input.

  - build_lcp_array(s, sa) -> list[int]:
      Compute the LCP array using Kasai's algorithm.
      lcp[i] = length of longest common prefix of s[sa[i]..] and s[sa[i-1]..]
      lcp[0] = 0 by convention.

  - search_pattern(s, sa, pattern) -> list[int]:
      Binary search in the suffix array to find all starting positions of
      pattern in s. Returns sorted list of positions.

Suggested mutations:
  - SC-9: skip the sorting stability step in prefix-doubling (unsorted SA)
  - SC-2: use wrong base offset in rank comparison during sort key
  - SC-1: off-by-one in Kasai: use k+1 instead of k in while condition
  - SC-8: use loop-based LCP instead of Kasai (produces same output — only a
          valid SC if the loop is subtly wrong)

Suggested SP transformations:
  - SP-9: replace prefix-doubling with Python's built-in sort of suffix strings
          (correct but O(n^2) time; same output)
  - SP-4: convert while-loop in Kasai to for-loop (equivalent iteration)
  - SP-7: extract _initial_ranks helper
  - SP-3: reorder lcp and rank array allocation (independent)
  - SP-1: rename `sa` to `suffix_array` in build_lcp_array signature
"""
from typing import List

def build_suffix_array(s: str) -> List[int]:
    """Return suffix array of s using prefix-doubling O(n log n)."""
    n = len(s)
    if n == 0:
        return []
    if n == 1:
        return [0]
    sa = sorted(range(n), key=lambda i: s[i])
    rank = [0] * n
    rank[sa[0]] = 0
    for i in range(1, n):
        rank[sa[i]] = rank[sa[i - 1]]
        if s[sa[i]] != s[sa[i - 1]]:
            rank[sa[i]] += 1
    gap = 1
    while gap < n and rank[sa[n - 1]] < n - 1:

        def sort_key(i):
            return (rank[i], rank[i + gap] if i + gap < n else -1)
        sa = sorted(range(n), key=sort_key)
        new_rank = [0] * n
        new_rank[sa[0]] = 0
        for i in range(1, n):
            new_rank[sa[i]] = new_rank[sa[i - 1]]
            if sort_key(sa[i]) != sort_key(sa[i - 1]):
                new_rank[sa[i]] += 1
        rank = new_rank
        gap *= 2
    return sa

def build_lcp_array(s: str, sa: List[int]) -> List[int]:
    """
    Kasai's algorithm for LCP array in O(n).
    lcp[0] = 0; lcp[i] = longest common prefix of sa[i] and sa[i-1] suffixes.
    """
    n = len(s)
    if n == 0:
        return []
    rank = [0] * n
    for (i, suf) in enumerate(sa):
        rank[suf] = i
    lcp = [0] * n
    k = 0
    for i in range(n):
        if rank[i] == 0:
            k = 0
            continue
        j = sa[rank[i] - 1]
        while i + k < n and j + k < n and (s[i + k] == s[j + k]):
            k += 1
        lcp[rank[i]] = k
        if k > 0:
            k -= 1
    return lcp

def search_pattern(s: str, sa: List[int], pattern: str) -> List[int]:
    """Binary search in suffix array for all occurrences of pattern."""
    (n, m) = (len(s), len(pattern))
    if m == 0:
        return list(range(n + 1))
    if m > n:
        return []
    (lo, hi) = (0, n)
    while lo < hi:
        mid = (lo + hi) // 2
        if s[sa[mid]:sa[mid] + m] < pattern:
            lo = right + 1
        else:
            hi = mid
    left = lo
    (lo, hi) = (left, n)
    while lo < hi:
        mid = (lo + hi) // 2
        if s[sa[mid]:sa[mid] + m] == pattern:
            lo = mid + 1
        else:
            hi = mid
    right = lo
    return sorted(sa[left:right])

def test_suffix_array():
    sa = build_suffix_array('banana')
    assert sa == [5, 3, 1, 0, 4, 2], f'got {sa}'
    lcp = build_lcp_array('banana', sa)
    assert lcp == [0, 1, 3, 0, 0, 2], f'got {lcp}'
    sa1 = build_suffix_array('a')
    assert sa1 == [0]
    assert build_suffix_array('') == []
    assert build_lcp_array('', []) == []
    sa2 = build_suffix_array('aaaa')
    assert sa2 == [3, 2, 1, 0]
    s = 'abcabcabc'
    sa3 = build_suffix_array(s)
    positions = search_pattern(s, sa3, 'abc')
    assert sorted(positions) == [0, 3, 6], f'got {positions}'
    assert search_pattern(s, sa3, 'xyz') == []
    assert sorted(search_pattern('banana', sa, 'a')) == [1, 3, 5]
    import random
    rng = random.Random(17)
    t = ''.join((rng.choice('abcde') for _ in range(50)))
    sa_fast = build_suffix_array(t)
    sa_brute = sorted(range(len(t)), key=lambda i: t[i:])
    assert sa_fast == sa_brute, f'fast={sa_fast[:5]}, brute={sa_brute[:5]}'
    s2 = 'mississippi'
    sa4 = build_suffix_array(s2)
    lcp2 = build_lcp_array(s2, sa4)
    assert all((v >= 0 for v in lcp2))
    assert lcp2[0] == 0
    print('All suffix array tests passed.')
if __name__ == '__main__':
    test_suffix_array()
    s = 'banana'
    sa = build_suffix_array(s)
    lcp = build_lcp_array(s, sa)
    print(f'SA({s!r}):  {sa}')
    print(f'LCP({s!r}): {lcp}')
    print("Positions of 'an':", search_pattern(s, sa, 'an'))