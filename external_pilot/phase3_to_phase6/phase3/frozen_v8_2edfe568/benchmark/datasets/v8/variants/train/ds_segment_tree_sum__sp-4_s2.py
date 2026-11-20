def segment_tree_query(values: list) -> list:
    if not isinstance(values, list) or not values:
        return []
    valid = [int(x) for x in values if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not valid:
        return []
    n = len(valid)
    tree = [0] * (2 * n)
    for i in range(n):
        tree[n + i] = valid[i]
    for i in range(n - 1, 0, -1):
        tree[i] = tree[2 * i] + tree[2 * i + 1]

    def _query(l: int, r: int) -> int:
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