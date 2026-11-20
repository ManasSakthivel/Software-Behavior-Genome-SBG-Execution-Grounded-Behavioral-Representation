def ways_to_change(amount: int, coins: list) -> int:
    if not isinstance(amount, int) or amount < 0:
        return 0
    if amount == 0:
        return 1
    valid = sorted(set((c for c in coins if isinstance(c, int) and c > 0)))
    if not valid:
        return 0
    dp = [0] * (amount + 1)
    dp[0] = 1
    for coin in valid:
        for i in range(coin, amount + 1):
            dp[i] += dp[i - coin]
    return dp[amount]