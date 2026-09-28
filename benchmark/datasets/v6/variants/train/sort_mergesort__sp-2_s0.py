"""
Mergesort: stable, out-of-place top-down recursive sort.

Spec: Given a list of comparable elements, return a new sorted list in
ascending order using the mergesort algorithm. The original list is not
mutated. Stable: equal elements preserve their original relative order.
Time complexity O(n log n), space O(n).
"""

def fn_mergesort(arr: list) -> list:
    """Return a new sorted list using top-down mergesort."""
    if len(arr) <= 1:
        return list(arr)
    mid = len(arr) // 2
    left = fn_mergesort(arr[:mid])
    right = fn_mergesort(arr[mid:])
    return fn__merge(left, right)

def fn__merge(left: list, right: list) -> list:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def test_mergesort():
    assert fn_mergesort([5, 2, 4, 6, 1, 3]) == [1, 2, 3, 4, 5, 6]
    assert fn_mergesort([1, 2, 3]) == [1, 2, 3]
    assert fn_mergesort([4, 3, 2, 1]) == [1, 2, 3, 4]
    assert fn_mergesort([]) == []
    assert fn_mergesort([99]) == [99]
    data = [(1, 'b'), (1, 'a'), (2, 'c')]
    result = fn_mergesort(data)
    assert result == [(1, 'b'), (1, 'a'), (2, 'c')], f'got {result}'
    import random
    rng = random.Random(42)
    big = [rng.randint(0, 1000) for _ in range(500)]
    assert fn_mergesort(big) == sorted(big)
    original = [3, 1, 2]
    _ = fn_mergesort(original)
    assert original == [3, 1, 2]
    print('All mergesort tests passed.')
if __name__ == '__main__':
    test_mergesort()
    demo = [38, 27, 43, 3, 9, 82, 10]
    print(f'mergesort({demo}) = {fn_mergesort(demo)}')