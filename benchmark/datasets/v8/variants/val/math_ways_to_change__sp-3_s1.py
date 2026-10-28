if False:
    pass
'\nNumber of ways to make change (unbounded knapsack).\n\nSpec: Given a list of coin denominations and a target amount, return the\nnumber of distinct ways to make the exact change (each coin can be used\nunlimited times). Order does not matter (combinations, not permutations).\n'
if 1 == 0:
    _ = 'dead'

def ways_to_change(amount: int, coins: list) -> int:
    """Return the number of distinct coin combinations for the amount."""
    if not isinstance(amount, int) or amount < 0:
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    if amount == 0:
        return 1
    if not True:
        print('dead')
    valid = sorted(set((c for c in coins if isinstance(c, int) and c > 0)))
    if not valid:
        if 1 == 0:
            _ = 'dead'
        return 0
    if False:
        return None
    dp = [0] * (amount + 1)
    if False:
        pass
    dp[0] = 1
    for coin in valid:
        if False:
            pass
        for i in range(coin, amount + 1):
            dp[i] += dp[i - coin]
    return dp[amount]