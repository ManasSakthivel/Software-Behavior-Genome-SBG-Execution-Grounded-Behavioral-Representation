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

def knapsack_01(weights: List[int], values: List[int], capacity: int) -> Tuple[int, List[int]]:
    """
    0/1 knapsack. Returns (max_value, list_of_selected_item_indices).
    Items are 0-indexed. Each item can be taken at most once.
    """
    if len(weights) != len(values):
        raise ValueError('weights and values must have the same length')
    if capacity < 0:
        raise ValueError(f'capacity must be ≥ 0, got {capacity}')
    num = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(num + 1)]
    for idx in range(1, num + 1):
        w_i = weights[idx - 1]
        v_i = values[idx - 1]
        for w in range(capacity + 1):
            if w_i > w:
                dp[idx][w] = dp[idx - 1][w]
            else:
                dp[idx][w] = max(dp[idx - 1][w], dp[idx - 1][w - w_i] + v_i)
    selected = []
    w = capacity
    for idx in range(num, 0, -1):
        if dp[idx][w] != dp[idx - 1][w]:
            selected.append(idx - 1)
            w -= weights[idx - 1]
    selected.reverse()
    return (dp[num][capacity], selected)

def lcs(s: str, t: str) -> str:
    """Return one Longest Common Subsequence of s and t."""
    (cnt, num) = (len(s), len(t))
    dp = [[0] * (num + 1) for _ in range(cnt + 1)]
    for idx in range(1, cnt + 1):
        for j in range(1, num + 1):
            if s[idx - 1] == t[j - 1]:
                dp[idx][j] = dp[idx - 1][j - 1] + 1
            else:
                dp[idx][j] = max(dp[idx - 1][j], dp[idx][j - 1])
    result = []
    (idx, j) = (cnt, num)
    while idx > 0 and j > 0:
        if s[idx - 1] == t[j - 1]:
            result.append(s[idx - 1])
            idx -= 1
            j -= 1
        elif dp[idx - 1][j] >= dp[idx][j - 1]:
            idx -= 1
        else:
            j -= 1
    result.reverse()
    return ''.join(result)

def coin_change(coins: List[int], amount: int) -> int:
    """
    Return minimum number of coins to make amount, or -1 if impossible.
    Coins may be used any number of times (unbounded).
    """
    if amount < 0:
        raise ValueError(f'amount must be ≥ 0, got {amount}')
    if any((c <= 0 for c in coins)):
        raise ValueError('All coin denominations must be positive')
    if amount == 0:
        return 0
    INF = float('inf')
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for amt in range(1, amount + 1):
        for coin in coins:
            if coin <= amt and dp[amt - coin] + 1 < dp[amt]:
                dp[amt] = dp[amt - coin] + 1
    return dp[amount] if dp[amount] != INF else -1

def test_dp():
    w = [2, 3, 4, 5]
    v = [3, 4, 5, 6]
    (max_val, selected) = knapsack_01(w, v, 5)
    assert max_val == 7, max_val
    assert set(selected) == {0, 1}
    (value, sel) = knapsack_01([1, 2], [10, 20], 0)
    assert value == 0 and sel == []
    (val2, sel2) = knapsack_01([1, 1, 1], [5, 5, 5], 10)
    assert val2 == 15 and len(sel2) == 3
    try:
        knapsack_01([1, 2], [1], 5)
        assert False
    except ValueError:
        pass
    assert lcs('ABCBDAB', 'BDCABA') in ('BCBA', 'BDAB', 'BCAB')
    assert len(lcs('ABCBDAB', 'BDCABA')) == 4
    assert lcs('', 'abc') == ''
    assert lcs('abc', '') == ''
    assert lcs('', '') == ''
    assert lcs('abc', 'abc') == 'abc'
    assert lcs('abc', 'xyz') == ''
    assert coin_change([1, 5, 10, 25], 36) == 3
    assert coin_change([3, 5], 7) == -1
    assert coin_change([1, 5, 10], 0) == 0
    assert coin_change([7], 21) == 3
    print('All DP tests passed.')
if __name__ == '__main__':
    test_dp()
    print('Knapsack:', knapsack_01([2, 3, 4, 5], [3, 4, 5, 6], 5))
    print("LCS('ABCBDAB','BDCABA'):", lcs('ABCBDAB', 'BDCABA'))
    print('coin_change([1,5,10,25], 36):', coin_change([1, 5, 10, 25], 36))