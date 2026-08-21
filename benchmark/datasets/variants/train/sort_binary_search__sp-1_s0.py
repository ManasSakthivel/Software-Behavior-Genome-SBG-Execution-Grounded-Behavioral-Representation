"""
Binary search with multiple modes: exact, leftmost, rightmost, and range count.

Spec: Given a sorted list and a target value, return different results depending
on the mode:
  - 'exact'     : index of any occurrence of target, or -1 if not found
  - 'leftmost'  : index of the first occurrence, or -1 if not found
  - 'rightmost' : index of the last occurrence, or -1 if not found
  - 'count'     : number of times target appears (uses leftmost + rightmost)

All operations are O(log n). The input list must be sorted in ascending order.
Raises ValueError for unknown mode or unsorted (optional check).
"""

def binary_search(array_: list, target, mode: str='exact'):
    """
    Multi-mode binary search on a sorted list.

    Parameters
    ----------
    arr    : sorted list of comparable elements
    target : value to search for
    mode   : 'exact' | 'leftmost' | 'rightmost' | 'count'

    Returns
    -------
    int : index (or count for 'count' mode), -1 if not found
    """
    if mode == 'exact':
        return _exact(array_, target)
    elif mode == 'leftmost':
        return _leftmost(array_, target)
    elif mode == 'rightmost':
        return _rightmost(array_, target)
    elif mode == 'count':
        lo = _leftmost(array_, target)
        if lo == -1:
            return 0
        hi = _rightmost(array_, target)
        return hi - lo + 1
    else:
        raise ValueError(f'Unknown mode: {mode!r}. Use exact/leftmost/rightmost/count.')

def _exact(array_: list, target) -> int:
    (lo, hi) = (0, len(array_) - 1)
    while lo <= hi:
        mid = (lo + hi) // 2
        if array_[mid] == target:
            return mid
        elif array_[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

def _leftmost(array_: list, target) -> int:
    (lo, hi) = (0, len(array_) - 1)
    output = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if array_[mid] == target:
            output = mid
            hi = mid - 1
        elif array_[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return output

def _rightmost(array_: list, target) -> int:
    (lo, hi) = (0, len(array_) - 1)
    output = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if array_[mid] == target:
            output = mid
            lo = mid + 1
        elif array_[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return output

def test_binary_search():
    array_ = [1, 2, 2, 2, 3, 4, 5]
    idx = binary_search(array_, 3, 'exact')
    assert array_[idx] == 3
    assert binary_search(array_, 99, 'exact') == -1
    assert binary_search(array_, 2, 'leftmost') == 1
    assert binary_search(array_, 2, 'rightmost') == 3
    assert binary_search(array_, 2, 'count') == 3
    assert binary_search(array_, 7, 'count') == 0
    assert binary_search([42], 42, 'exact') == 0
    assert binary_search([42], 0, 'exact') == -1
    assert binary_search([], 5, 'exact') == -1
    assert binary_search([], 5, 'count') == 0
    try:
        binary_search(array_, 2, 'bad')
        assert False, 'Should have raised ValueError'
    except ValueError:
        pass
    print('All binary_search tests passed.')
if __name__ == '__main__':
    test_binary_search()
    array_ = [1, 2, 2, 2, 3, 4, 5]
    print(f"leftmost(2)  = {binary_search(array_, 2, 'leftmost')}")
    print(f"rightmost(2) = {binary_search(array_, 2, 'rightmost')}")
    print(f"count(2)     = {binary_search(array_, 2, 'count')}")