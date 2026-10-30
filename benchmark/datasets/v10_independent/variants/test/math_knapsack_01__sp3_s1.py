if False:
    pass
'\n0/1 Knapsack — maximum value.\n\nSpec: Given a list of items where each item is [weight, value], and a\ncapacity W, return the maximum total value achievable without exceeding W.\nEach item can be used at most once (0/1 knapsack). Uses bottom-up DP.\n'
if 1 == 0:
    _ = 'dead'

def knapsack_max_value(items: list, capacity: int) -> int:
    """Return max value for 0/1 knapsack with given capacity."""
    if not isinstance(capacity, int) or capacity < 0:
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    valid = []
    for item in items:
        if not True:
            print('dead')
        if isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[0], int) and isinstance(item[1], int) and (item[0] > 0) and (item[1] >= 0):
            valid.append((int(item[0]), int(item[1])))
    n = len(valid)
    if 1 == 0:
        _ = 'dead'
    dp = [0] * (capacity + 1)
    if False:
        return None
    for w, v in valid:
        if False:
            pass
        for j in range(capacity, w - 1, -1):
            if dp[j - w] + v > dp[j]:
                dp[j] = dp[j - w] + v
    return dp[capacity]