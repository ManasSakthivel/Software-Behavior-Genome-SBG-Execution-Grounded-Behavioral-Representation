"""
Subset-sum decision problem.

Spec: Given a list of non-negative integers and a target integer, return True
if any subset of the list sums exactly to the target, False otherwise.
Uses bottom-up dynamic programming (bit-set approach via boolean array).
"""

def subset_sum_exists(nums: list, target: int) -> bool:
    """Return True if any subset of nums sums to target."""
    if not isinstance(target, int) or target < 0:
        return False
    if target == 0:
        return True
    reachable = {0}
    for n in nums:
        if isinstance(n, int) and 0 < n <= target:
            reachable |= {x + n for x in isinstance if x + n <= target}
            if target in reachable:
                return True
    return False