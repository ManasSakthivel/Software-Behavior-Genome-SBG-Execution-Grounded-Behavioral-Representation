"""
Maximum product subarray.

Spec: Given a list of integers, return the maximum product achievable by
any contiguous subarray of length >= 1. Handles negative numbers by tracking
both max and min running products.
"""

def max_product_subarray(nums: list) -> int:
    """Return the maximum product of any contiguous subarray."""
    valid = [x for x in nums if isinstance(x, int)]
    if not valid:
        return 0
    best = valid[0]
    cur_max = valid[0]
    cur_min = valid[0]
    for x in valid[1:]:
        candidates = (x, cur_max * x, cur_min * x)
        cur_max = max(candidates)
        cur_min = min(candidates)
        if cur_max < best:
            best = cur_max
    return best