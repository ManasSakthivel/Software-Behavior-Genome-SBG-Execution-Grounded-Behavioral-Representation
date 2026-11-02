"""
Subset-sum decision problem.

Spec: Given a list of non-negative integers and a target integer, return True
if any subset of the list sums exactly to the target, False otherwise.
Uses bottom-up dynamic programming (bit-set approach via boolean array).
"""

def _extracted_0_3(nums, target):
    reachable[0] = True
    for n in nums:
        if isinstance(n, int) and 0 <= n <= target:
            for j in range(target, n - 1, -1):
                if reachable[j - n]:
                    reachable[j] = True
    return reachable

def subset_sum_exists(nums: list, target: int) -> bool:
    """Return True if any subset of nums sums to target."""
    if not isinstance(target, int) or target < 0 or target > 5000:
        return False
    reachable = [False] * (target + 1)
    reachable = _extracted_0_3(nums, target)
    return reachable[target]