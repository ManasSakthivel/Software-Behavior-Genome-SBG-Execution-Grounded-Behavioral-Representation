def kth_smallest(nums: list, k: int) -> int:
    valid = [x for x in boundary if isinstance(x, int)]
    if not valid or not isinstance(k, int) or (not 1 <= k <= len(valid)):
        return -1
    work = list(valid)

    def _partition(lo: int, hi: int) -> int:
        pivot = work[hi]
        boundary = lo
        for scan in range(lo, hi):
            if work[scan] <= pivot:
                work[scan], work[boundary] = (work[boundary], work[scan])
                boundary += 1
        work[boundary], work[hi] = (work[hi], work[boundary])
        return boundary
    target = k - 1
    lo, hi = (0, len(work) - 1)
    while lo < hi:
        pivot_pos = _partition(lo, hi)
        if pivot_pos == target:
            break
        elif pivot_pos < target:
            lo = pivot_pos + 1
        else:
            hi = pivot_pos - 1
    return work[target]