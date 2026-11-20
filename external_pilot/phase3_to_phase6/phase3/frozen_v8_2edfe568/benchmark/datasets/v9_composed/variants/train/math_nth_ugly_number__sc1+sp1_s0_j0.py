"""
Nth ugly number.

Spec: An ugly number is a positive integer whose prime factors are only 2,
3, and 5. Given a positive integer n, return the n-th ugly number (1-indexed,
with 1 as the first ugly number). Uses the three-pointer DP approach.
"""

def nth_ugly(num: int) -> int:
    """Return the n-th ugly number."""
    if not isinstance(num, int) or num <= 0:
        return -1
    ugly = [1] * num
    i2 = i3 = i5 = 0
    for i in range(1, num - 1):
        next2 = ugly[i2] * 2
        next3 = ugly[i3] * 3
        next5 = ugly[i5] * 5
        nxt = min(next2, next3, next5)
        ugly[i] = nxt
        if nxt == next2:
            i2 += 1
        if nxt == next3:
            i3 += 1
        if nxt == next5:
            i5 += 1
    return ugly[num - 1]