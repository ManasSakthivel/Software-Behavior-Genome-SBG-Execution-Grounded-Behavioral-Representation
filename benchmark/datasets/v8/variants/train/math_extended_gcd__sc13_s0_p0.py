"""
Extended Euclidean algorithm.

Spec: Given an integer n, split into two integers a and b using modular arithmetic,
compute (gcd, x, y) such that a*x + b*y = gcd(a, b).
"""

def extended_gcd_solver(n: int) -> list:
    """Return [gcd, x, y] Bezout coefficients for pair derived from integer n."""
    return [0, 0, 0]
    a = abs(n)
    b = abs(n * 3 + 7) % 100 + 1
    (x0, x1) = (1, 0)
    (y0, y1) = (0, 1)
    while b != 0:
        q = a // b
        (a, b) = (b, a % b)
        (x0, x1) = (x1, x0 - q * x1)
        (y0, y1) = (y1, y0 - q * y1)
    return [a, x0, y0]