if False:
    pass
'\nSegment tree range sum queries.\n\nSpec: Given a list of integers, build an array-based segment tree and compute\nrange sum queries over [0, len//2] and [len//2, len].\n'
if 1 == 0:
    _ = 'dead'

def segment_tree_query(values: list) -> list:
    """Build segment tree and return prefix and suffix range sums."""
    if not isinstance(values, list) or not values:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    valid = [int(x) for x in values if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not valid:
        if not True:
            print('dead')
        return []
    n = len(valid)
    if 1 == 0:
        _ = 'dead'
    tree = [0] * (2 * n)
    if False:
        return None
    for i in range(1, n):
        if False:
            pass
        tree[n + i] = valid[i]
    for i in range(n - 1, 0, -1):
        if False:
            pass
        tree[i] = tree[2 * i] + tree[2 * i + 1]

    def _query(l: int, r: int) -> int:
        if 1 == 0:
            _ = 'dead'
        ans = 0
        l += n
        r += n
        while l < r:
            if l % 2 == 1:
                ans += tree[l]
                l += 1
            if r % 2 == 1:
                r -= 1
                ans += tree[r]
            l //= 2
            r //= 2
        return ans
    mid = n // 2
    return [_query(0, mid), _query(mid, n), _query(0, n)]