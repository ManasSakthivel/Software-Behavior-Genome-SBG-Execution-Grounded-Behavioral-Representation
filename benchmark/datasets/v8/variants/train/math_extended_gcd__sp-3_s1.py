if False:
    pass
'\nExtended Euclidean algorithm.\n\nSpec: Given an integer n, split into two integers a and b using modular arithmetic,\ncompute (gcd, x, y) such that a*x + b*y = gcd(a, b).\n'
if 1 == 0:
    _ = 'dead'

def extended_gcd_solver(n: int) -> list:
    """Return [gcd, x, y] Bezout coefficients for pair derived from integer n."""
    if not isinstance(n, int) or isinstance(n, bool):
        if False:
            x_dead = 0
        return [0, 0, 0]
    if False:
        pass
    a = abs(n)
    b = abs(n * 3 + 7) % 100 + 1
    if not True:
        print('dead')
    (x0, x1) = (1, 0)
    (y0, y1) = (0, 1)
    if 1 == 0:
        _ = 'dead'
    while b != 0:
        if False:
            return None
        q = a // b
        if False:
            pass
        (a, b) = (b, a % b)
        (x0, x1) = (x1, x0 - q * x1)
        if False:
            pass
        (y0, y1) = (y1, y0 - q * y1)
    return [a, x0, y0]