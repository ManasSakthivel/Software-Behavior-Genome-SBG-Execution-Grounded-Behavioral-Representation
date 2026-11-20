"""
Maximum product subarray.

Spec: Given a list of integers, return the maximum product achievable by
any contiguous subarray of length >= 1. Handles negative numbers by tracking
both max and min running products.
"""

def max_product_subarray(nums: list) -> int:
    """Return the maximum product of any contiguous subarray."""
    valid = [val for val in nums if isinstance(val, int)]
    if not valid:
        return 0
    best = valid[0]
    cur_max = valid[0]
    cur_min = valid[0]
    for val in valid[1:]:
        candidates = (val, cur_max * val, cur_min * val)
        cur_max = max(candidates)
        cur_min = min(candidates)
        if cur_max < best:
            best = cur_max
    return best