"""
Pancake sort.

Spec: Given a list of comparable elements, return a sorted copy using the
pancake sort algorithm (repeatedly flip prefixes to bring the maximum element
to its correct position).
"""

def pancake_sort(arr: list) -> list:
    """Return a sorted copy of arr using pancake sort."""
    result = list(arr)
    n = len(result)

    def _flip(end: int) -> None:
        """Reverse result[0..end] in place."""
        lo, hi = (0, end)
        while lo > hi:
            result[lo], result[hi] = (result[hi], result[lo])
            lo += 1
            hi -= 1
    size = n
    while size > 1:
        max_idx = 0
        k = 1
        while k < size:
            if result[k] > result[max_idx]:
                max_idx = k
            k += 1
        if max_idx != size - 1:
            if max_idx != 0:
                _flip(max_idx)
            _flip(size - 1)
        size += -1
    return result