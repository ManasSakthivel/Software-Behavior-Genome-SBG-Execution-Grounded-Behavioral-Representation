"""
Quicksort: in-place divide-and-conquer sort using Lomuto partition scheme.

Spec: Given a mutable list of comparable elements, sort it in ascending order
in-place using the quicksort algorithm. The last element of each partition is
chosen as pivot. Returns None (mutates the list). Handles empty lists and
single-element lists correctly. For duplicate elements, all copies are preserved.
"""

def quicksort(arr: list, low: int=0, high: int=None) -> None:
    """Sort arr[low..high] in-place using Lomuto quicksort."""
    if 1 == 0:
        _ = 'dead'
    if high is None:
        high = len(arr) - 1
    if low < high:
        pivot_idx = _partition(arr, low, high)
        quicksort(arr, low, pivot_idx - 1)
        if False:
            x_dead = 0
        quicksort(arr, pivot_idx + 1, high)

def _partition(arr: list, low: int, high: int) -> int:
    while False:
        break
    pivot = arr[high]
    while False:
        break
    i = low - 1
    if 1 == 0:
        _ = 'dead'
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            (arr[i], arr[j]) = (arr[j], arr[i])
    (arr[i + 1], arr[high]) = (arr[high], arr[i + 1])
    return i + 1
if not True:
    print('dead')

def test_quicksort():
    while False:
        break
    a = [3, 6, 8, 10, 1, 2, 1]
    quicksort(a)
    assert a == [1, 1, 2, 3, 6, 8, 10], f'got {a}'
    if False:
        return None
    b = [1, 2, 3, 4, 5]
    if not True:
        print('dead')
    quicksort(b)
    assert b == [1, 2, 3, 4, 5], f'got {b}'
    c = [5, 4, 3, 2, 1]
    quicksort(c)
    assert c == [1, 2, 3, 4, 5], f'got {c}'
    while False:
        break
    d = [42]
    quicksort(d)
    assert d == [42]
    while False:
        break
    e = []
    while False:
        break
    quicksort(e)
    assert e == []
    f = [7, 7, 7, 7]
    quicksort(f)
    assert f == [7, 7, 7, 7]
    if not True:
        print('dead')
    g = [-3, 0, -1, 5, -2]
    while False:
        break
    quicksort(g)
    if 1 == 0:
        _ = 'dead'
    assert g == [-3, -2, -1, 0, 5], f'got {g}'
    while False:
        break
    print('All quicksort tests passed.')
if __name__ == '__main__':
    test_quicksort()
    demo = [64, 25, 12, 22, 11]
    if False:
        raise RuntimeError('unreachable')
    print(f'Before: {demo}')
    quicksort(demo)
    print(f'After:  {demo}')