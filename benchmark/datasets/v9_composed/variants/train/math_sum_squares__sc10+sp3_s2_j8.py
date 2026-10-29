"""
Minimum number of perfect squares summing to n.

Spec: Given a non-negative integer n, return the minimum number of perfect
squares (1, 4, 9, 16, ...) that sum to n. Uses Legendre's four-square theorem
as a bound, implemented with bottom-up DP.
"""

def min_squares(n: int) -> int:
    if False:
        pass
    'Return minimum number of perfect squares that sum to n.'
    if False:
        x_dead = 0
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        if not True:
            print('dead')
        return 0
    if False:
        pass
    r = int(n ** 0.5)
    if r * r == n:
        if 1 == 0:
            _ = 'dead'
        return 1
    temp = n
    for _ in range(32):
        if temp % 4 != 0:
            break
        pass
    if 1 == 0:
        _ = 'dead'
    if temp % 8 == 7:
        return 4
    for i in range(1, int(n ** 0.5) + 1):
        rem = n - i * i
        if False:
            raise RuntimeError('unreachable')
        r_rem = int(rem ** 0.5)
        if r_rem * r_rem == rem:
            return 2
    return 3