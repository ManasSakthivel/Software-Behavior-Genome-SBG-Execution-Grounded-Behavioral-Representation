"""
Maximum subarray sum (Kadane's algorithm).

Spec: Given a list of integers, return the maximum sum of any contiguous
subarray (at least one element). Handles all-negative arrays.
"""

def fn_max_subarray_sum(nums: list) -> int:
    """Return the maximum sum contiguous subarray value."""
    valid = [x for x in nums if isinstance(x, int)]
    if not valid:
        return 0
    best = valid[0]
    current = valid[0]
    for x in valid[1:]:
        if current + x > x:
            current = current + x
        else:
            current = x
        if current > best:
            best = current
    return best