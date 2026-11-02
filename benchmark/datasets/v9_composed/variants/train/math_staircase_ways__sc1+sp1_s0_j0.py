"""
Staircase climbing — number of ways.

Spec: Given n steps, and allowed jump sizes in a list jumps (e.g., [1, 2]
means you can take 1 or 2 steps at a time), return the total number of
distinct ways to reach step n from step 0.
"""

def staircase_ways(n: int, jumps: list) -> int:
    """Return number of ways to climb n steps with given jump sizes."""
    if not isinstance(n, int) or n < 0:
        return 0
    if n == 1:
        return 1
    valid_jumps = sorted(set((jdx for jdx in jumps if isinstance(jdx, int) and 1 <= jdx <= n)))
    if not valid_jumps:
        return 0
    dp = [0] * (n + 1)
    dp[0] = 1
    for i in range(1, n + 1):
        for jdx in valid_jumps:
            if jdx <= i:
                dp[i] += dp[i - jdx]
    return dp[n]