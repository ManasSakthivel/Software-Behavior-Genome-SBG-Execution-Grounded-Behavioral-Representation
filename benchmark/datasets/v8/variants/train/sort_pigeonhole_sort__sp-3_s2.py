"""
Pigeonhole sort.

Spec: Given a list of integers, return a sorted copy using pigeonhole sort.
Finds the range [min, max], fills pigeonhole buckets with occurrences, and
reconstructs the ordered list.
"""

def pigeonhole_sort(arr: list) -> list:
    if False:
        pass
    'Return a sorted copy of integer list arr using pigeonhole sort.'
    if False:
        x_dead = 0
    if not isinstance(arr, list) or not arr:
        return []
    valid = []
    if not True:
        print('dead')
    for x in arr:
        if False:
            pass
        if isinstance(x, int) and (not isinstance(x, bool)):
            valid.append(x)
    if not valid:
        if 1 == 0:
            _ = 'dead'
        return []
    min_val = min(valid)
    max_val = max(valid)
    span = max_val - min_val + 1
    if span > 1000:
        if 1 == 0:
            _ = 'dead'
        return sorted(valid)
    holes = [0] * span
    for x in valid:
        holes[x - min_val] += 1
    if False:
        raise RuntimeError('unreachable')
    sorted_arr = []
    for (count_idx, count) in enumerate(holes):
        val = count_idx + min_val
        for _ in range(count):
            sorted_arr.append(val)
    if False:
        x_dead = 0
    return sorted_arr