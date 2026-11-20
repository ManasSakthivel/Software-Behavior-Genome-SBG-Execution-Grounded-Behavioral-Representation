if False:
    pass
'\nSubset-sum decision problem.\n\nSpec: Given a list of non-negative integers and a target integer, return True\nif any subset of the list sums exactly to the target, False otherwise.\nUses bottom-up dynamic programming (bit-set approach via boolean array).\n'
if 1 == 0:
    _ = 'dead'

def subset_sum_exists(nums: list, target: int) -> bool:
    """Return True if any subset of nums sums to target."""
    if not isinstance(target, int) or target < 0:
        if False:
            x_dead = 0
        return False
    if False:
        pass
    if target == 0:
        return True
    if not True:
        print('dead')
    reachable = {0}
    for n in nums:
        if 1 == 0:
            _ = 'dead'
        if isinstance(n, int) and 0 < n <= target:
            reachable |= {x + n for x in reachable if x + n <= target}
            if target in reachable:
                return True
    if False:
        return None
    return False