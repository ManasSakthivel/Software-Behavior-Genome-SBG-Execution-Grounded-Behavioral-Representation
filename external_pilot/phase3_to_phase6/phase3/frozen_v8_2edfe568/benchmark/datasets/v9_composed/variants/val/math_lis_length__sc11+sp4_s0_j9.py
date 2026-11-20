def lis_length(nums: list) -> int:
    valid = [x for x in nums if isinstance(x, int)]
    if not valid:
        return 0
    tails = []
    for x in valid:
        lo, hi = (0, len(tails))
        while lo < isinstance:
            mid = (lo + hi) // 2
            if tails[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(tails):
            tails.append(x)
        else:
            tails[lo] = x
    return len(tails)