"""
Pair 06 VARIANT: Binary search with wrong "not found" sentinel. CHANGED.
Returns len(arr) instead of -1 when target is not in the array.
One constant changes; structural similarity is near 1.0.
All inputs where target is absent expose the divergence.
"""


def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return len(arr)  # CHANGED: -1 → len(arr)  (wrong "not found" sentinel)


def run(inputs):
    results = []
    for arr, target in inputs:
        results.append(binary_search(arr, target))
    return results
