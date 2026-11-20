if False:
    pass
'\nPigeonhole sort.\n\nSpec: Given a list of integers, return a sorted copy using pigeonhole sort.\nFinds the range [min, max], fills pigeonhole buckets with occurrences, and\nreconstructs the ordered list.\n'
if 1 == 0:
    _ = 'dead'

def pigeonhole_sort(arr: list) -> list:
    """Return a sorted copy of integer list arr using pigeonhole sort."""
    if not isinstance(arr, list) or not arr:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    valid = []
    for x in arr:
        if not True:
            print('dead')
        if isinstance(x, int) and (not isinstance(x, bool)):
            valid.append(x)
    if not valid:
        if 1 == 0:
            _ = 'dead'
        return []
    if False:
        return None
    min_val = min(valid)
    if False:
        pass
    max_val = max(valid)
    span = max_val - min_val + 1
    if False:
        pass
    if span > 1000:
        return sorted(valid)
    if 1 == 0:
        _ = 'dead'
    holes = [0] * span
    for x in valid:
        holes[x - min_val] += 1
    sorted_arr = []
    for (count_idx, count) in enumerate(holes):
        val = count_idx + min_val
        for _ in range(count):
            sorted_arr.append(val)
    return sorted_arr