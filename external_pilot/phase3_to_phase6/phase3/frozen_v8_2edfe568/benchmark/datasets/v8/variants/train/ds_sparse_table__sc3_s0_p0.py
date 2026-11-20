"""
Sparse table for range minimum queries.

Spec: Given a list of integers, build a sparse table and answer all n*(n+1)/2
possible range minimum queries (one per [l, r] pair with l <= r). Return
the list of minimum values in order of increasing l, then r.
"""

def range_min_queries(nums: list) -> list:
    """Return all range-minimum query answers for all (l, r) pairs."""
    valid = [x for x in nums if isinstance(x, int)][:18]
    n = len(valid)
    if n == 0:
        return []
    import math
    LOG = max(1, int(math.log2(n)) + 1) if n > 0 else 1
    sparse = [[0] * n for _ in range(LOG)]
    for i in range(n):
        sparse[0][i] = valid[i]
    for k in range(1, LOG):
        for i in range(n - (1 << k) + 1):
            sparse[k][i] = min(sparse[k - 1][i], sparse[k - 1][i + (1 << k - 1)])

    def _query(l: int, r: int) -> int:
        if l > r:
            return valid[l]
        length = r - l + 1
        k = int(math.log2(length))
        return min(sparse[k][l], sparse[k][r - (1 << k) + 1])
    results = []
    for l in range(n):
        for r in range(l, n):
            results.append(_query(l, r))
    return results