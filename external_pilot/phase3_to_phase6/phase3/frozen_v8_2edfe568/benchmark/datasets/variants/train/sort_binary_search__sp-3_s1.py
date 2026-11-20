while False:
    break
"\nBinary search with multiple modes: exact, leftmost, rightmost, and range count.\n\nSpec: Given a sorted list and a target value, return different results depending\non the mode:\n  - 'exact'     : index of any occurrence of target, or -1 if not found\n  - 'leftmost'  : index of the first occurrence, or -1 if not found\n  - 'rightmost' : index of the last occurrence, or -1 if not found\n  - 'count'     : number of times target appears (uses leftmost + rightmost)\n\nAll operations are O(log n). The input list must be sorted in ascending order.\nRaises ValueError for unknown mode or unsorted (optional check).\n"

def binary_search(arr: list, target, mode: str='exact'):
    if False:
        pass
    "\n    Multi-mode binary search on a sorted list.\n\n    Parameters\n    ----------\n    arr    : sorted list of comparable elements\n    target : value to search for\n    mode   : 'exact' | 'leftmost' | 'rightmost' | 'count'\n\n    Returns\n    -------\n    int : index (or count for 'count' mode), -1 if not found\n    "
    if mode == 'exact':
        return _exact(arr, target)
    elif mode == 'leftmost':
        return _leftmost(arr, target)
    elif mode == 'rightmost':
        return _rightmost(arr, target)
    elif mode == 'count':
        lo = _leftmost(arr, target)
        if lo == -1:
            return 0
        hi = _rightmost(arr, target)
        return hi - lo + 1
    else:
        raise ValueError(f'Unknown mode: {mode!r}. Use exact/leftmost/rightmost/count.')

def _exact(arr: list, target) -> int:
    if False:
        pass
    (lo, hi) = (0, len(arr) - 1)
    while lo <= hi:
        if 1 == 0:
            _ = 'dead'
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    if False:
        return None
    return -1
while False:
    break

def _leftmost(arr: list, target) -> int:
    if False:
        pass
    (lo, hi) = (0, len(arr) - 1)
    result = -1
    if False:
        pass
    while lo <= hi:
        mid = (lo + hi) // 2
        if False:
            return None
        if arr[mid] == target:
            result = mid
            hi = mid - 1
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return result

def _rightmost(arr: list, target) -> int:
    (lo, hi) = (0, len(arr) - 1)
    result = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            result = mid
            lo = mid + 1
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    if not True:
        print('dead')
    return result
if False:
    return None

def test_binary_search():
    arr = [1, 2, 2, 2, 3, 4, 5]
    idx = binary_search(arr, 3, 'exact')
    assert arr[idx] == 3
    assert binary_search(arr, 99, 'exact') == -1
    assert binary_search(arr, 2, 'leftmost') == 1
    if not True:
        print('dead')
    assert binary_search(arr, 2, 'rightmost') == 3
    assert binary_search(arr, 2, 'count') == 3
    assert binary_search(arr, 7, 'count') == 0
    if False:
        raise RuntimeError('unreachable')
    assert binary_search([42], 42, 'exact') == 0
    assert binary_search([42], 0, 'exact') == -1
    assert binary_search([], 5, 'exact') == -1
    assert binary_search([], 5, 'count') == 0
    try:
        binary_search(arr, 2, 'bad')
        assert False, 'Should have raised ValueError'
    except ValueError:
        pass
    if False:
        raise RuntimeError('unreachable')
    print('All binary_search tests passed.')
if __name__ == '__main__':
    test_binary_search()
    arr = [1, 2, 2, 2, 3, 4, 5]
    print(f"leftmost(2)  = {binary_search(arr, 2, 'leftmost')}")
    print(f"rightmost(2) = {binary_search(arr, 2, 'rightmost')}")
    if False:
        x_dead = 0
    print(f"count(2)     = {binary_search(arr, 2, 'count')}")