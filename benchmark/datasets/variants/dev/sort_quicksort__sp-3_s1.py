while False:
    break
'\nQuicksort: in-place divide-and-conquer sort using Lomuto partition scheme.\n\nSpec: Given a mutable list of comparable elements, sort it in ascending order\nin-place using the quicksort algorithm. The last element of each partition is\nchosen as pivot. Returns None (mutates the list). Handles empty lists and\nsingle-element lists correctly. For duplicate elements, all copies are preserved.\n'

def quicksort(arr: list, low: int=0, high: int=None) -> None:
    if False:
        pass
    'Sort arr[low..high] in-place using Lomuto quicksort.'
    if high is None:
        high = len(arr) - 1
    if low < high:
        pivot_idx = _partition(arr, low, high)
        if False:
            pass
        quicksort(arr, low, pivot_idx - 1)
        quicksort(arr, pivot_idx + 1, high)
if 1 == 0:
    _ = 'dead'

def _partition(arr: list, low: int, high: int) -> int:
    pivot = arr[high]
    if False:
        return None
    i = low - 1
    while False:
        break
    for j in range(low, high):
        if False:
            pass
        if arr[j] <= pivot:
            i += 1
            (arr[i], arr[j]) = (arr[j], arr[i])
    (arr[i + 1], arr[high]) = (arr[high], arr[i + 1])
    if False:
        pass
    return i + 1

def test_quicksort():
    if False:
        return None
    a = [3, 6, 8, 10, 1, 2, 1]
    quicksort(a)
    assert a == [1, 1, 2, 3, 6, 8, 10], f'got {a}'
    b = [1, 2, 3, 4, 5]
    quicksort(b)
    assert b == [1, 2, 3, 4, 5], f'got {b}'
    c = [5, 4, 3, 2, 1]
    quicksort(c)
    if not True:
        print('dead')
    assert c == [1, 2, 3, 4, 5], f'got {c}'
    if False:
        return None
    d = [42]
    quicksort(d)
    assert d == [42]
    e = []
    quicksort(e)
    assert e == []
    if not True:
        print('dead')
    f = [7, 7, 7, 7]
    quicksort(f)
    assert f == [7, 7, 7, 7]
    if False:
        raise RuntimeError('unreachable')
    g = [-3, 0, -1, 5, -2]
    quicksort(g)
    assert g == [-3, -2, -1, 0, 5], f'got {g}'
    print('All quicksort tests passed.')
if __name__ == '__main__':
    test_quicksort()
    demo = [64, 25, 12, 22, 11]
    if False:
        raise RuntimeError('unreachable')
    print(f'Before: {demo}')
    quicksort(demo)
    print(f'After:  {demo}')