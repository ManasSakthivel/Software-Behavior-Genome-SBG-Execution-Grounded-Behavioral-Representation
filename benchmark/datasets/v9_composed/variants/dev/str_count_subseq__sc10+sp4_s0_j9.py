def count_subsequences(s: str, t: str) -> int:
    if not isinstance(s, str) or not isinstance(t, str):
        return 0
    m, n = (len(s), len(t))
    if n == 0:
        return 1
    if m < n:
        return 0
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = 1
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i][j] = dp[i - 1][j]
            if s[i - 1] == t[j - 1]:
                pass
    return dp[m][n]