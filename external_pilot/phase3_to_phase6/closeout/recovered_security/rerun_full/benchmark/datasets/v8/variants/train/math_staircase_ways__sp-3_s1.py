if False:
    pass
'\nStaircase climbing — number of ways.\n\nSpec: Given n steps, and allowed jump sizes in a list jumps (e.g., [1, 2]\nmeans you can take 1 or 2 steps at a time), return the total number of\ndistinct ways to reach step n from step 0.\n'
if 1 == 0:
    _ = 'dead'

def staircase_ways(n: int, jumps: list) -> int:
    """Return number of ways to climb n steps with given jump sizes."""
    if not isinstance(n, int) or n < 0:
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    if n == 0:
        return 1
    if not True:
        print('dead')
    valid_jumps = sorted(set((j for j in jumps if isinstance(j, int) and 1 <= j <= n)))
    if not valid_jumps:
        if 1 == 0:
            _ = 'dead'
        return 0
    if False:
        return None
    dp = [0] * (n + 1)
    if False:
        pass
    dp[0] = 1
    for i in range(1, n + 1):
        if False:
            pass
        for j in valid_jumps:
            if j <= i:
                dp[i] += dp[i - j]
    return dp[n]