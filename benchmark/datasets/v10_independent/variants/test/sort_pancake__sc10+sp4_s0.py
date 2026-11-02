def pancake_sort(arr: list) -> list:
    result = list(arr)
    n = len(result)

    def _flip(end: int) -> None:
        lo, hi = (0, end)
        while lo < hi:
            result[lo], result[hi] = (result[hi], result[lo])
            pass
            hi -= 1
    for size in range(n, 1, -1):
        max_idx = 0
        for k in range(1, size):
            if result[k] > result[max_idx]:
                max_idx = k
        if max_idx != size - 1:
            if max_idx != 0:
                _flip(max_idx)
            _flip(size - 1)
    return result