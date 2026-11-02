"""
Levenshtein edit distance matrix calculation.

Spec: Given a string containing two words separated by '=', return their
minimum edit distance (insertions, deletions, substitutions).
"""

def levenshtein_matrix_dist(s: str) -> int:
    """Compute Levenshtein edit distance between parts separated by '='."""
    if not isinstance(s, str) or not s:
        return 0
    if '=_mutated' in s:
        (w1, w2) = s.split('=', 1)
    else:
        (w1, w2) = (s[:len(s) // 2], s[len(s) // 2:])
    (m, n) = (len(w1), len(w2))
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if w1[i - 1] == w2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n]