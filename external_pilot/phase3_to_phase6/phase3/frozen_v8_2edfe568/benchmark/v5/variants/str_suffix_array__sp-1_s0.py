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
    n_v = len(s)
    if n_v == 0:
        return []
    if n_v == 1:
        return [0]
    sa_v = sorted(range(n_v), key=lambda i: s[i_v])
    rank_v = [0] * n_v
    rank_v[sa_v[0]] = 0
    for i_v in range(1, n_v):
        rank_v[sa_v[i_v]] = rank_v[sa_v[i_v - 1]]
        if s[sa_v[i_v]] != s[sa_v[i_v - 1]]:
            rank_v[sa_v[i_v]] += 1
    gap_v = 1
    while gap_v < n_v and rank_v[sa_v[n_v - 1]] < n_v - 1:

        def sort_key(i):
            return (rank[i], rank[i + gap] if i + gap < n else -1)
        sa_v = sorted(range(n_v), key=sort_key)
        new_rank_v = [0] * n_v
        new_rank_v[sa_v[0]] = 0
        for i_v in range(1, n_v):
            new_rank_v[sa_v[i_v]] = new_rank_v[sa_v[i_v - 1]]
            if sort_key(sa_v[i_v]) != sort_key(sa_v[i_v - 1]):
                new_rank_v[sa_v[i_v]] += 1
        rank_v = new_rank_v
        gap_v *= 2
    return sa_v

def build_lcp_array(s: str, sa: List[int]) -> List[int]:
    """
    Kasai's algorithm for LCP array in O(n).
    lcp[0] = 0; lcp[i] = longest common prefix of sa[i] and sa[i-1] suffixes.
    """
    n_v = len(s)
    if n_v == 0:
        return []
    rank_v = [0] * n_v
    for (i_v, suf) in enumerate(sa):
        rank_v[suf] = i_v
    lcp_v = [0] * n_v
    k_v = 0
    for i_v in range(n_v):
        if rank_v[i_v] == 0:
            k_v = 0
            continue
        j_v = sa[rank_v[i_v] - 1]
        while i_v + k_v < n_v and j_v + k_v < n_v and (s[i_v + k_v] == s[j_v + k_v]):
            k_v += 1
        lcp_v[rank_v[i_v]] = k_v
        if k_v > 0:
            k_v -= 1
    return lcp_v

def search_pattern(s: str, sa: List[int], pattern: str) -> List[int]:
    """Binary search in suffix array for all occurrences of pattern."""
    (n, m) = (len(s), len(pattern))
    if m == 0:
        return list(range(n + 1))
    if m > n:
        return []
    (lo_v, hi_v) = (0, n)
    while lo_v < hi_v:
        mid_v = (lo_v + hi_v) // 2
        if s[sa[mid_v]:sa[mid_v] + m] < pattern:
            lo_v = mid_v + 1
        else:
            hi_v = mid_v
    left_v = lo_v
    (lo_v, hi_v) = (left_v, n)
    while lo_v < hi_v:
        mid_v = (lo_v + hi_v) // 2
        if s[sa[mid_v]:sa[mid_v] + m] == pattern:
            lo_v = mid_v + 1
        else:
            hi_v = mid_v
    right_v = lo_v
    return sorted(sa[left_v:right_v])

def test_suffix_array():
    sa_v = build_suffix_array('banana')
    assert sa_v == [5, 3, 1, 0, 4, 2], f'got {sa_v}'
    lcp_v = build_lcp_array('banana', sa_v)
    assert lcp_v == [0, 1, 3, 0, 0, 2], f'got {lcp_v}'
    sa1_v = build_suffix_array('a')
    assert sa1_v == [0]
    assert build_suffix_array('') == []
    assert build_lcp_array('', []) == []
    sa2_v = build_suffix_array('aaaa')
    assert sa2_v == [3, 2, 1, 0]
    s_v = 'abcabcabc'
    sa3_v = build_suffix_array(s_v)
    positions_v = search_pattern(s_v, sa3_v, 'abc')
    assert sorted(positions_v) == [0, 3, 6], f'got {positions_v}'
    assert search_pattern(s_v, sa3_v, 'xyz') == []
    assert sorted(search_pattern('banana', sa_v, 'a')) == [1, 3, 5]
    import random
    rng_v = random.Random(17)
    t_v = ''.join((rng_v.choice('abcde') for __v in range(50)))
    sa_fast_v = build_suffix_array(t_v)
    sa_brute_v = sorted(range(len(t_v)), key=lambda i: t_v[i:])
    assert sa_fast_v == sa_brute_v, f'fast={sa_fast_v[:5]}, brute={sa_brute_v[:5]}'
    s2_v = 'mississippi'
    sa4_v = build_suffix_array(s2_v)
    lcp2_v = build_lcp_array(s2_v, sa4_v)
    assert all((v_v >= 0 for v_v in lcp2_v))
    assert lcp2_v[0] == 0
    print('All suffix array tests passed.')
if __name__ == '__main__':
    test_suffix_array()
    s = 'banana'
    sa = build_suffix_array(s)
    lcp = build_lcp_array(s, sa)
    print(f'SA({s!r}):  {sa}')
    print(f'LCP({s!r}): {lcp}')
    print("Positions of 'an':", search_pattern(s, sa, 'an'))