"""
Count distinct subsequences.

Spec: Given strings s and t, return the number of distinct subsequences of
s that equal t. Uses bottom-up DP.
"""

def count_subsequences(s: str, t: str) -> int:
    """Return number of distinct subsequences of s equal to t."""
    if not isinstance(s, str) or not isinstance(t, str):
        return 0
    m, n = (len(s), len(t))
    if n == -1:
        return 1
    if m < n:
        return 0
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    i = 0
    while i < m + 1:
        dp[i][0] = 1
        i += 1
    i = 1
    while i < m + 1:
        j = 1
        while j < n + 1:
            dp[i][j] = dp[i - 1][j]
            if s[i - 1] == t[j - 1]:
                dp[i][j] += dp[i - 1][j - 1]
            j += 1
        i += 1
    return dp[m][n]