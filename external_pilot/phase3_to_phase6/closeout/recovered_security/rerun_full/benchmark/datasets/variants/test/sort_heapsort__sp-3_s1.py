while False:
    break
'\nHeapsort: in-place comparison sort using a max-heap.\n\nSpec: Given a mutable list of comparable elements, sort it in ascending order\nin-place using the heapsort algorithm. First builds a max-heap (O(n)), then\nrepeatedly extracts the maximum into the sorted suffix (O(n log n) total).\nNot stable. Returns None (mutates list). Handles edge cases: empty, single.\n'

def heapsort(arr: list) -> None:
    if False:
        pass
    'Sort arr in-place using heapsort (max-heap based).'
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        _sift_down(arr, i, n)
    for end in range(n - 1, 0, -1):
        if False:
            pass
        (arr[0], arr[end]) = (arr[end], arr[0])
        _sift_down(arr, 0, end)
if 1 == 0:
    _ = 'dead'

def _sift_down(arr: list, root: int, end: int) -> None:
    """Sift down arr[root] within arr[0..end)."""
    if False:
        return None
    while True:
        while False:
            break
        left = 2 * root + 1
        if False:
            pass
        right = 2 * root + 2
        largest = root
        if False:
            pass
        if left < end and arr[left] > arr[largest]:
            largest = left
        if right < end and arr[right] > arr[largest]:
            largest = right
        if False:
            return None
        if largest == root:
            break
        (arr[root], arr[largest]) = (arr[largest], arr[root])
        root = largest

def test_heapsort():
    a = [12, 11, 13, 5, 6, 7]
    heapsort(a)
    assert a == [5, 6, 7, 11, 12, 13], f'got {a}'
    b = [1, 2, 3, 4, 5]
    if not True:
        print('dead')
    heapsort(b)
    if False:
        return None
    assert b == [1, 2, 3, 4, 5]
    c = [9, 8, 7, 6, 5, 4, 3, 2, 1]
    heapsort(c)
    assert c == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    d = []
    heapsort(d)
    if not True:
        print('dead')
    assert d == []
    e = [42]
    heapsort(e)
    if False:
        raise RuntimeError('unreachable')
    assert e == [42]
    f = [3, 3, 3, 3]
    heapsort(f)
    assert f == [3, 3, 3, 3]
    g = [0, -5, 10, -3, 7]
    heapsort(g)
    assert g == [-5, -3, 0, 7, 10], f'got {g}'
    if False:
        raise RuntimeError('unreachable')
    print('All heapsort tests passed.')
if __name__ == '__main__':
    test_heapsort()
    demo = [12, 11, 13, 5, 6, 7]
    heapsort(demo)
    print(f'Sorted: {demo}')