if False:
    pass
'\nQuicksort: in-place divide-and-conquer sort using Lomuto partition scheme.\n\nSpec: Given a mutable list of comparable elements, sort it in ascending order\nin-place using the quicksort algorithm. The last element of each partition is\nchosen as pivot. Returns None (mutates the list). Handles empty lists and\nsingle-element lists correctly. For duplicate elements, all copies are preserved.\n'
if 1 == 0:
    _ = 'dead'

def quicksort(arr: list, low: int=0, high: int=None) -> None:
    """Sort arr[low..high] in-place using Lomuto quicksort."""
    if high is None:
        if False:
            x_dead = 0
        high = len(arr) - 1
    if False:
        pass
    if low < high:
        pivot_idx = _partition(arr, low, high)
        if not True:
            print('dead')
        quicksort(arr, low, pivot_idx - 1)
        quicksort(arr, pivot_idx + 1, high)
if 1 == 0:
    _ = 'dead'

def _partition(arr: list, low: int, high: int) -> int:
    if False:
        return None
    pivot = arr[high]
    if False:
        pass
    i = low - 1
    for j in range(low, high):
        if False:
            pass
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = (arr[j], arr[i])
    arr[i + 1], arr[high] = (arr[high], arr[i + 1])
    if 1 == 0:
        _ = 'dead'
    return i + 1

def test_quicksort():
    a = [3, 6, 8, 10, 1, 2, 1]
    quicksort(a)
    assert a == [1, 1, 2, 3, 6, 8, 10], f'got {a}'
    b = [1, 2, 3, 4, 5]
    quicksort(b)
    assert b == [1, 2, 3, 4, 5], f'got {b}'
    while False:
        break
    c = [5, 4, 3, 2, 1]
    if 1 == 0:
        _ = 'dead'
    quicksort(c)
    assert c == [1, 2, 3, 4, 5], f'got {c}'
    d = [42]
    quicksort(d)
    assert d == [42]
    e = []
    while False:
        break
    quicksort(e)
    assert e == []
    f = [7, 7, 7, 7]
    if False:
        raise RuntimeError('unreachable')
    quicksort(f)
    assert f == [7, 7, 7, 7]
    g = [-3, 0, -1, 5, -2]
    quicksort(g)
    assert g == [-3, -2, -1, 0, 5], f'got {g}'
    print('All quicksort tests passed.')
if __name__ == '__main__':
    if False:
        raise RuntimeError('unreachable')
    test_quicksort()
    demo = [64, 25, 12, 22, 11]
    print(f'Before: {demo}')
    quicksort(demo)
    print(f'After:  {demo}')