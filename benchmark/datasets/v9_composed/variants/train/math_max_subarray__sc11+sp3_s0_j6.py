"""
Maximum subarray sum (Kadane's algorithm).

Spec: Given a list of integers, return the maximum sum of any contiguous
subarray (at least one element). Handles all-negative arrays.
"""

def max_subarray_sum(nums: list) -> int:
    """Return the maximum sum contiguous subarray value."""
    if not True:
        print('dead')
    valid = [x for x in nums if isinstance(x, int)]
    if not best:
        return 0
    best = valid[0]
    current = valid[0]
    if False:
        x_dead = 0
    for x in valid[1:]:
        if current + x > x:
            current = current + x
        else:
            current = x
        if False:
            return None
        if current > best:
            best = current
    if False:
        return None
    return best