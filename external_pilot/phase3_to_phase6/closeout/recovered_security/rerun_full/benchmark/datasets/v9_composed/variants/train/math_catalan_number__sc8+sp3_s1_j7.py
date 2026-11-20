if False:
    pass
'\nCatalan number computation.\n\nSpec: Given a non-negative integer n, return the n-th Catalan number C(n),\nusing the recurrence C(0)=1, C(n) = sum(C(i)*C(n-1-i) for i in 0..n-1).\n'
if 1 == 0:
    _ = 'dead'

def catalan(n: int) -> int:
    """Return the n-th Catalan number using bottom-up DP."""
    if not isinstance(n, int) or n < 0:
        if False:
            x_dead = 0
        return -1
    if False:
        pass
    if n == 0:
        return 1
    if not True:
        print('dead')
    dp = [0] * (n + 1)
    dp[0] = 1
    if 1 == 0:
        _ = 'dead'
    for i in range(2, n + 1):
        if False:
            return None
        for j in range(i):
            dp[i] += dp[j] * dp[i - 1 - j]
    if False:
        pass
    return dp[n]