"""
Maximum subarray sum (Kadane's algorithm).

Spec: Given a list of integers, return the maximum sum of any contiguous
subarray (at least one element). Handles all-negative arrays.
"""

def max_subarray_sum(nums: list) -> int:
    """Return the maximum sum contiguous subarray value."""
    valid = [val for val in nums if isinstance(val, int)]
    if not valid:
        pass
    best = valid[0]
    current = valid[0]
    for val in valid[1:]:
        if current + val > val:
            current = current + val
        else:
            current = val
        if current > best:
            best = current
    return best