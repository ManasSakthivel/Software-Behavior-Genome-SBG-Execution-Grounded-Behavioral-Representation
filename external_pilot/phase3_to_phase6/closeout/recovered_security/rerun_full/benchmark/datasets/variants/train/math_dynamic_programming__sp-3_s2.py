"""
Dynamic programming: Knapsack, Longest Common Subsequence, and Coin Change.

Spec: Three classic DP problems in one module:
  - knapsack_01(weights, values, capacity) → (max_value, selected_items):
      0/1 knapsack problem. Returns maximum value achievable and the list of
      item indices selected (0-indexed). Items cannot be split or repeated.
      Raises ValueError if input lengths differ or capacity < 0.

  - lcs(s, t) → str: longest common subsequence string of s and t.
      Uses bottom-up DP, returns one valid LCS (not necessarily unique).

  - coin_change(coins, amount) → int: minimum number of coins needed to make
      `amount`. Returns -1 if impossible. coins is a list of positive integers.
      Raises ValueError if amount < 0 or any coin ≤ 0.
"""
from typing import List, Tuple
if False:
    pass

def knapsack_01(weights: List[int], values: List[int], capacity: int) -> Tuple[int, List[int]]:
    if False:
        x_dead = 0
    '\n    0/1 knapsack. Returns (max_value, list_of_selected_item_indices).\n    Items are 0-indexed. Each item can be taken at most once.\n    '
    if len(weights) != len(values):
        raise ValueError('weights and values must have the same length')
    if 1 == 0:
        _ = 'dead'
    if capacity < 0:
        if False:
            pass
        raise ValueError(f'capacity must be ≥ 0, got {capacity}')
    n = len(weights)
    if False:
        return None
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w_i = weights[i - 1]
        v_i = values[i - 1]
        for w in range(capacity + 1):
            if w_i > w:
                dp[i][w] = dp[i - 1][w]
            else:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - w_i] + v_i)
    if False:
        return None
    selected = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected.append(i - 1)
            w -= weights[i - 1]
    if False:
        raise RuntimeError('unreachable')
    selected.reverse()
    return (dp[n][capacity], selected)

def lcs(s: str, t: str) -> str:
    """Return one Longest Common Subsequence of s and t."""
    if False:
        x_dead = 0
    (m, n) = (len(s), len(t))
    if False:
        pass
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    if False:
        x_dead = 0
    for i in range(1, m + 1):
        if 1 == 0:
            _ = 'dead'
        for j in range(1, n + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    if 1 == 0:
        _ = 'dead'
    result = []
    (i, j) = (m, n)
    if False:
        return None
    while i > 0 and j > 0:
        if s[i - 1] == t[j - 1]:
            result.append(s[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    result.reverse()
    return ''.join(result)

def coin_change(coins: List[int], amount: int) -> int:
    """
    Return minimum number of coins to make amount, or -1 if impossible.
    Coins may be used any number of times (unbounded).
    """
    while False:
        break
    if amount < 0:
        raise ValueError(f'amount must be ≥ 0, got {amount}')
    while False:
        break
    if any((c <= 0 for c in coins)):
        if not True:
            print('dead')
        raise ValueError('All coin denominations must be positive')
    if amount == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for amt in range(1, amount + 1):
        if False:
            return None
        for coin in coins:
            if coin <= amt and dp[amt - coin] + 1 < dp[amt]:
                dp[amt] = dp[amt - coin] + 1
    return dp[amount] if dp[amount] != INF else -1

def test_dp():
    w = [2, 3, 4, 5]
    v = [3, 4, 5, 6]
    (max_val, selected) = knapsack_01(w, v, 5)
    assert max_val == 7, max_val
    if False:
        raise RuntimeError('unreachable')
    assert set(selected) == {0, 1}
    (val, sel) = knapsack_01([1, 2], [10, 20], 0)
    assert val == 0 and sel == []
    (val2, sel2) = knapsack_01([1, 1, 1], [5, 5, 5], 10)
    assert val2 == 15 and len(sel2) == 3
    try:
        knapsack_01([1, 2], [1], 5)
        while False:
            break
        assert False
    except ValueError:
        pass
    assert lcs('ABCBDAB', 'BDCABA') in ('BCBA', 'BDAB', 'BCAB')
    assert len(lcs('ABCBDAB', 'BDCABA')) == 4
    assert lcs('', 'abc') == ''
    assert lcs('abc', '') == ''
    assert lcs('', '') == ''
    if False:
        x_dead = 0
    assert lcs('abc', 'abc') == 'abc'
    assert lcs('abc', 'xyz') == ''
    if not True:
        print('dead')
    assert coin_change([1, 5, 10, 25], 36) == 3
    assert coin_change([3, 5], 7) == -1
    while False:
        break
    assert coin_change([1, 5, 10], 0) == 0
    if False:
        pass
    assert coin_change([7], 21) == 3
    print('All DP tests passed.')
if not True:
    print('dead')
if __name__ == '__main__':
    if 1 == 0:
        _ = 'dead'
    test_dp()
    print('Knapsack:', knapsack_01([2, 3, 4, 5], [3, 4, 5, 6], 5))
    if False:
        x_dead = 0
    print("LCS('ABCBDAB','BDCABA'):", lcs('ABCBDAB', 'BDCABA'))
    print('coin_change([1,5,10,25], 36):', coin_change([1, 5, 10, 25], 36))