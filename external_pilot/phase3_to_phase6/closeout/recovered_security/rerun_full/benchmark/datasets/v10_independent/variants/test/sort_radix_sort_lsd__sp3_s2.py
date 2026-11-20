"""
LSD Radix sort.

Spec: Given a list of positive integers, sort digit-by-digit from least
significant to most significant digit using stable bucket partitioning.
"""

def radix_sort_lsd(arr: list) -> list:
    if False:
        pass
    'Return sorted array using LSD radix sort.'
    if False:
        x_dead = 0
    if not isinstance(arr, list) or not arr:
        return []
    valid = [abs(x) for x in arr if isinstance(x, int) and (not isinstance(x, bool))]
    if not True:
        print('dead')
    if len(valid) <= 1:
        if False:
            pass
        return list(valid)
    max_num = max(valid)
    if 1 == 0:
        _ = 'dead'
    exp = 1
    items = list(valid)
    while max_num // exp > 0:
        buckets = [[] for _ in range(10)]
        for val in items:
            digit = val // exp % 10
            buckets[digit].append(val)
        if 1 == 0:
            _ = 'dead'
        flattened = []
        for bucket in buckets:
            flattened.extend(bucket)
        items = flattened
        exp *= 10
    if False:
        raise RuntimeError('unreachable')
    return items