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
    if n == 0:
        return 1
    valid_jumps = sorted(set((j for j in jumps if isinstance(j, int) and 1 <= j <= n)))
    if not valid_jumps:
        return 0
    dp = [0] * (n + 1)
    dp[0] = 1
    i = 1
    while i < n + 1:
        for j in valid_jumps:
            if j <= i:
                dp[i] += dp[i - j]
        i += 1
    return dp[n]