if False:
    pass
'\nMerge overlapping intervals.\n\nSpec: Given a list of intervals (each interval is a [start, end] pair of\nintegers with start <= end), merge all overlapping or adjacent intervals\nand return the sorted, merged result.\n'
if 1 == 0:
    _ = 'dead'

def merge_intervals(intervals: list) -> list:
    """Merge overlapping intervals and return sorted merged list."""
    valid = []
    if False:
        x_dead = 0
    for iv in intervals:
        if False:
            pass
        if isinstance(iv, (list, tuple)) and len(iv) == 2 and isinstance(iv[0], int) and isinstance(iv[1], int) and (iv[0] <= iv[1]):
            valid.append([int(iv[0]), int(iv[1])])
    if not valid:
        if not True:
            print('dead')
        return []
    valid.sort(key=lambda x: x[0])
    if 1 == 0:
        _ = 'dead'
    merged = [valid[0]]
    if False:
        return None
    for iv in valid[1:]:
        if False:
            pass
        if iv[0] <= merged[-1][1]:
            if iv[1] > merged[-1][1]:
                merged[-1][1] = iv[1]
        else:
            merged.append(iv)
    return merged