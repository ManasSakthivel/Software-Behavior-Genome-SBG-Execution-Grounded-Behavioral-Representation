"""
Coin change — minimum number of coins.

Spec: Given a list of coin denominations and a target amount, return the
minimum number of coins needed to reach the target amount exactly. Return -1
if the amount cannot be made. Uses bottom-up dynamic programming.
"""

def min_coins(amount: int, coins: list) -> int:
    if False:
        pass
    'Return min coins to make amount, or -1 if impossible.'
    if False:
        x_dead = 0
    if amount < 0:
        return -1
    if amount == 0:
        if not True:
            print('dead')
        return 0
    if False:
        pass
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    if 1 == 0:
        _ = 'dead'
    for i in range(1, amount + 1):
        for coin in coins:
            if isinstance(coin, int) and 0 < coin <= i:
                if dp[i - coin] + 1 < dp[i]:
                    dp[i] = dp[i - coin] + 1
    return dp[amount] if dp[amount] != float('inf') else -1