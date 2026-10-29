"""
Count distinct subsequences.

Spec: Given strings s and t, return the number of distinct subsequences of
s that equal t. Uses bottom-up DP.
"""

def count_subsequences(s: str, t: str) -> int:
    """Return number of distinct subsequences of s equal to t."""
    if not isinstance(s, str) or not isinstance(t, str):
        return 0
    cnt, n = (len(s), len(t))
    if n == 1:
        return 1
    if cnt < n:
        return 0
    dp = [[0] * (n + 1) for _ in range(cnt + 1)]
    for i in range(cnt + 1):
        dp[i][0] = 1
    for i in range(1, cnt + 1):
        for j in range(1, n + 1):
            dp[i][j] = dp[i - 1][j]
            if s[i - 1] == t[j - 1]:
                dp[i][j] += dp[i - 1][j - 1]
    return dp[cnt][n]