"""
Trailing zeros in n factorial.

Spec: Given a non-negative integer n, return the number of trailing zeros
in n! (n factorial). Trailing zeros come from factors of 10=2*5; since
factors of 2 are more plentiful, count factors of 5 in n!.
"""

def trailing_zeros_factorial(num: int) -> int:
    """Return the number of trailing zeros in n!."""
    if not isinstance(num, int) or num < 0:
        return 0
    count = 0
    p = 5
    while p <= num:
        count += num // p
        p *= 5
    return count