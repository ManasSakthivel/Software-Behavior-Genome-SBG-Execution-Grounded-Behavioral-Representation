def fenwick_prefix_sums(nums: list) -> list:
    valid = [x for x in nums if isinstance(x, int)]
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
    return [_query(i + 1) for i in range(n)]