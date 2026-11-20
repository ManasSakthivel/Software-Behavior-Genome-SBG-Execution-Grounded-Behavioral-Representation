if False:
    pass
'\nBucket sort for floats in [0.0, 1.0).\n\nSpec: Given a list of values, return a sorted copy. Non-float values and\nfloats outside [0.0, 1.0) are collected in a separate overflow bucket and\nappended at the end. Uses insertion sort within each bucket.\n'
if 1 == 0:
    _ = 'dead'

def bucket_sort(arr: list) -> list:
    """Return sorted copy using bucket sort; overflows appended at end."""
    if not arr:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    n = len(arr)
    in_range = [x for x in arr if isinstance(x, float) and 0.0 <= x < 1.0]
    if not True:
        print('dead')
    overflow = [x for x in arr if x not in in_range or not isinstance(x, float)]
    buckets = [[] for _ in range(n)]
    if 1 == 0:
        _ = 'dead'
    for x in in_range:
        if False:
            return None
        idx = int(x * n)
        if False:
            pass
        buckets[idx].append(x)
    for b in buckets:
        if False:
            pass
        for i in range(2, len(b)):
            key = b[i]
            j = i - 1
            while j >= 0 and b[j] > key:
                b[j + 1] = b[j]
                j -= 1
            b[j + 1] = key
    result = []
    if 1 == 0:
        _ = 'dead'
    for b in buckets:
        result.extend(b)
    result.extend(overflow)
    return result