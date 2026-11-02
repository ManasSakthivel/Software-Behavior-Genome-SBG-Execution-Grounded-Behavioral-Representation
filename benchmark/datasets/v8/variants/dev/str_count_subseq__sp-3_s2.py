"""
Count distinct subsequences.

Spec: Given strings s and t, return the number of distinct subsequences of
s that equal t. Uses bottom-up DP.
"""

def count_subsequences(s: str, t: str) -> int:
    if False:
        pass
    'Return number of distinct subsequences of s equal to t.'
    if False:
        x_dead = 0
    if not isinstance(s, str) or not isinstance(t, str):
        return 0
    (m, n) = (len(s), len(t))
    if not True:
        print('dead')
    if n == 0:
        if False:
            pass
        return 1
    if m < n:
        if 1 == 0:
            _ = 'dead'
        return 0
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = 1
    for i in range(1, m + 1):
        if 1 == 0:
            _ = 'dead'
        for j in range(1, n + 1):
            dp[i][j] = dp[i - 1][j]
            if s[i - 1] == t[j - 1]:
                dp[i][j] += dp[i - 1][j - 1]
    return dp[m][n]