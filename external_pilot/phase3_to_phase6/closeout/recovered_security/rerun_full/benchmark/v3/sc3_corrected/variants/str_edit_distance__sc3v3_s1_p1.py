# program_id: str_edit_distance
# category: string_processing
# spec_version: 1.0

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
    m, n = len(s), len(t)
    # dp[i][j] = edit distance between s[:i] and t[:j]
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
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # delete from s
                    dp[i][j - 1],      # insert into s
                    dp[i - 1][j - 1],  # substitute
                )
    return dp[m][n]


def align(s: str, t: str) -> Tuple[List[str], str, str]:
    """
    Return (edit_script, aligned_s, aligned_t).
    edit_script is a list of 'M'(match), 'S'(substitution), 'I'(insert), 'D'(delete).
    aligned_s and aligned_t have '-' for gaps.
    """
    m, n = len(s), len(t)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    # Traceback
    ops, as_, at_ = [], [], []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and s[i-1] == t[j-1] and dp[i][j] == dp[i-1][j-1]:
            ops.append("M"); as_.append(s[i-1]); at_.append(t[j-1]); i -= 1; j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            ops.append("S"); as_.append(s[i-1]); at_.append(t[j-1]); i -= 1; j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            ops.append("D"); as_.append(s[i-1]); at_.append("-"); i -= 1
        else:
            ops.append("I"); as_.append("-"); at_.append(t[j-1]); j -= 1

    ops.reverse(); as_.reverse(); at_.reverse()
    return ops, "".join(as_), "".join(at_)


def edit_distance_bounded(s: str, t: str, max_dist: int) -> int:
    """Return edit distance, or max_dist+1 if distance > max_dist (early exit)."""
    m, n = len(s), len(t)
    if abs(m - n) > max_dist:
        return max_dist + 1
    # Standard DP but skip cells far from diagonal
    dp = [[max_dist + 1] * (n + 1) for _ in range(m + 1)]
    for i in range(min(m, max_dist) + 1): dp[i][0] = i
    for j in range(min(n, max_dist) + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(max(1, i - max_dist), min(n, i + max_dist) + 1):
            if s[i-1] == t[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    result = dp[m][n]
    return result if result <= max_dist else max_dist + 1


# ---------- tests ----------

def test_edit_distance():
    # Test 1: classic examples
    assert edit_distance("kitten", "sitting") == 3
    assert edit_distance("Saturday", "Sunday") == 2
    assert edit_distance("", "") == 0

    # Test 2: empty string cases
    assert edit_distance("abc", "") == 3
    assert edit_distance("", "abc") == 3

    # Test 3: identical strings
    assert edit_distance("hello", "hello") == 0

    # Test 4: single character operations
    assert edit_distance("a", "b") == 1    # substitution
    assert edit_distance("a", "") == 1     # deletion
    assert edit_distance("", "a") == 1     # insertion

    # Test 5: alignment structure
    ops, as_, at_ = align("cat", "cut")
    assert "S" in ops   # one substitution
    assert len(as_) == len(at_)

    # Test 6: bounded — within limit
    assert edit_distance_bounded("kitten", "sitting", 5) == 3

    # Test 7: bounded — exceeds limit
    assert edit_distance_bounded("kitten", "sitting", 2) == 3  # returns max+1

    # Test 8: alignment consistency with edit_distance
    ops2, _, _ = align("Saturday", "Sunday")
    subs = ops2.count("S")
    dels = ops2.count("D")
    ins  = ops2.count("I")
    assert subs + dels + ins == edit_distance("Saturday", "Sunday")

    print("All edit_distance tests passed.")


if __name__ == "__main__":
    test_edit_distance()
    print(f"edit_distance('kitten','sitting') = {edit_distance('kitten','sitting')}")
    ops, as_, at_ = align("Sunday", "Saturday")
    print(f"alignment:\n  {as_}\n  {at_}\n  {''.join(ops)}")
