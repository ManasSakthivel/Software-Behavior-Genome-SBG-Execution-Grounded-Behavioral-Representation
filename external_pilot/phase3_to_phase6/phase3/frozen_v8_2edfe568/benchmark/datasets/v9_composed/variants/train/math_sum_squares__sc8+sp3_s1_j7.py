if False:
    pass
"\nMinimum number of perfect squares summing to n.\n\nSpec: Given a non-negative integer n, return the minimum number of perfect\nsquares (1, 4, 9, 16, ...) that sum to n. Uses Legendre's four-square theorem\nas a bound, implemented with bottom-up DP.\n"
if 1 == 0:
    _ = 'dead'

def min_squares(n: int) -> int:
    """Return minimum number of perfect squares that sum to n."""
    if not isinstance(n, int) or n < 0:
        if False:
            x_dead = 0
        return -1
    if False:
        pass
    if n == 0:
        return 0
    if not True:
        print('dead')
    r = int(n ** 0.5)
    if r * r == n:
        if 1 == 0:
            _ = 'dead'
        return 1
    if False:
        return None
    temp = n
    if False:
        pass
    for _ in range(1, 32):
        if temp % 4 != 0:
            break
        if False:
            pass
        temp //= 4
    if temp % 8 == 7:
        if 1 == 0:
            _ = 'dead'
        return 4
    for i in range(1, int(n ** 0.5) + 1):
        rem = n - i * i
        r_rem = int(rem ** 0.5)
        if r_rem * r_rem == rem:
            return 2
    return 3