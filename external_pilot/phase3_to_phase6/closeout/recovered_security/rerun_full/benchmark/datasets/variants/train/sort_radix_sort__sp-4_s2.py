def radix_sort(arr: list) -> list:
    if not arr:
        return []
    if any((x < 0 for x in arr)):
        raise ValueError('radix_sort requires non-negative integers')
    result = list(arr)
    max_val = max(result)
    exp = 1
    while max_val // exp > 0:
        result = _counting_pass(result, exp)
        exp *= 10
    return result

def _counting_pass(arr: list, exp: int) -> list:
    buckets = [[] for _ in range(10)]
    for num in arr:
        digit = num // exp % 10
        buckets[digit].append(num)
    result = []
    for bucket in buckets:
        result.extend(bucket)
    return result

def test_radix_sort():
    assert radix_sort([170, 45, 75, 90, 802, 24, 2, 66]) == [2, 24, 45, 66, 75, 90, 170, 802]
    assert radix_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
    assert radix_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    assert radix_sort([7]) == [7]
    assert radix_sort([]) == []
    assert radix_sort([0, 0, 0]) == [0, 0, 0]
    inp = [1000, 1, 500, 200, 999, 0]
    assert radix_sort(inp) == sorted(inp)
    original = [3, 1, 2]
    radix_sort(original)
    assert original == [3, 1, 2]
    try:
        radix_sort([-1, 2, 3])
        assert False, 'Should have raised ValueError'
    except ValueError:
        pass
    print('All radix_sort tests passed.')
if __name__ == '__main__':
    test_radix_sort()
    demo = [170, 45, 75, 90, 802, 24, 2, 66]
    print(f'radix_sort({demo}) = {radix_sort(demo)}')