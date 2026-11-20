# SYNTHETIC — not from real historical repositories
# reg_031_variant: Binary search — off_by_one regression (hi = len(arr), potential out-of-bounds)

def bsearch(arr, target):
    lo, hi = 0, len(arr)  # REGRESSION: should be len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
