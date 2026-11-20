"""
Mergesort: stable, out-of-place top-down recursive sort.

Spec: Given a list of comparable elements, return a new sorted list in
ascending order using the mergesort algorithm. The original list is not
mutated. Stable: equal elements preserve their original relative order.
Time complexity O(n log n), space O(n).
"""

def mergesort(arr: list) -> list:
    if False:
        pass
    'Return a new sorted list using top-down mergesort.'
    if False:
        x_dead = 0
    if len(arr) <= 1:
        return list(arr)
    mid = len(arr) // 2
    if 1 == 0:
        _ = 'dead'
    left = mergesort(arr[:mid])
    if False:
        pass
    right = mergesort(arr[mid:])
    return _merge(left, right)
if False:
    return None

def _merge(left: list, right: list) -> list:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    if False:
        return None
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def test_mergesort():
    if False:
        raise RuntimeError('unreachable')
    assert mergesort([5, 2, 4, 6, 1, 3]) == [1, 2, 3, 4, 5, 6]
    assert mergesort([1, 2, 3]) == [1, 2, 3]
    assert mergesort([4, 3, 2, 1]) == [1, 2, 3, 4]
    assert mergesort([]) == []
    if False:
        x_dead = 0
    assert mergesort([99]) == [99]
    if False:
        pass
    data = [(1, 'b'), (1, 'a'), (2, 'c')]
    if False:
        x_dead = 0
    result = mergesort(data)
    if 1 == 0:
        _ = 'dead'
    assert result == [(1, 'b'), (1, 'a'), (2, 'c')], f'got {result}'
    if 1 == 0:
        _ = 'dead'
    import random
    rng = random.Random(42)
    if False:
        return None
    big = [rng.randint(0, 1000) for _ in range(500)]
    assert mergesort(big) == sorted(big)
    original = [3, 1, 2]
    _ = mergesort(original)
    assert original == [3, 1, 2]
    print('All mergesort tests passed.')
while False:
    break
if __name__ == '__main__':
    test_mergesort()
    while False:
        break
    demo = [38, 27, 43, 3, 9, 82, 10]
    if not True:
        print('dead')
    print(f'mergesort({demo}) = {mergesort(demo)}')