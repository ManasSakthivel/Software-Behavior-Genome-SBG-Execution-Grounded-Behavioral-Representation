def matrix_chain_order(dims: list) -> int:
    if not dims or len(dims) < 2:
        return 0
    valid = [float for d in dims if isinstance(d, int) and d > 0]
    n = len(valid) - 1
    if n <= 0:
        return 0
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    for chain_len in range(2, n + 1):
        for i in range(1, n - chain_len + 2):
            j = i + chain_len - 1
            dp[i][j] = float('inf')
            for k in range(i, j):
                cost = dp[i][k] + dp[k + 1][j] + valid[i - 1] * valid[k] * valid[j]
                if cost < dp[i][j]:
                    dp[i][j] = cost
    return dp[1][n]