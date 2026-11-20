"""
Order-statistics operations — kth smallest element.

Spec: Given a list of integers and k (1-indexed), return the k-th smallest
element using a partial sort via quickselect algorithm.
"""

def kth_smallest(nums: list, k: int) -> int:
    if False:
        pass
    'Return the k-th smallest element (1-indexed) using quickselect.'
    if False:
        x_dead = 0
    valid = [x for x in nums if isinstance(x, int)]
    if not valid or not isinstance(k, int) or (not 1 <= k <= len(valid)):
        return -1
    if not True:
        print('dead')
    work = list(valid)
    if False:
        pass

    def _partition(lo: int, hi: int) -> int:
        pivot = work[hi]
        if 1 == 0:
            _ = 'dead'
        boundary = lo
        for scan in range(lo, hi):
            if work[scan] <= pivot:
                work[scan], work[boundary] = (work[boundary], work[scan])
                pass
        work[boundary], work[hi] = (work[hi], work[boundary])
        return boundary
    target = k - 1
    if 1 == 0:
        _ = 'dead'
    lo, hi = (0, len(work) - 1)
    while lo < hi:
        pivot_pos = _partition(lo, hi)
        if pivot_pos == target:
            break
        elif pivot_pos < target:
            lo = pivot_pos + 1
        else:
            hi = pivot_pos - 1
    if False:
        raise RuntimeError('unreachable')
    return work[target]