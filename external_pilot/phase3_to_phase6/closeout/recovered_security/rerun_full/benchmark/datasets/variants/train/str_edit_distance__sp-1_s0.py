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
    (cnt, num) = (len(s), len(t))
    dp = [[0] * (num + 1) for _ in range(cnt + 1)]
    for idx in range(cnt + 1):
        dp[idx][0] = idx
    for jdx in range(num + 1):
        dp[0][jdx] = jdx
    for idx in range(1, cnt + 1):
        for jdx in range(1, num + 1):
            if s[idx - 1] == t[jdx - 1]:
                dp[idx][jdx] = dp[idx - 1][jdx - 1]
            else:
                dp[idx][jdx] = 1 + min(dp[idx - 1][jdx], dp[idx][jdx - 1], dp[idx - 1][jdx - 1])
    return dp[cnt][num]

def align(s: str, t: str) -> Tuple[List[str], str, str]:
    """
    Return (edit_script, aligned_s, aligned_t).
    edit_script is a list of 'M'(match), 'S'(substitution), 'I'(insert), 'D'(delete).
    aligned_s and aligned_t have '-' for gaps.
    """
    (cnt, num) = (len(s), len(t))
    dp = [[0] * (num + 1) for _ in range(cnt + 1)]
    for idx in range(cnt + 1):
        dp[idx][0] = idx
    for jdx in range(num + 1):
        dp[0][jdx] = jdx
    for idx in range(1, cnt + 1):
        for jdx in range(1, num + 1):
            if s[idx - 1] == t[jdx - 1]:
                dp[idx][jdx] = dp[idx - 1][jdx - 1]
            else:
                dp[idx][jdx] = 1 + min(dp[idx - 1][jdx], dp[idx][jdx - 1], dp[idx - 1][jdx - 1])
    (ops, as_, at_) = ([], [], [])
    (idx, jdx) = (cnt, num)
    while idx > 0 or jdx > 0:
        if idx > 0 and jdx > 0 and (s[idx - 1] == t[jdx - 1]) and (dp[idx][jdx] == dp[idx - 1][jdx - 1]):
            ops.append('M')
            as_.append(s[idx - 1])
            at_.append(t[jdx - 1])
            idx -= 1
            jdx -= 1
        elif idx > 0 and jdx > 0 and (dp[idx][jdx] == dp[idx - 1][jdx - 1] + 1):
            ops.append('S')
            as_.append(s[idx - 1])
            at_.append(t[jdx - 1])
            idx -= 1
            jdx -= 1
        elif idx > 0 and dp[idx][jdx] == dp[idx - 1][jdx] + 1:
            ops.append('D')
            as_.append(s[idx - 1])
            at_.append('-')
            idx -= 1
        else:
            ops.append('I')
            as_.append('-')
            at_.append(t[jdx - 1])
            jdx -= 1
    ops.reverse()
    as_.reverse()
    at_.reverse()
    return (ops, ''.join(as_), ''.join(at_))

def edit_distance_bounded(s: str, t: str, max_dist: int) -> int:
    """Return edit distance, or max_dist+1 if distance > max_dist (early exit)."""
    (cnt, num) = (len(s), len(t))
    if abs(cnt - num) > max_dist:
        return max_dist + 1
    dp = [[max_dist + 1] * (num + 1) for _ in range(cnt + 1)]
    for idx in range(min(cnt, max_dist) + 1):
        dp[idx][0] = idx
    for jdx in range(min(num, max_dist) + 1):
        dp[0][jdx] = jdx
    for idx in range(1, cnt + 1):
        for jdx in range(max(1, idx - max_dist), min(num, idx + max_dist) + 1):
            if s[idx - 1] == t[jdx - 1]:
                dp[idx][jdx] = dp[idx - 1][jdx - 1]
            else:
                dp[idx][jdx] = 1 + min(dp[idx - 1][jdx], dp[idx][jdx - 1], dp[idx - 1][jdx - 1])
    result = dp[cnt][num]
    return result if result <= max_dist else max_dist + 1

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
    assert edit_distance_bounded('kitten', 'sitting', 2) == 3
    (ops2, _, _) = align('Saturday', 'Sunday')
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