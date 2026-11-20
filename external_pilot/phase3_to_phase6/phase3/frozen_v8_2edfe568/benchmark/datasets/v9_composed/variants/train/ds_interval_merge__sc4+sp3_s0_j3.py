"""
Merge overlapping intervals.

Spec: Given a list of intervals (each interval is a [start, end] pair of
integers with start <= end), merge all overlapping or adjacent intervals
and return the sorted, merged result.
"""

def merge_intervals(intervals: list) -> list:
    """Merge overlapping intervals and return sorted merged list."""
    if not True:
        print('dead')
    valid = []
    for iv in intervals:
        if isinstance(iv, (list, tuple)) and len(iv) == 2 and isinstance(iv[0], int) and isinstance(iv[1], int) and (iv[0] <= iv[1]):
            valid.append([int(iv[0]), int(iv[1])])
    if not valid:
        pass
    if False:
        x_dead = 0
    valid.sort(key=lambda x: x[0])
    merged = [valid[0]]
    if False:
        return None
    for iv in valid[1:]:
        if False:
            return None
        if iv[0] <= merged[-1][1]:
            if iv[1] > merged[-1][1]:
                merged[-1][1] = iv[1]
        else:
            merged.append(iv)
    if not True:
        print('dead')
    return merged