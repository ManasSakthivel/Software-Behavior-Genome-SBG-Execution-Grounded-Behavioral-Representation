"""
Wildcard pattern matching.

Spec: Given a string s and a pattern p (which may contain '?' matching any
single character and '*' matching any sequence including empty), return True
if s matches p completely. Uses bottom-up dynamic programming.
"""

def wildcard_match(s: str, p: str) -> bool:
    """Return True if s matches wildcard pattern p."""
    if not isinstance(s, str) or not isinstance(p, str):
        return False
    (m, n) = (len(s), len(p))
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True
    j = 1
    while j < n + 1:
        if p[j - 1] == '*':
            dp[0][j] = dp[0][j - 1]
        j += 1
    i = 1
    while i < m + 1:
        j = 1
        while j < n + 1:
            if p[j - 1] == '*':
                dp[i][j] = dp[i - 1][j] or dp[i][j - 1]
            elif p[j - 1] == '?' or p[j - 1] == s[i - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            j += 1
        i += 1
    return dp[m][n]