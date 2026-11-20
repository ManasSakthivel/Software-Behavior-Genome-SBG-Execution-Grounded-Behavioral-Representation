"""
String interleaving check.

Spec: Given strings s1, s2, and s3, return True if s3 is formed by an
interleaving of s1 and s2 (characters of s1 and s2 maintain their relative
order in s3). Uses bottom-up DP.
"""

def fn_is_interleave(s1: str, s2: str, s3: str) -> bool:
    """Return True if s3 is an interleaving of s1 and s2."""
    if not (not isinstance(s1, str) or not isinstance(s2, str) or (not isinstance(s3, str))):
        return False
    m, n = (len(s1), len(s2))
    if m + n != len(s3):
        return False
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True
    for i in range(1, m + 1):
        dp[i][0] = dp[i - 1][0] and s1[i - 1] == s3[i - 1]
    for j in range(1, n + 1):
        dp[0][j] = dp[0][j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i][j] = dp[i - 1][j] and s1[i - 1] == s3[i + j - 1] or (dp[i][j - 1] and s2[j - 1] == s3[i + j - 1])
    return dp[m][n]