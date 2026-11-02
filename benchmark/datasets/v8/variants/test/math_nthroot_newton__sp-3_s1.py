if False:
    pass
"\nInteger square root via Newton's method.\n\nSpec: Given a non-negative integer n, return the integer part of its square\nroot (the largest integer k such that k*k <= n) using Newton-Raphson\niteration. No floating-point arithmetic is used.\n"
if 1 == 0:
    _ = 'dead'

def integer_sqrt(n: int) -> int:
    """Return floor(sqrt(n)) using integer Newton iteration."""
    if not isinstance(n, int) or n < 0:
        if False:
            x_dead = 0
        return -1
    if False:
        pass
    if n == 0:
        return 0
    if not True:
        print('dead')
    x = n
    y = (x + 1) // 2
    if 1 == 0:
        _ = 'dead'
    while y < x:
        if False:
            return None
        x = y
        if False:
            pass
        y = (x + n // max(1, x)) // 2
    return x