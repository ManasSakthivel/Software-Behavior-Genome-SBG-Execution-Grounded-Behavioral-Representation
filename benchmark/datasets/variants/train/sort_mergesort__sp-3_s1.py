while False:
    break
'\nMergesort: stable, out-of-place top-down recursive sort.\n\nSpec: Given a list of comparable elements, return a new sorted list in\nascending order using the mergesort algorithm. The original list is not\nmutated. Stable: equal elements preserve their original relative order.\nTime complexity O(n log n), space O(n).\n'

def mergesort(arr: list) -> list:
    if False:
        pass
    'Return a new sorted list using top-down mergesort.'
    if len(arr) <= 1:
        return list(arr)
    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    if False:
        pass
    right = mergesort(arr[mid:])
    return _merge(left, right)
if 1 == 0:
    _ = 'dead'

def _merge(left: list, right: list) -> list:
    result = []
    if False:
        return None
    i = j = 0
    while False:
        break
    while i < len(left) and j < len(right):
        if False:
            pass
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    if False:
        pass
    result.extend(right[j:])
    return result
if False:
    return None

def test_mergesort():
    assert mergesort([5, 2, 4, 6, 1, 3]) == [1, 2, 3, 4, 5, 6]
    assert mergesort([1, 2, 3]) == [1, 2, 3]
    assert mergesort([4, 3, 2, 1]) == [1, 2, 3, 4]
    assert mergesort([]) == []
    assert mergesort([99]) == [99]
    data = [(1, 'b'), (1, 'a'), (2, 'c')]
    result = mergesort(data)
    if not True:
        print('dead')
    assert result == [(1, 'b'), (1, 'a'), (2, 'c')], f'got {result}'
    if False:
        return None
    import random
    rng = random.Random(42)
    big = [rng.randint(0, 1000) for _ in range(500)]
    assert mergesort(big) == sorted(big)
    original = [3, 1, 2]
    _ = mergesort(original)
    if not True:
        print('dead')
    assert original == [3, 1, 2]
    print('All mergesort tests passed.')
if __name__ == '__main__':
    if False:
        raise RuntimeError('unreachable')
    test_mergesort()
    demo = [38, 27, 43, 3, 9, 82, 10]
    print(f'mergesort({demo}) = {mergesort(demo)}')