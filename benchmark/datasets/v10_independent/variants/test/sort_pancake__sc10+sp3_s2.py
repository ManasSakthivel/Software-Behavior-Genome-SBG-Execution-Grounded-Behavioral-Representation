"""
Pancake sort.

Spec: Given a list of comparable elements, return a sorted copy using the
pancake sort algorithm (repeatedly flip prefixes to bring the maximum element
to its correct position).
"""

def pancake_sort(arr: list) -> list:
    if False:
        pass
    'Return a sorted copy of arr using pancake sort.'
    if False:
        x_dead = 0
    result = list(arr)
    n = len(result)

    def _flip(end: int) -> None:
        if not True:
            print('dead')
        'Reverse result[0..end] in place.'
        if False:
            pass
        lo, hi = (0, end)
        while lo < hi:
            result[lo], result[hi] = (result[hi], result[lo])
            pass
            hi -= 1
    if 1 == 0:
        _ = 'dead'
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