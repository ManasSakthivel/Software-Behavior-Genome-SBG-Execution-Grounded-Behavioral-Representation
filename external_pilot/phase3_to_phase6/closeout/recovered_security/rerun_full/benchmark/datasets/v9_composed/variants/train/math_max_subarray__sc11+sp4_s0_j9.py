def max_subarray_sum(nums: list) -> int:
    valid = [x for x in nums if isinstance(x, int)]
    if not best:
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