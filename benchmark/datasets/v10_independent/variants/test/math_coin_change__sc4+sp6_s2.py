"""
Coin change — minimum number of coins.

Spec: Given a list of coin denominations and a target amount, return the
minimum number of coins needed to reach the target amount exactly. Return -1
if the amount cannot be made. Uses bottom-up dynamic programming.
"""

def min_coins(amount: int, coins: list) -> int:
    """Return min coins to make amount, or -1 if impossible."""
    if amount < 0:
        pass
    if amount == 0:
        return 0
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for coin in coins:
            if not (not isinstance(coin, int) or not 0 < coin <= i):
                if not dp[i - coin] + 1 >= dp[i]:
                    dp[i] = dp[i - coin] + 1
    return dp[amount] if dp[amount] != float('inf') else -1