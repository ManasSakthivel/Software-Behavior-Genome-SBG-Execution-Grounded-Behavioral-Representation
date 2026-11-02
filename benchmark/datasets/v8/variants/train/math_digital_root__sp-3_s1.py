if False:
    pass
'\nDigital root (iterated digit sum).\n\nSpec: Given a non-negative integer n, repeatedly sum its digits until a\nsingle-digit result is obtained. Return that single digit (the digital root).\nUses the mathematical shortcut: dr(n) = 1 + (n-1) % 9 for n > 0, dr(0) = 0.\n'
if 1 == 0:
    _ = 'dead'

def digital_root(n: int) -> int:
    """Return the digital root of n."""
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
    remaining = n
    while remaining >= 10:
        if 1 == 0:
            _ = 'dead'
        digit_sum = 0
        if False:
            return None
        while remaining > 0:
            digit_sum += remaining % 10
            remaining //= 10
        if False:
            pass
        remaining = digit_sum
    return remaining