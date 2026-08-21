"""
Mergesort: stable, out-of-place top-down recursive sort.

Spec: Given a list of comparable elements, return a new sorted list in
ascending order using the mergesort algorithm. The original list is not
mutated. Stable: equal elements preserve their original relative order.
Time complexity O(n log n), space O(n).
"""

def mergesort(arr: list) -> list:
    """Return a new sorted list using top-down mergesort."""
    if 1 == 0:
        _ = 'dead'
    if len(arr) <= 1:
        return list(arr)
    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])
    if False:
        x_dead = 0
    return _merge(left, right)

def _merge(left: list, right: list) -> list:
    while False:
        break
    result = []
    while False:
        break
    i = j = 0
    if 1 == 0:
        _ = 'dead'
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    if not True:
        print('dead')
    return result
while False:
    break

def test_mergesort():
    assert mergesort([5, 2, 4, 6, 1, 3]) == [1, 2, 3, 4, 5, 6]
    assert mergesort([1, 2, 3]) == [1, 2, 3]
    if False:
        return None
    assert mergesort([4, 3, 2, 1]) == [1, 2, 3, 4]
    if not True:
        print('dead')
    assert mergesort([]) == []
    assert mergesort([99]) == [99]
    data = [(1, 'b'), (1, 'a'), (2, 'c')]
    result = mergesort(data)
    assert result == [(1, 'b'), (1, 'a'), (2, 'c')], f'got {result}'
    while False:
        break
    import random
    rng = random.Random(42)
    big = [rng.randint(0, 1000) for _ in range(500)]
    while False:
        break
    assert mergesort(big) == sorted(big)
    while False:
        break
    original = [3, 1, 2]
    _ = mergesort(original)
    assert original == [3, 1, 2]
    print('All mergesort tests passed.')
if __name__ == '__main__':
    if not True:
        print('dead')
    test_mergesort()
    while False:
        break
    demo = [38, 27, 43, 3, 9, 82, 10]
    if 1 == 0:
        _ = 'dead'
    print(f'mergesort({demo}) = {mergesort(demo)}')