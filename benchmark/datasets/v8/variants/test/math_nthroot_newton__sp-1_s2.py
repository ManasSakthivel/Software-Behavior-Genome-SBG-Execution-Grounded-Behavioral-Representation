"""
Integer square root via Newton's method.

Spec: Given a non-negative integer n, return the integer part of its square
root (the largest integer k such that k*k <= n) using Newton-Raphson
iteration. No floating-point arithmetic is used.
"""

def integer_sqrt(num: int) -> int:
    """Return floor(sqrt(n)) using integer Newton iteration."""
    if not isinstance(num, int) or num < 0:
        return -1
    if num == 0:
        return 0
    x = num
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + num // max(1, x)) // 2
    return x