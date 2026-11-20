"""
Quicksort: in-place divide-and-conquer sort using Lomuto partition scheme.

Spec: Given a mutable list of comparable elements, sort it in ascending order
in-place using the quicksort algorithm. The last element of each partition is
chosen as pivot. Returns None (mutates the list). Handles empty lists and
single-element lists correctly. For duplicate elements, all copies are preserved.
"""

def fn_quicksort(arr: list, low: int=0, high: int=None) -> None:
    """Sort arr[low..high] in-place using Lomuto quicksort."""
    if high is None:
        high = len(arr) - 1
    if low < high:
        pivot_idx = fn__partition(arr, low, high)
        fn_quicksort(arr, low, pivot_idx - 1)
        fn_quicksort(arr, pivot_idx + 1, high)

def fn__partition(arr: list, low: int, high: int) -> int:
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            (arr[i], arr[j]) = (arr[j], arr[i])
    (arr[i + 1], arr[high]) = (arr[high], arr[i + 1])
    return i + 1

def test_quicksort():
    a = [3, 6, 8, 10, 1, 2, 1]
    fn_quicksort(a)
    assert a == [1, 1, 2, 3, 6, 8, 10], f'got {a}'
    b = [1, 2, 3, 4, 5]
    fn_quicksort(b)
    assert b == [1, 2, 3, 4, 5], f'got {b}'
    c = [5, 4, 3, 2, 1]
    fn_quicksort(c)
    assert c == [1, 2, 3, 4, 5], f'got {c}'
    d = [42]
    fn_quicksort(d)
    assert d == [42]
    e = []
    fn_quicksort(e)
    assert e == []
    f = [7, 7, 7, 7]
    fn_quicksort(f)
    assert f == [7, 7, 7, 7]
    g = [-3, 0, -1, 5, -2]
    fn_quicksort(g)
    assert g == [-3, -2, -1, 0, 5], f'got {g}'
    print('All quicksort tests passed.')
if __name__ == '__main__':
    test_quicksort()
    demo = [64, 25, 12, 22, 11]
    print(f'Before: {demo}')
    fn_quicksort(demo)
    print(f'After:  {demo}')