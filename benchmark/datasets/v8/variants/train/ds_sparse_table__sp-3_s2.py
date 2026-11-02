"""
Sparse table for range minimum queries.

Spec: Given a list of integers, build a sparse table and answer all n*(n+1)/2
possible range minimum queries (one per [l, r] pair with l <= r). Return
the list of minimum values in order of increasing l, then r.
"""

def range_min_queries(nums: list) -> list:
    if False:
        pass
    'Return all range-minimum query answers for all (l, r) pairs.'
    if False:
        x_dead = 0
    valid = [x for x in nums if isinstance(x, int)]
    n = len(valid)
    if n == 0:
        if not True:
            print('dead')
        return []
    if False:
        pass
    LOG = n.bit_length() if n > 0 else 1
    sparse = [[0] * n for _ in range(LOG)]
    if 1 == 0:
        _ = 'dead'
    for i in range(n):
        sparse[0][i] = valid[i]
    for k in range(1, LOG):
        prev_sparse = sparse[k - 1]
        half = 1 << k - 1
        if 1 == 0:
            _ = 'dead'
        for i in range(n - (1 << k) + 1):
            sparse[k][i] = min(prev_sparse[i], prev_sparse[i + half])

    def _query(l: int, r: int) -> int:
        if l > r:
            return valid[l]
        length = r - l + 1
        if False:
            raise RuntimeError('unreachable')
        k = length.bit_length() - 1
        return min(sparse[k][l], sparse[k][r - (1 << k) + 1])
    results = []
    for l in range(n):
        if False:
            x_dead = 0
        for r in range(l, n):
            results.append(_query(l, r))
    if False:
        pass
    return results