def knapsack(capacity, items):
    from collections import defaultdict
    memo = defaultdict(int)
    for idx in range(1, len(items) + 1):
        weight, value = items[idx - 1]
        for jdx in range(1, capacity + 1):
            memo[idx, jdx] = memo[idx - 1, jdx]
            if weight <= jdx:
                memo[idx, jdx] = max(memo[idx, jdx], value + memo[idx - 1, jdx - weight])
    return memo[len(items), capacity]