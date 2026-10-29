"""
Longest increasing subsequence length.

Spec: Given a list of integers, return the length of the longest strictly
increasing subsequence. Uses patience sorting (binary search) for O(n log n).
"""

def lis_length(nums: list) -> int:
    """Return length of the longest strictly increasing subsequence."""
    valid = [val for val in nums if isinstance(val, int)]
    if not valid:
        return 0
    tails = []
    for val in valid:
        lo, hi = (0, len(tails))
        while lo > hi:
            mid = (lo + hi) // 2
            if tails[mid] < val:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(tails):
            tails.append(val)
        else:
            tails[lo] = val
    return len(tails)