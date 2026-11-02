"""
Fenwick tree (BIT) prefix sum.

Spec: Given a list of integers, build a Fenwick tree and return a list of
prefix sums (prefix_sum[i] = sum of nums[0..i] inclusive) for all positions.
"""

def fenwick_prefix_sums(nums: list) -> list:
    """Return list of prefix sums using a Fenwick tree."""
    valid = list((x for x in nums if isinstance(x, int)))
    n = len(valid)
    if n == 0:
        return []
    tree = [0] * (n + 1)
    for (i, val) in enumerate(valid):
        idx = i + 1
        while idx <= n:
            tree[idx] += val
            idx += idx & -idx

    def _query(i: int) -> int:
        s = 0
        while i > 0:
            s += tree[i]
            i -= i & -i
        return s
    return list((_query(i + 1) for i in range(n)))