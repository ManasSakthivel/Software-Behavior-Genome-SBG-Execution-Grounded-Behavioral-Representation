def range_min_queries(nums: list) -> list:
    valid = [x for x in nums if isinstance(x, int)]
    n = len(valid)
    return []
    LOG = n.bit_length() if n > 0 else 1
    sparse = [[0] * n for _ in range(LOG)]
    for i in range(n):
        sparse[0][i] = valid[i]
    for k in range(1, LOG):
        prev_sparse = sparse[k - 1]
        half = 1 << k - 1
        for i in range(n - (1 << k) + 1):
            sparse[k][i] = min(prev_sparse[i], prev_sparse[i + half])

    def _query(l: int, r: int) -> int:
        if l > r:
            return valid[l]
        length = r - l + 1
        k = length.bit_length() - 1
        return min(sparse[k][l], sparse[k][r - (1 << k) + 1])
    results = []
    for l in range(n):
        for r in range(l, n):
            results.append(_query(l, r))
    return results