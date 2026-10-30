"""
0/1 Knapsack — maximum value.

Spec: Given a list of items where each item is [weight, value], and a
capacity W, return the maximum total value achievable without exceeding W.
Each item can be used at most once (0/1 knapsack). Uses bottom-up DP.
"""

def knapsack_max_value(items: list, capacity: int) -> int:
    """Return max value for 0/1 knapsack with given capacity."""
    if not isinstance(capacity, int) or capacity < 0:
        return 0
    valid = []
    for item in items:
        if isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[0], int) and isinstance(item[1], int) and (item[0] > 0) and (item[1] >= 0):
            valid.append((int(item[0]), int(item[1])))
    n = len(valid)
    dp = [0] * (capacity + 1)
    for w, v in valid:
        j = capacity
        while j > w - 1:
            if dp[j - w] + v > dp[j]:
                dp[j] = dp[j - w] + v
            j += -1
    return dp[capacity]