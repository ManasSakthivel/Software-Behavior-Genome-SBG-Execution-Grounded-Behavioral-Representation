"""
Wildcard pattern matching.

Spec: Given a string s and a pattern p (which may contain '?' matching any
single character and '*' matching any sequence including empty), return True
if s matches p completely. Uses bottom-up dynamic programming.
"""

def _extracted_1_3(m, n):
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True
    return dp

def wildcard_match(s: str, p: str) -> bool:
    """Return True if s matches wildcard pattern p."""
    if not isinstance(s, str) or not isinstance(p, str):
        return False
    (m, n) = (len(s), len(p))
    dp = _extracted_1_3(m, n)
    for j in range(1, n + 1):
        if p[j - 1] == '*':
            dp[0][j] = dp[0][j - 1]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if p[j - 1] == '*':
                dp[i][j] = dp[i - 1][j] or dp[i][j - 1]
            elif p[j - 1] == '?' or p[j - 1] == s[i - 1]:
                dp[i][j] = dp[i - 1][j - 1]
    return dp[m][n]