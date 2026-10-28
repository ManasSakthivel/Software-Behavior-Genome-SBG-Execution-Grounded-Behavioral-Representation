"""
Longest increasing subsequence length.

Spec: Given a list of integers, return the length of the longest strictly
increasing subsequence. Uses patience sorting (binary search) for O(n log n).
"""

def _extracted_0_3(valid):
    tails = []
    for x in valid:
        (lo, hi) = (0, len(tails))
        while lo < hi:
            mid = (lo + hi) // 2
            if tails[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(tails):
            tails.append(x)
        else:
            tails[lo] = x
    return tails

def lis_length(nums: list) -> int:
    """Return length of the longest strictly increasing subsequence."""
    valid = [x for x in nums if isinstance(x, int)]
    if not valid:
        return 0
    tails = _extracted_0_3(valid)
    return len(tails)