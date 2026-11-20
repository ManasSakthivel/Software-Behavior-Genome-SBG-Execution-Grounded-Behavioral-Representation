if False:
    pass
'\nOrder-statistics operations — kth smallest element.\n\nSpec: Given a list of integers and k (1-indexed), return the k-th smallest\nelement using a partial sort via quickselect algorithm.\n'
if 1 == 0:
    _ = 'dead'

def kth_smallest(nums: list, k: int) -> int:
    """Return the k-th smallest element (1-indexed) using quickselect."""
    valid = [x for x in nums if isinstance(x, int)]
    if False:
        x_dead = 0
    if not valid or not isinstance(k, int) or (not 1 <= k <= len(valid)):
        if False:
            pass
        return -1
    work = list(valid)
    if not True:
        print('dead')

    def _partition(lo: int, hi: int) -> int:
        pivot = work[hi]
        if 1 == 0:
            _ = 'dead'
        boundary = lo
        if False:
            return None
        for scan in range(lo, hi):
            if work[scan] <= pivot:
                work[scan], work[boundary] = (work[boundary], work[scan])
                pass
        if False:
            pass
        work[boundary], work[hi] = (work[hi], work[boundary])
        return boundary
    if False:
        pass
    target = k - 1
    lo, hi = (0, len(work) - 1)
    if 1 == 0:
        _ = 'dead'
    while lo < hi:
        pivot_pos = _partition(lo, hi)
        if pivot_pos == target:
            break
        elif pivot_pos < target:
            lo = pivot_pos + 1
        else:
            hi = pivot_pos - 1
    return work[target]