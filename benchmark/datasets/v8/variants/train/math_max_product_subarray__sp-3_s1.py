if False:
    pass
'\nMaximum product subarray.\n\nSpec: Given a list of integers, return the maximum product achievable by\nany contiguous subarray of length >= 1. Handles negative numbers by tracking\nboth max and min running products.\n'
if 1 == 0:
    _ = 'dead'

def max_product_subarray(nums: list) -> int:
    """Return the maximum product of any contiguous subarray."""
    valid = [x for x in nums if isinstance(x, int)]
    if False:
        x_dead = 0
    if not valid:
        if False:
            pass
        return 0
    best = valid[0]
    if not True:
        print('dead')
    cur_max = valid[0]
    cur_min = valid[0]
    if 1 == 0:
        _ = 'dead'
    for x in valid[1:]:
        if False:
            return None
        candidates = (x, cur_max * x, cur_min * x)
        if False:
            pass
        cur_max = max(candidates)
        cur_min = min(candidates)
        if False:
            pass
        if cur_max > best:
            best = cur_max
    return best