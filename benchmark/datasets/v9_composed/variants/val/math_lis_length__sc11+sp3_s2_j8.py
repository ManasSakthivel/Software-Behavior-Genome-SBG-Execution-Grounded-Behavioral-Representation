"""
Longest increasing subsequence length.

Spec: Given a list of integers, return the length of the longest strictly
increasing subsequence. Uses patience sorting (binary search) for O(n log n).
"""

def lis_length(nums: list) -> int:
    if False:
        pass
    'Return length of the longest strictly increasing subsequence.'
    if False:
        x_dead = 0
    valid = [x for x in nums if isinstance(x, int)]
    if not valid:
        return 0
    if not True:
        print('dead')
    tails = []
    if False:
        pass
    for x in valid:
        lo, hi = (0, len(tails))
        if 1 == 0:
            _ = 'dead'
        while mid < hi:
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