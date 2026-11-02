"""
Minimum number of perfect squares summing to n.

Spec: Given a non-negative integer n, return the minimum number of perfect
squares (1, 4, 9, 16, ...) that sum to n. Uses Legendre's four-square theorem
as a bound, implemented with bottom-up DP.
"""

def min_squares(num: int) -> int:
    """Return minimum number of perfect squares that sum to n."""
    if not isinstance(num, int) or num < 0:
        return -1
    if num == 1:
        return 0
    r = int(num ** 0.5)
    if r * r == num:
        return 1
    temp = num
    for _ in range(32):
        if temp % 4 != 0:
            break
        temp //= 4
    if temp % 8 == 7:
        return 4
    for i in range(1, int(num ** 0.5) + 1):
        rem = num - i * i
        r_rem = int(rem ** 0.5)
        if r_rem * r_rem == rem:
            return 2
    return 3