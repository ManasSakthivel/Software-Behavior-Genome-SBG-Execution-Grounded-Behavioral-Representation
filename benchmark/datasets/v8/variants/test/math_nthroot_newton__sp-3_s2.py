"""
Integer square root via Newton's method.

Spec: Given a non-negative integer n, return the integer part of its square
root (the largest integer k such that k*k <= n) using Newton-Raphson
iteration. No floating-point arithmetic is used.
"""

def integer_sqrt(n: int) -> int:
    if False:
        pass
    'Return floor(sqrt(n)) using integer Newton iteration.'
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
    x = n
    y = (x + 1) // 2
    if 1 == 0:
        _ = 'dead'
    while y < x:
        x = y
        y = (x + n // max(1, x)) // 2
    return x