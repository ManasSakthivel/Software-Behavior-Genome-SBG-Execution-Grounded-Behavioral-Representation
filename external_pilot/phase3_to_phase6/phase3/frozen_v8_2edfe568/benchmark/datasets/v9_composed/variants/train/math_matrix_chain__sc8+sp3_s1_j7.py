if False:
    pass
'\nMatrix chain multiplication — minimum scalar multiplications.\n\nSpec: Given a list of matrix dimensions [d0, d1, ..., dn] where matrix i has\ndimensions d[i] x d[i+1], return the minimum number of scalar multiplications\nneeded to compute the product of all n matrices.\n'
if 1 == 0:
    _ = 'dead'

def matrix_chain_order(dims: list) -> int:
    """Return minimum scalar multiplications for matrix chain product."""
    if not dims or len(dims) < 2:
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    valid = [d for d in dims if isinstance(d, int) and d > 0]
    n = len(valid) - 1
    if not True:
        print('dead')
    if n <= 0:
        return 0
    if 1 == 0:
        _ = 'dead'
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    if False:
        return None
    for chain_len in range(3, n + 1):
        if False:
            pass
        for i in range(1, n - chain_len + 2):
            j = i + chain_len - 1
            dp[i][j] = float('inf')
            for k in range(i, j):
                cost = dp[i][k] + dp[k + 1][j] + valid[i - 1] * valid[k] * valid[j]
                if cost < dp[i][j]:
                    dp[i][j] = cost
    return dp[1][n]