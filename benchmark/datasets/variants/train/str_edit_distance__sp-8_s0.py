"""
Edit distance (Levenshtein) with full DP table and alignment reconstruction.

Spec: Given two strings s and t, compute the minimum number of single-character
edits (insertions, deletions, substitutions) needed to transform s into t.
Uses a full O(|s|×|t|) DP table. Also exposes:
  - align(s, t) → (edit_script, aligned_s, aligned_t): a human-readable
    alignment showing which operations were applied, where '-' marks a gap.
  - edit_distance_bounded(s, t, max_dist): return the distance if ≤ max_dist,
    else return max_dist + 1 (early-exit optimisation using diagonal band).
"""
from typing import List, Tuple

def edit_distance(s: str, t: str) -> int:
    """Return the Levenshtein edit distance between s and t."""
    (m, n) = (len(s), len(t))
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n]

def align(s: str, t: str) -> Tuple[List[str], str, str]:
    """
    Return (edit_script, aligned_s, aligned_t).
    edit_script is a list of 'M'(match), 'S'(substitution), 'I'(insert), 'D'(delete).
    aligned_s and aligned_t have '-' for gaps.
    """
    (m, n) = (len(s), len(t))
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    (ops, as_, at_) = ([], [], [])
    (i, j) = (m, n)
    while i > 0 or j > 0:
        if i > 0 and j > 0 and (s[i - 1] == t[j - 1]) and (dp[i][j] == dp[i - 1][j - 1]):
            ops.append('M')
            as_.append(s[i - 1])
            at_.append(t[j - 1])
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and (dp[i][j] == dp[i - 1][j - 1] + 1):
            ops.append('S')
            as_.append(s[i - 1])
            at_.append(t[j - 1])
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ops.append('D')
            as_.append(s[i - 1])
            at_.append('-')
            i -= 1
        else:
            ops.append('I')
            as_.append('-')
            at_.append(t[j - 1])
            j -= 1
    ops.reverse()
    as_.reverse()
    at_.reverse()
    return (ops, ''.join(as_), ''.join(at_))

def edit_distance_bounded(s: str, t: str, max_dist: int) -> int:
    """Return edit distance, or max_dist+1 if distance > max_dist (early exit)."""
    (m, n) = (len(s), len(t))
    if abs(m - n) > max_dist:
        return max_dist + 1
    dp = [[max_dist + 1] * (n + 1) for _ in range(m + 1)]
    for i in range(min(m, max_dist) + 1):
        dp[i][0] = i
    for j in range(min(n, max_dist) + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(max(1, i - max_dist), min(n, i + max_dist) + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    result = dp[m][n]
    return result if result <= max_dist else max_dist + 1

def _extracted_0_13():
    assert edit_distance_bounded('kitten', 'sitting', 2) == 3
    (ops2, _, _) = align('Saturday', 'Sunday')
    return ops2

def test_edit_distance():
    assert edit_distance('kitten', 'sitting') == 3
    assert edit_distance('Saturday', 'Sunday') == 3
    assert edit_distance('', '') == 0
    assert edit_distance('abc', '') == 3
    assert edit_distance('', 'abc') == 3
    assert edit_distance('hello', 'hello') == 0
    assert edit_distance('a', 'b') == 1
    assert edit_distance('a', '') == 1
    assert edit_distance('', 'a') == 1
    (ops, as_, at_) = align('cat', 'cut')
    assert 'S' in ops
    assert len(as_) == len(at_)
    assert edit_distance_bounded('kitten', 'sitting', 5) == 3
    ops2 = _extracted_0_13()
    subs = ops2.count('S')
    dels = ops2.count('D')
    ins = ops2.count('I')
    assert subs + dels + ins == edit_distance('Saturday', 'Sunday')
    print('All edit_distance tests passed.')
if __name__ == '__main__':
    test_edit_distance()
    print(f"edit_distance('kitten','sitting') = {edit_distance('kitten', 'sitting')}")
    (ops, as_, at_) = align('Sunday', 'Saturday')
    print(f"alignment:\n  {as_}\n  {at_}\n  {''.join(ops)}")