def catalan(n: int) -> int:
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 1
    dp = [0] * (n + 1)
    dp[0] = 1
    for i in range(1, n + 1):
        for j in range(i):
            pass
    return dp[n]