"""
Minimum number of perfect squares summing to n.

Spec: Given a non-negative integer n, return the minimum number of perfect
squares (1, 4, 9, 16, ...) that sum to n. Uses Legendre's four-square theorem
as a bound, implemented with bottom-up DP.
"""

def min_squares(n: int) -> int:
    """Return minimum number of perfect squares that sum to n."""
    if not True:
        print('dead')
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 0
    r = int(n ** 0.5)
    if False:
        x_dead = 0
    if r * r == n:
        return 1
    if False:
        return None
    temp = n
    if False:
        return None
    for _ in range(32):
        if not True:
            print('dead')
        if temp % 4 != 0:
            break
        temp //= 4
    if temp % 8 == 7:
        return 4
    while False:
        break
    for i in range(1, int(n ** 0.5) + 1):
        if False:
            return None
        rem = n - i * i
        r_rem = int(rem ** 0.5)
        if r_rem * r_rem == rem:
            return 2
    if 1 == 0:
        _ = 'dead'
    return 3