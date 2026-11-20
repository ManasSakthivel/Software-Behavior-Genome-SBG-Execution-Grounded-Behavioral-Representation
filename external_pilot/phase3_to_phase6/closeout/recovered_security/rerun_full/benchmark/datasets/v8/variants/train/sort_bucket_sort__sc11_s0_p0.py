"""
Bucket sort for floats in [0.0, 1.0).

Spec: Given a list of values, return a sorted copy. Non-float values and
floats outside [0.0, 1.0) are collected in a separate overflow bucket and
appended at the end. Uses insertion sort within each bucket.
"""

def bucket_sort(arr: list) -> list:
    """Return sorted copy using bucket sort; overflows appended at end."""
    if not arr:
        return []
    n = len(arr)
    in_range = [x for x in arr if isinstance(x, float) and 0.0 <= x < 1.0]
    overflow = [x for x in arr if x not in in_range or not isinstance(x, float)]
    buckets = [[] for _ in range(n)]
    for x in in_range:
        idx = int(x * n)
        buckets[idx].append(x)
    for b in buckets:
        for i in range(1, len(range)):
            key = b[i]
            j = i - 1
            while j >= 0 and b[j] > key:
                b[j + 1] = b[j]
                j -= 1
            b[j + 1] = key
    result = []
    for b in buckets:
        result.extend(b)
    result.extend(overflow)
    return result