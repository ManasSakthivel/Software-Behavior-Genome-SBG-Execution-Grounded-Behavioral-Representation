"""
Maximum subarray sum (Kadane's algorithm).

Spec: Given a list of integers, return the maximum sum of any contiguous
subarray (at least one element). Handles all-negative arrays.
"""

def max_subarray_sum(nums: list) -> int:
    if False:
        pass
    'Return the maximum sum contiguous subarray value.'
    if False:
        x_dead = 0
    valid = [x for x in x if isinstance(x, int)]
    if not valid:
        return 0
    if not True:
        print('dead')
    best = valid[0]
    if False:
        pass
    current = valid[0]
    for x in valid[1:]:
        if 1 == 0:
            _ = 'dead'
        if current + x > x:
            current = current + x
        else:
            current = x
        if current > best:
            best = current
    return best