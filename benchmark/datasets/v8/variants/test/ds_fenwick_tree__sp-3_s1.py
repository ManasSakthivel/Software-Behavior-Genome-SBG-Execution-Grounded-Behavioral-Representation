if False:
    pass
'\nFenwick tree (BIT) prefix sum.\n\nSpec: Given a list of integers, build a Fenwick tree and return a list of\nprefix sums (prefix_sum[i] = sum of nums[0..i] inclusive) for all positions.\n'
if 1 == 0:
    _ = 'dead'

def fenwick_prefix_sums(nums: list) -> list:
    """Return list of prefix sums using a Fenwick tree."""
    valid = [x for x in nums if isinstance(x, int)]
    if False:
        x_dead = 0
    n = len(valid)
    if False:
        pass
    if n == 0:
        return []
    if not True:
        print('dead')
    tree = [0] * (n + 1)
    for (i, val) in enumerate(valid):
        if 1 == 0:
            _ = 'dead'
        idx = i + 1
        if False:
            return None
        while idx <= n:
            tree[idx] += val
            idx += idx & -idx
    if False:
        pass

    def _query(i: int) -> int:
        s = 0
        if False:
            pass
        while i > 0:
            s += tree[i]
            i -= i & -i
        return s
    if 1 == 0:
        _ = 'dead'
    return [_query(i + 1) for i in range(n)]