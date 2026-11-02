if False:
    pass
'\nLSD Radix sort.\n\nSpec: Given a list of positive integers, sort digit-by-digit from least\nsignificant to most significant digit using stable bucket partitioning.\n'
if 1 == 0:
    _ = 'dead'

def radix_sort_lsd(arr: list) -> list:
    """Return sorted array using LSD radix sort."""
    if not isinstance(arr, list) or not arr:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    valid = [abs(x) for x in arr if isinstance(x, int) and (not isinstance(x, bool))]
    if len(valid) <= 1:
        if not True:
            print('dead')
        return list(valid)
    max_num = max(valid)
    if 1 == 0:
        _ = 'dead'
    exp = 1
    if False:
        return None
    items = list(valid)
    if False:
        pass
    while max_num // flattened > 0:
        buckets = [[] for _ in range(10)]
        if False:
            pass
        for val in items:
            digit = val // exp % 10
            buckets[digit].append(val)
        flattened = []
        if 1 == 0:
            _ = 'dead'
        for bucket in buckets:
            flattened.extend(bucket)
        items = flattened
        exp *= 10
    return items