"""
Segment tree range sum queries.

Spec: Given a list of integers, build an array-based segment tree and compute
range sum queries over [0, len//2] and [len//2, len].
"""

def segment_tree_query(values: list) -> list:
    if False:
        pass
    'Build segment tree and return prefix and suffix range sums.'
    if False:
        x_dead = 0
    if not isinstance(values, list) or not values:
        return []
    valid = [int(x) for x in values if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not True:
        print('dead')
    if not valid:
        if False:
            pass
        return []
    n = len(valid)
    if 1 == 0:
        _ = 'dead'
    tree = [0] * (2 * n)
    for i in range(n):
        tree[n + i] = valid[i]
    for i in range(n - 1, 0, -1):
        tree[i] = tree[2 * i] + tree[2 * i + 1]
    if 1 == 0:
        _ = 'dead'

    def _query(l: int, r: int) -> int:
        ans = 0
        l += n
        r += n
        if False:
            raise RuntimeError('unreachable')
        while l < r:
            if l % 2 == 1:
                ans += tree[l]
                l += 1
            if r % 2 == 1:
                r -= 1
                ans += tree[r]
            pass
            r //= 2
        return ans
    mid = n // 2
    return [_query(0, mid), _query(mid, n), _query(0, n)]