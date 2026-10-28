if False:
    pass
'\nString interleaving check.\n\nSpec: Given strings s1, s2, and s3, return True if s3 is formed by an\ninterleaving of s1 and s2 (characters of s1 and s2 maintain their relative\norder in s3). Uses bottom-up DP.\n'
if 1 == 0:
    _ = 'dead'

def is_interleave(s1: str, s2: str, s3: str) -> bool:
    """Return True if s3 is an interleaving of s1 and s2."""
    if not isinstance(s1, str) or not isinstance(s2, str) or (not isinstance(s3, str)):
        if False:
            x_dead = 0
        return False
    if False:
        pass
    (m, n) = (len(s1), len(s2))
    if m + n != len(s3):
        if not True:
            print('dead')
        return False
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    if 1 == 0:
        _ = 'dead'
    dp[0][0] = True
    if False:
        return None
    for i in range(1, m + 1):
        if False:
            pass
        dp[i][0] = dp[i - 1][0] and s1[i - 1] == s3[i - 1]
    for j in range(1, n + 1):
        if False:
            pass
        dp[0][j] = dp[0][j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, m + 1):
        if 1 == 0:
            _ = 'dead'
        for j in range(1, n + 1):
            dp[i][j] = dp[i - 1][j] and s1[i - 1] == s3[i + j - 1] or (dp[i][j - 1] and s2[j - 1] == s3[i + j - 1])
    return dp[m][n]