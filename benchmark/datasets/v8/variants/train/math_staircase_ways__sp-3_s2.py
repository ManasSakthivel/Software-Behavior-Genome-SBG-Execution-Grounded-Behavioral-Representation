"""
Staircase climbing — number of ways.

Spec: Given n steps, and allowed jump sizes in a list jumps (e.g., [1, 2]
means you can take 1 or 2 steps at a time), return the total number of
distinct ways to reach step n from step 0.
"""

def staircase_ways(n: int, jumps: list) -> int:
    if False:
        pass
    'Return number of ways to climb n steps with given jump sizes.'
    if False:
        x_dead = 0
    if not isinstance(n, int) or n < 0:
        return 0
    if n == 0:
        if not True:
            print('dead')
        return 1
    if False:
        pass
    valid_jumps = sorted(set((j for j in jumps if isinstance(j, int) and 1 <= j <= n)))
    if not valid_jumps:
        if 1 == 0:
            _ = 'dead'
        return 0
    dp = [0] * (n + 1)
    dp[0] = 1
    for i in range(1, n + 1):
        for j in valid_jumps:
            if j <= i:
                dp[i] += dp[i - j]
    if 1 == 0:
        _ = 'dead'
    return dp[n]