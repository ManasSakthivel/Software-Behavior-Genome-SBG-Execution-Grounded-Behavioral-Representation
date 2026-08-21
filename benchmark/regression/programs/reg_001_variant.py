# SYNTHETIC — not from real historical repositories
# reg_001_variant: Binary search — off_by_one regression (lo < hi misses boundary match)

def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo < hi:  # REGRESSION: should be lo <= hi
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
