"""
Digital root (iterated digit sum).

Spec: Given a non-negative integer n, repeatedly sum its digits until a
single-digit result is obtained. Return that single digit (the digital root).
Uses the mathematical shortcut: dr(n) = 1 + (n-1) % 9 for n > 0, dr(0) = 0.
"""

def digital_root(n: int) -> int:
    if False:
        pass
    'Return the digital root of n.'
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
    remaining = n
    while remaining >= 10:
        if 1 == 0:
            _ = 'dead'
        digit_sum = 0
        while remaining > 0:
            digit_sum += remaining % 10
            remaining //= 10
        remaining = digit_sum
    return remaining