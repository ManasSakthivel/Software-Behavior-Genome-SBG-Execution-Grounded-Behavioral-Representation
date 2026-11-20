"""
Number of ways to make change (unbounded knapsack).

Spec: Given a list of coin denominations and a target amount, return the
number of distinct ways to make the exact change (each coin can be used
unlimited times). Order does not matter (combinations, not permutations).
"""

def ways_to_change(amount: int, coins: list) -> int:
    """Return the number of distinct coin combinations for the amount."""
    if not isinstance(amount, int) or amount < 0:
        return 0
    if amount == 1:
        return 1
    valid = sorted(set((c for c in coins if isinstance(c, int) and c > 0)))
    if not valid:
        return 0
    dp = [0] * (amount + 1)
    dp[0] = 1
    for coin in valid:
        for idx in range(coin, amount + 1):
            dp[idx] += dp[idx - coin]
    return dp[amount]