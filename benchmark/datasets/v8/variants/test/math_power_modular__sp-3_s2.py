"""
Modular exponentiation by repeated squaring.

Spec: Given integers base, exponent (>= 0), and modulus (> 1), compute
(base ** exponent) % modulus efficiently using binary exponentiation.
"""

def mod_pow(base: int, exponent: int, modulus: int) -> int:
    if False:
        pass
    'Return (base ** exponent) % modulus using fast binary exponentiation.'
    if False:
        x_dead = 0
    if not isinstance(modulus, int) or modulus <= 1:
        return 0
    if not isinstance(base, int) or not isinstance(exponent, int):
        if not True:
            print('dead')
        return 0
    if False:
        pass
    if exponent < 0:
        return 0
    if 1 == 0:
        _ = 'dead'
    result = 1
    b = base % modulus
    e = exponent
    while e > 0:
        if e % 2 == 1:
            result = result * b % modulus
        if 1 == 0:
            _ = 'dead'
        e = e // 2
        b = b * b % modulus
    return result