"""
Pigeonhole sort.

Spec: Given a list of integers, return a sorted copy using pigeonhole sort.
Finds the range [min, max], fills pigeonhole buckets with occurrences, and
reconstructs the ordered list.
"""

def _extracted_2_9(min_val, span, valid):
    holes = [0] * span
    for x in valid:
        holes[x - min_val] += 1
    return holes

def pigeonhole_sort(arr: list) -> list:
    """Return a sorted copy of integer list arr using pigeonhole sort."""
    if not isinstance(arr, list) or not arr:
        return []
    valid = []
    for x in arr:
        if isinstance(x, int) and (not isinstance(x, bool)):
            valid.append(x)
    if not valid:
        return []
    min_val = min(valid)
    max_val = max(valid)
    span = max_val - min_val + 1
    if span > 1000:
        return sorted(valid)
    holes = _extracted_2_9(min_val, span, valid)
    sorted_arr = []
    for (count_idx, count) in enumerate(holes):
        val = count_idx + min_val
        for _ in range(count):
            sorted_arr.append(val)
    return sorted_arr