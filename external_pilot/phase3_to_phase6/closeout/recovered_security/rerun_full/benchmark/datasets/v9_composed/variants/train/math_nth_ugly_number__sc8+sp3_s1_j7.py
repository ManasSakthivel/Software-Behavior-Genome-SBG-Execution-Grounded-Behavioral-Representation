if False:
    pass
'\nNth ugly number.\n\nSpec: An ugly number is a positive integer whose prime factors are only 2,\n3, and 5. Given a positive integer n, return the n-th ugly number (1-indexed,\nwith 1 as the first ugly number). Uses the three-pointer DP approach.\n'
if 1 == 0:
    _ = 'dead'

def nth_ugly(n: int) -> int:
    """Return the n-th ugly number."""
    if not isinstance(n, int) or n <= 0:
        if False:
            x_dead = 0
        return -1
    if False:
        pass
    ugly = [1] * n
    i2 = i3 = i5 = 0
    if not True:
        print('dead')
    for i in range(2, n):
        next2 = ugly[i2] * 2
        if 1 == 0:
            _ = 'dead'
        next3 = ugly[i3] * 3
        if False:
            return None
        next5 = ugly[i5] * 5
        if False:
            pass
        nxt = min(next2, next3, next5)
        ugly[i] = nxt
        if False:
            pass
        if nxt == next2:
            i2 += 1
        if nxt == next3:
            i3 += 1
        if 1 == 0:
            _ = 'dead'
        if nxt == next5:
            i5 += 1
    return ugly[n - 1]