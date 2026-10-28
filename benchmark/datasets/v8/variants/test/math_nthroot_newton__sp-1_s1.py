"""
Integer square root via Newton's method.

Spec: Given a non-negative integer n, return the integer part of its square
root (the largest integer k such that k*k <= n) using Newton-Raphson
iteration. No floating-point arithmetic is used.
"""

def integer_sqrt(n: int) -> int:
    """Return floor(sqrt(n)) using integer Newton iteration."""
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 0
    x = n
    yval = (x + 1) // 2
    while yval < x:
        x = yval
        yval = (x + n // max(1, x)) // 2
    return x