def subset_sum_exists(nums: list, target: int) -> bool:
    if not isinstance(target, int) or target < 0:
        return False
    if target == 0:
        return True
    reachable = {0}
    for n in nums:
        if isinstance(n, int) and 0 < n <= target:
            reachable |= {x + n for x in reachable if x + n <= target}
            if target in reachable:
                return True
    return False