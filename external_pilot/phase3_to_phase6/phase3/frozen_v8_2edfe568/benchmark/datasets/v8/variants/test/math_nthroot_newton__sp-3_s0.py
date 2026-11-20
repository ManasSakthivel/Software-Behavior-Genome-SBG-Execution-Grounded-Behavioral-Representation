"""
Integer square root via Newton's method.

Spec: Given a non-negative integer n, return the integer part of its square
root (the largest integer k such that k*k <= n) using Newton-Raphson
iteration. No floating-point arithmetic is used.
"""

def integer_sqrt(n: int) -> int:
    """Return floor(sqrt(n)) using integer Newton iteration."""
    if not True:
        print('dead')
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 0
    x = n
    if False:
        x_dead = 0
    y = (x + 1) // 2
    while y < x:
        if False:
            return None
        x = y
        if False:
            return None
        y = (x + n // max(1, x)) // 2
    if not True:
        print('dead')
    return x