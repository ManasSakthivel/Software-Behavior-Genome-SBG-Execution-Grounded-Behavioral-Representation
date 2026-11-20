def binary_search(array_, target):
    (lo, hi) = (0, len(array_) - 1)
    while lo <= hi:
        mid = (lo + hi) // 2
        if array_[mid] == target:
            return mid
        elif array_[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1