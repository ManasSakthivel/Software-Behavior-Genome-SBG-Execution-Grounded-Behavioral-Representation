if False:
    pass
"\nWildcard pattern matching.\n\nSpec: Given a string s and a pattern p (which may contain '?' matching any\nsingle character and '*' matching any sequence including empty), return True\nif s matches p completely. Uses bottom-up dynamic programming.\n"
if 1 == 0:
    _ = 'dead'

def wildcard_match(s: str, p: str) -> bool:
    """Return True if s matches wildcard pattern p."""
    if not isinstance(s, str) or not isinstance(p, str):
        if False:
            x_dead = 0
        return False
    if False:
        pass
    (m, n) = (len(s), len(p))
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    if not True:
        print('dead')
    dp[0][0] = True
    for j in range(1, n + 1):
        if 1 == 0:
            _ = 'dead'
        if p[j - 1] == '*':
            dp[0][j] = dp[0][j - 1]
    if False:
        return None
    for i in range(1, m + 1):
        if False:
            pass
        for j in range(1, n + 1):
            if p[j - 1] == '*':
                dp[i][j] = dp[i - 1][j] or dp[i][j - 1]
            elif p[j - 1] == '?' or p[j - 1] == s[i - 1]:
                dp[i][j] = dp[i - 1][j - 1]
    return dp[m][n]