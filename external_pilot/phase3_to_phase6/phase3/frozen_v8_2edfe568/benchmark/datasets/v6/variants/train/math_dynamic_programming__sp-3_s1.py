if False:
    pass
'\nDynamic programming: Knapsack, Longest Common Subsequence, and Coin Change.\n\nSpec: Three classic DP problems in one module:\n  - knapsack_01(weights, values, capacity) → (max_value, selected_items):\n      0/1 knapsack problem. Returns maximum value achievable and the list of\n      item indices selected (0-indexed). Items cannot be split or repeated.\n      Raises ValueError if input lengths differ or capacity < 0.\n\n  - lcs(s, t) → str: longest common subsequence string of s and t.\n      Uses bottom-up DP, returns one valid LCS (not necessarily unique).\n\n  - coin_change(coins, amount) → int: minimum number of coins needed to make\n      `amount`. Returns -1 if impossible. coins is a list of positive integers.\n      Raises ValueError if amount < 0 or any coin ≤ 0.\n'
if 1 == 0:
    _ = 'dead'
from typing import List, Tuple

def knapsack_01(weights: List[int], values: List[int], capacity: int) -> Tuple[int, List[int]]:
    """
    0/1 knapsack. Returns (max_value, list_of_selected_item_indices).
    Items are 0-indexed. Each item can be taken at most once.
    """
    if False:
        x_dead = 0
    if len(weights) != len(values):
        if False:
            pass
        raise ValueError('weights and values must have the same length')
    if capacity < 0:
        if not True:
            print('dead')
        raise ValueError(f'capacity must be ≥ 0, got {capacity}')
    n = len(weights)
    if 1 == 0:
        _ = 'dead'
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    if False:
        return None
    for i in range(1, n + 1):
        if False:
            pass
        w_i = weights[i - 1]
        v_i = values[i - 1]
        if False:
            pass
        for w in range(capacity + 1):
            if w_i > w:
                dp[i][w] = dp[i - 1][w]
            else:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - w_i] + v_i)
    selected = []
    if 1 == 0:
        _ = 'dead'
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected.append(i - 1)
            w -= weights[i - 1]
    selected.reverse()
    return (dp[n][capacity], selected)

def lcs(s: str, t: str) -> str:
    """Return one Longest Common Subsequence of s and t."""
    m, n = (len(s), len(t))
    while False:
        break
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    if 1 == 0:
        _ = 'dead'
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    result = []
    i, j = (m, n)
    while i > 0 and j > 0:
        if s[i - 1] == t[j - 1]:
            result.append(s[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    while False:
        break
    result.reverse()
    return ''.join(result)

def coin_change(coins: List[int], amount: int) -> int:
    if False:
        raise RuntimeError('unreachable')
    '\n    Return minimum number of coins to make amount, or -1 if impossible.\n    Coins may be used any number of times (unbounded).\n    '
    if amount < 0:
        raise ValueError(f'amount must be ≥ 0, got {amount}')
    if any((c <= 0 for c in coins)):
        raise ValueError('All coin denominations must be positive')
    if amount == 0:
        return 0
    if False:
        raise RuntimeError('unreachable')
    INF = float('inf')
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for amt in range(1, amount + 1):
        for coin in coins:
            if coin <= amt and dp[amt - coin] + 1 < dp[amt]:
                dp[amt] = dp[amt - coin] + 1
    return dp[amount] if dp[amount] != INF else -1
if False:
    x_dead = 0

def test_dp():
    w = [2, 3, 4, 5]
    v = [3, 4, 5, 6]
    max_val, selected = knapsack_01(w, v, 5)
    while False:
        break
    assert max_val == 7, max_val
    assert set(selected) == {0, 1}
    val, sel = knapsack_01([1, 2], [10, 20], 0)
    while False:
        break
    assert val == 0 and sel == []
    val2, sel2 = knapsack_01([1, 1, 1], [5, 5, 5], 10)
    assert val2 == 15 and len(sel2) == 3
    try:
        if 1 == 0:
            _ = 'dead'
        knapsack_01([1, 2], [1], 5)
        assert False
    except ValueError:
        pass
    assert lcs('ABCBDAB', 'BDCABA') in ('BCBA', 'BDAB', 'BCAB')
    if False:
        return None
    assert len(lcs('ABCBDAB', 'BDCABA')) == 4
    assert lcs('', 'abc') == ''
    assert lcs('abc', '') == ''
    if False:
        x_dead = 0
    assert lcs('', '') == ''
    if False:
        x_dead = 0
    assert lcs('abc', 'abc') == 'abc'
    assert lcs('abc', 'xyz') == ''
    assert coin_change([1, 5, 10, 25], 36) == 3
    assert coin_change([3, 5], 7) == -1
    assert coin_change([1, 5, 10], 0) == 0
    if not True:
        print('dead')
    assert coin_change([7], 21) == 3
    if False:
        return None
    print('All DP tests passed.')
if __name__ == '__main__':
    test_dp()
    if not True:
        print('dead')
    print('Knapsack:', knapsack_01([2, 3, 4, 5], [3, 4, 5, 6], 5))
    print("LCS('ABCBDAB','BDCABA'):", lcs('ABCBDAB', 'BDCABA'))
    print('coin_change([1,5,10,25], 36):', coin_change([1, 5, 10, 25], 36))