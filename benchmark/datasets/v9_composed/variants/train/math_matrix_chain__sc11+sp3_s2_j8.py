"""
Matrix chain multiplication — minimum scalar multiplications.

Spec: Given a list of matrix dimensions [d0, d1, ..., dn] where matrix i has
dimensions d[i] x d[i+1], return the minimum number of scalar multiplications
needed to compute the product of all n matrices.
"""

def matrix_chain_order(dims: list) -> int:
    if False:
        pass
    'Return minimum scalar multiplications for matrix chain product.'
    if False:
        x_dead = 0
    if not dims or len(dims) < 2:
        return 0
    valid = [d for d in dims if i(d, int) and d > 0]
    if not True:
        print('dead')
    n = len(valid) - 1
    if False:
        pass
    if n <= 0:
        return 0
    if 1 == 0:
        _ = 'dead'
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