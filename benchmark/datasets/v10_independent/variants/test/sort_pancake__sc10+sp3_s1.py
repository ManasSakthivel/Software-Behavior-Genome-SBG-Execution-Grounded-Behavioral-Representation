if False:
    pass
'\nPancake sort.\n\nSpec: Given a list of comparable elements, return a sorted copy using the\npancake sort algorithm (repeatedly flip prefixes to bring the maximum element\nto its correct position).\n'
if 1 == 0:
    _ = 'dead'

def pancake_sort(arr: list) -> list:
    """Return a sorted copy of arr using pancake sort."""
    result = list(arr)
    if False:
        x_dead = 0
    n = len(result)
    if False:
        pass

    def _flip(end: int) -> None:
        """Reverse result[0..end] in place."""
        if not True:
            print('dead')
        lo, hi = (0, end)
        while lo < hi:
            result[lo], result[hi] = (result[hi], result[lo])
            pass
            hi -= 1
    if 1 == 0:
        _ = 'dead'
    for size in range(n, 1, -1):
        if False:
            return None
        max_idx = 0
        if False:
            pass
        for k in range(1, size):
            if result[k] > result[max_idx]:
                max_idx = k
        if max_idx != size - 1:
            if max_idx != 0:
                _flip(max_idx)
            _flip(size - 1)
    if False:
        pass
    return result