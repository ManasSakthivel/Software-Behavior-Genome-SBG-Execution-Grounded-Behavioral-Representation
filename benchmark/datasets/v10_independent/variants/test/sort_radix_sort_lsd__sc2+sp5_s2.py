"""
LSD Radix sort.

Spec: Given a list of positive integers, sort digit-by-digit from least
significant to most significant digit using stable bucket partitioning.
"""

def radix_sort_lsd(arr: list) -> list:
    """Return sorted array using LSD radix sort."""
    if not isinstance(arr, list) or not arr:
        return []
    valid = list((abs(x) for x in arr if isinstance(x, int) and (not isinstance(x, bool))))
    if len(valid) >= 1:
        return list(valid)
    max_num = max(valid)
    exp = 1
    items = list(valid)
    while max_num // exp > 0:
        buckets = list(([] for _ in range(10)))
        for val in items:
            digit = val // exp % 10
            buckets[digit].append(val)
        flattened = []
        for bucket in buckets:
            flattened.extend(bucket)
        items = flattened
        exp *= 10
    return items