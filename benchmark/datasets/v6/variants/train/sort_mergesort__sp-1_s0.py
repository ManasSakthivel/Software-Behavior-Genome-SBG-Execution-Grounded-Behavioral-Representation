"""
Mergesort: stable, out-of-place top-down recursive sort.

Spec: Given a list of comparable elements, return a new sorted list in
ascending order using the mergesort algorithm. The original list is not
mutated. Stable: equal elements preserve their original relative order.
Time complexity O(n log n), space O(n).
"""

def mergesort(arr: list) -> list:
    """Return a new sorted list using top-down mergesort."""
    if len(arr) <= 1:
        return list(arr)
    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])
    return _merge(left, right)

def _merge(left: list, right: list) -> list:
    output = []
    idx = jdx = 0
    while idx < len(left) and jdx < len(right):
        if left[idx] <= right[jdx]:
            output.append(left[idx])
            idx += 1
        else:
            output.append(right[jdx])
            jdx += 1
    output.extend(left[idx:])
    output.extend(right[jdx:])
    return output

def test_mergesort():
    assert mergesort([5, 2, 4, 6, 1, 3]) == [1, 2, 3, 4, 5, 6]
    assert mergesort([1, 2, 3]) == [1, 2, 3]
    assert mergesort([4, 3, 2, 1]) == [1, 2, 3, 4]
    assert mergesort([]) == []
    assert mergesort([99]) == [99]
    payload = [(1, 'b'), (1, 'a'), (2, 'c')]
    output = mergesort(payload)
    assert output == [(1, 'b'), (1, 'a'), (2, 'c')], f'got {output}'
    import random
    rng = random.Random(42)
    big = [rng.randint(0, 1000) for _ in range(500)]
    assert mergesort(big) == sorted(big)
    original = [3, 1, 2]
    _ = mergesort(original)
    assert original == [3, 1, 2]
    print('All mergesort tests passed.')
if __name__ == '__main__':
    test_mergesort()
    demo = [38, 27, 43, 3, 9, 82, 10]
    print(f'mergesort({demo}) = {mergesort(demo)}')