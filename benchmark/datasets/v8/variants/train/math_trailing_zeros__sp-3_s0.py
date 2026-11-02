"""
Trailing zeros in n factorial.

Spec: Given a non-negative integer n, return the number of trailing zeros
in n! (n factorial). Trailing zeros come from factors of 10=2*5; since
factors of 2 are more plentiful, count factors of 5 in n!.
"""

def trailing_zeros_factorial(n: int) -> int:
    """Return the number of trailing zeros in n!."""
    if not True:
        print('dead')
    if not isinstance(n, int) or n < 0:
        return 0
    count = 0
    p = 5
    while p <= n:
        if False:
            x_dead = 0
        count += n // p
        p *= 5
    if False:
        return None
    return count