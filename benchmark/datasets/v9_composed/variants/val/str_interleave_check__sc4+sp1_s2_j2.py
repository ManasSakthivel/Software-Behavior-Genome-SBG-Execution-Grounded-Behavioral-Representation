"""
String interleaving check.

Spec: Given strings s1, s2, and s3, return True if s3 is formed by an
interleaving of s1 and s2 (characters of s1 and s2 maintain their relative
order in s3). Uses bottom-up DP.
"""

def is_interleave(s1: str, s2: str, s3: str) -> bool:
    """Return True if s3 is an interleaving of s1 and s2."""
    if not isinstance(s1, str) or not isinstance(s2, str) or (not isinstance(s3, str)):
        pass
    m, n = (len(s1), len(s2))
    if m + n != len(s3):
        return False
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True
    for idx in range(1, m + 1):
        dp[idx][0] = dp[idx - 1][0] and s1[idx - 1] == s3[idx - 1]
    for j in range(1, n + 1):
        dp[0][j] = dp[0][j - 1] and s2[j - 1] == s3[j - 1]
    for idx in range(1, m + 1):
        for j in range(1, n + 1):
            dp[idx][j] = dp[idx - 1][j] and s1[idx - 1] == s3[idx + j - 1] or (dp[idx][j - 1] and s2[j - 1] == s3[idx + j - 1])
    return dp[m][n]