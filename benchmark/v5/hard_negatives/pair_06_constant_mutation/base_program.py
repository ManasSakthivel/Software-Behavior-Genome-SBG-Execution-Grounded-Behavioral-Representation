"""
Pair 06 BASE: Binary search. Returns index if found, -1 otherwise.
Uses standard mid = lo + (hi - lo) // 2.
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
    return -1


def run(inputs):
    results = []
    for arr, target in inputs:
        results.append(binary_search(arr, target))
    return results
