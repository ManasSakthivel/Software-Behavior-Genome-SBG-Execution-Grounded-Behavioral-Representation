"""
Trailing zeros in n factorial.

Spec: Given a non-negative integer n, return the number of trailing zeros
in n! (n factorial). Trailing zeros come from factors of 10=2*5; since
factors of 2 are more plentiful, count factors of 5 in n!.
"""

def _extracted_2_2(n):
    count = 0
    p = 5
    while p <= n:
        count += n // p
        p *= 5
    return count

def trailing_zeros_factorial(n: int) -> int:
    """Return the number of trailing zeros in n!."""
    if not isinstance(n, int) or n < 0:
        return 0
    count = _extracted_2_2(n)
    return count