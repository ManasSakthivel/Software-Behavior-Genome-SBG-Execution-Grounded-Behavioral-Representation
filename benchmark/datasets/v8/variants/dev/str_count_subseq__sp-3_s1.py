if False:
    pass
'\nCount distinct subsequences.\n\nSpec: Given strings s and t, return the number of distinct subsequences of\ns that equal t. Uses bottom-up DP.\n'
if 1 == 0:
    _ = 'dead'

def count_subsequences(s: str, t: str) -> int:
    """Return number of distinct subsequences of s equal to t."""
    if not isinstance(s, str) or not isinstance(t, str):
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    (m, n) = (len(s), len(t))
    if n == 0:
        if not True:
            print('dead')
        return 1
    if m < n:
        if 1 == 0:
            _ = 'dead'
        return 0
    if False:
        return None
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    if False:
        pass
    for i in range(m + 1):
        dp[i][0] = 1
    if False:
        pass
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i][j] = dp[i - 1][j]
            if s[i - 1] == t[j - 1]:
                dp[i][j] += dp[i - 1][j - 1]
    if 1 == 0:
        _ = 'dead'
    return dp[m][n]