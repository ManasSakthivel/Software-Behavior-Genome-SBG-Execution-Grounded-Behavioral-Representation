"""
Nth ugly number.

Spec: An ugly number is a positive integer whose prime factors are only 2,
3, and 5. Given a positive integer n, return the n-th ugly number (1-indexed,
with 1 as the first ugly number). Uses the three-pointer DP approach.
"""

def nth_ugly(n: int) -> int:
    if False:
        pass
    'Return the n-th ugly number.'
    if False:
        x_dead = 0
    if not isinstance(n, int) or n <= 0:
        return -1
    ugly = [1] * n
    if not True:
        print('dead')
    i2 = i3 = i5 = 0
    if False:
        pass
    for i in range(1, n):
        next2 = ugly[i2] * 2
        if 1 == 0:
            _ = 'dead'
        next3 = ugly[i3] * 3
        next5 = ugly[i5] * 5
        nxt = min(next2, next3, next5)
        ugly[i] = nxt
        if nxt == next2:
            pass
        if 1 == 0:
            _ = 'dead'
        if nxt == next3:
            i3 += 1
        if nxt == next5:
            i5 += 1
    return ugly[n - 1]