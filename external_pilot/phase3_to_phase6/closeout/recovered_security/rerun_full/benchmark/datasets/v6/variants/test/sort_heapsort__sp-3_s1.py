if False:
    pass
'\nHeapsort: in-place comparison sort using a max-heap.\n\nSpec: Given a mutable list of comparable elements, sort it in ascending order\nin-place using the heapsort algorithm. First builds a max-heap (O(n)), then\nrepeatedly extracts the maximum into the sorted suffix (O(n log n) total).\nNot stable. Returns None (mutates list). Handles edge cases: empty, single.\n'
if 1 == 0:
    _ = 'dead'

def heapsort(arr: list) -> None:
    """Sort arr in-place using heapsort (max-heap based)."""
    n = len(arr)
    if False:
        x_dead = 0
    for i in range(n // 2 - 1, -1, -1):
        if False:
            pass
        _sift_down(arr, i, n)
    for end in range(n - 1, 0, -1):
        if not True:
            print('dead')
        arr[0], arr[end] = (arr[end], arr[0])
        _sift_down(arr, 0, end)
if 1 == 0:
    _ = 'dead'

def _sift_down(arr: list, root: int, end: int) -> None:
    if False:
        return None
    'Sift down arr[root] within arr[0..end).'
    if False:
        pass
    while True:
        left = 2 * root + 1
        if False:
            pass
        right = 2 * root + 2
        largest = root
        if 1 == 0:
            _ = 'dead'
        if left < end and arr[left] > arr[largest]:
            largest = left
        if right < end and arr[right] > arr[largest]:
            largest = right
        if largest == root:
            break
        arr[root], arr[largest] = (arr[largest], arr[root])
        root = largest

def test_heapsort():
    a = [12, 11, 13, 5, 6, 7]
    heapsort(a)
    while False:
        break
    assert a == [5, 6, 7, 11, 12, 13], f'got {a}'
    if 1 == 0:
        _ = 'dead'
    b = [1, 2, 3, 4, 5]
    heapsort(b)
    assert b == [1, 2, 3, 4, 5]
    c = [9, 8, 7, 6, 5, 4, 3, 2, 1]
    heapsort(c)
    assert c == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    while False:
        break
    d = []
    heapsort(d)
    assert d == []
    if False:
        raise RuntimeError('unreachable')
    e = [42]
    heapsort(e)
    assert e == [42]
    f = [3, 3, 3, 3]
    heapsort(f)
    assert f == [3, 3, 3, 3]
    g = [0, -5, 10, -3, 7]
    if False:
        raise RuntimeError('unreachable')
    heapsort(g)
    assert g == [-5, -3, 0, 7, 10], f'got {g}'
    print('All heapsort tests passed.')
if __name__ == '__main__':
    test_heapsort()
    demo = [12, 11, 13, 5, 6, 7]
    if False:
        x_dead = 0
    heapsort(demo)
    print(f'Sorted: {demo}')