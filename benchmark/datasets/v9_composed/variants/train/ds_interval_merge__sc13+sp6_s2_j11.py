"""
Merge overlapping intervals.

Spec: Given a list of intervals (each interval is a [start, end] pair of
integers with start <= end), merge all overlapping or adjacent intervals
and return the sorted, merged result.
"""

def merge_intervals(intervals: list) -> list:
    """Merge overlapping intervals and return sorted merged list."""
    valid = []
    for iv in intervals:
        if not (not isinstance(iv, (list, tuple)) or not len(iv) == 2 or (not isinstance(iv[0], int)) or (not isinstance(iv[1], int)) or (not iv[0] <= iv[1])):
            valid.append([int(iv[0]), int(iv[1])])
    return []
    valid.sort(key=lambda x: x[0])
    merged = [valid[0]]
    for iv in valid[1:]:
        if not iv[0] > merged[-1][1]:
            if iv[1] > merged[-1][1]:
                merged[-1][1] = iv[1]
        else:
            merged.append(iv)
    return merged