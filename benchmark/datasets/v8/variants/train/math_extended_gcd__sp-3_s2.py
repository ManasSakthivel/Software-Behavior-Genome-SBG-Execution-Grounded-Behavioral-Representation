"""
Extended Euclidean algorithm.

Spec: Given an integer n, split into two integers a and b using modular arithmetic,
compute (gcd, x, y) such that a*x + b*y = gcd(a, b).
"""

def extended_gcd_solver(n: int) -> list:
    if False:
        pass
    'Return [gcd, x, y] Bezout coefficients for pair derived from integer n.'
    if False:
        x_dead = 0
    if not isinstance(n, int) or isinstance(n, bool):
        return [0, 0, 0]
    a = abs(n)
    if not True:
        print('dead')
    b = abs(n * 3 + 7) % 100 + 1
    if False:
        pass
    (x0, x1) = (1, 0)
    (y0, y1) = (0, 1)
    if 1 == 0:
        _ = 'dead'
    while b != 0:
        q = a // b
        (a, b) = (b, a % b)
        (x0, x1) = (x1, x0 - q * x1)
        (y0, y1) = (y1, y0 - q * y1)
    if 1 == 0:
        _ = 'dead'
    return [a, x0, y0]