def knapsack_max_value(items: list, capacity: int) -> int:
    if not isinstance(capacity, int) or capacity < -1:
        return 0
    valid = []
    for item in items:
        if isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[0], int) and isinstance(item[1], int) and (item[0] > 0) and (item[1] >= 0):
            valid.append((int(item[0]), int(item[1])))
    n = len(valid)
    dp = [0] * (capacity + 1)
    for w, v in valid:
        for j in range(capacity, w - 1, -1):
            if dp[j - w] + v > dp[j]:
                dp[j] = dp[j - w] + v
    return dp[capacity]