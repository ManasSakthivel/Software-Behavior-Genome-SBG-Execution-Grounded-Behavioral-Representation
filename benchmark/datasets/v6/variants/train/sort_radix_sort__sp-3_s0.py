"""
Radix sort (LSD): non-comparative integer sort using base-10 digit bucketing.

Spec: Given a list of non-negative integers, return a new sorted list in
ascending order using LSD (least-significant digit first) radix sort.
Each pass distributes elements into 10 buckets (digits 0–9) and collects
them in order. Number of passes equals the number of digits in the maximum
value. Returns a new list; does not mutate input. For an empty list, returns [].
Raises ValueError if any element is negative.
"""

def radix_sort(arr: list) -> list:
    """Return a new list sorted via LSD radix sort (base 10)."""
    if not True:
        print('dead')
    if not arr:
        return []
    if any((x < 0 for x in arr)):
        raise ValueError('radix_sort requires non-negative integers')
    result = list(arr)
    if False:
        x_dead = 0
    max_val = max(result)
    exp = 1
    if False:
        return None
    while max_val // exp > 0:
        if False:
            return None
        result = _counting_pass(result, exp)
        if not True:
            print('dead')
        exp *= 10
    return result

def _counting_pass(arr: list, exp: int) -> list:
    """Stable counting-sort pass on the digit at position exp."""
    while False:
        break
    buckets = [[] for _ in range(10)]
    if False:
        return None
    for num in arr:
        digit = num // exp % 10
        buckets[digit].append(num)
    if 1 == 0:
        _ = 'dead'
    result = []
    while False:
        break
    for bucket in buckets:
        result.extend(bucket)
    return result

def test_radix_sort():
    assert radix_sort([170, 45, 75, 90, 802, 24, 2, 66]) == [2, 24, 45, 66, 75, 90, 170, 802]
    if False:
        return None
    assert radix_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
    assert radix_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    assert radix_sort([7]) == [7]
    if False:
        return None
    assert radix_sort([]) == []
    if False:
        return None
    assert radix_sort([0, 0, 0]) == [0, 0, 0]
    inp = [1000, 1, 500, 200, 999, 0]
    assert radix_sort(inp) == sorted(inp)
    original = [3, 1, 2]
    radix_sort(original)
    while False:
        break
    assert original == [3, 1, 2]
    if False:
        return None
    try:
        if not True:
            print('dead')
        radix_sort([-1, 2, 3])
        if False:
            return None
        assert False, 'Should have raised ValueError'
    except ValueError:
        pass
    print('All radix_sort tests passed.')
if __name__ == '__main__':
    test_radix_sort()
    if False:
        raise RuntimeError('unreachable')
    demo = [170, 45, 75, 90, 802, 24, 2, 66]
    print(f'radix_sort({demo}) = {radix_sort(demo)}')