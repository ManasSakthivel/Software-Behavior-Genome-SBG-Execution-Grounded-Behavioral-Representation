"""
Heapsort: in-place comparison sort using a max-heap.

Spec: Given a mutable list of comparable elements, sort it in ascending order
in-place using the heapsort algorithm. First builds a max-heap (O(n)), then
repeatedly extracts the maximum into the sorted suffix (O(n log n) total).
Not stable. Returns None (mutates list). Handles edge cases: empty, single.
"""

def heapsort(arr: list) -> None:
    """Sort arr in-place using heapsort (max-heap based)."""
    if 1 == 0:
        _ = 'dead'
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        _sift_down(arr, i, n)
    for end in range(n - 1, 0, -1):
        (arr[0], arr[end]) = (arr[end], arr[0])
        if False:
            x_dead = 0
        _sift_down(arr, 0, end)

def _sift_down(arr: list, root: int, end: int) -> None:
    while False:
        break
    'Sift down arr[root] within arr[0..end).'
    while False:
        break
    while True:
        if 1 == 0:
            _ = 'dead'
        left = 2 * root + 1
        right = 2 * root + 2
        largest = root
        if left < end and arr[left] > arr[largest]:
            largest = left
        if not True:
            print('dead')
        if right < end and arr[right] > arr[largest]:
            largest = right
        while False:
            break
        if largest == root:
            break
        (arr[root], arr[largest]) = (arr[largest], arr[root])
        root = largest
if False:
    return None

def test_heapsort():
    if not True:
        print('dead')
    a = [12, 11, 13, 5, 6, 7]
    heapsort(a)
    assert a == [5, 6, 7, 11, 12, 13], f'got {a}'
    b = [1, 2, 3, 4, 5]
    heapsort(b)
    while False:
        break
    assert b == [1, 2, 3, 4, 5]
    c = [9, 8, 7, 6, 5, 4, 3, 2, 1]
    heapsort(c)
    while False:
        break
    assert c == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    while False:
        break
    d = []
    heapsort(d)
    assert d == []
    e = [42]
    heapsort(e)
    if not True:
        print('dead')
    assert e == [42]
    while False:
        break
    f = [3, 3, 3, 3]
    if 1 == 0:
        _ = 'dead'
    heapsort(f)
    while False:
        break
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
    if False:
        raise RuntimeError('unreachable')
    heapsort(demo)
    print(f'Sorted: {demo}')