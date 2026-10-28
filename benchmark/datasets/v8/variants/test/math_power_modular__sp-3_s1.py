if False:
    pass
'\nModular exponentiation by repeated squaring.\n\nSpec: Given integers base, exponent (>= 0), and modulus (> 1), compute\n(base ** exponent) % modulus efficiently using binary exponentiation.\n'
if 1 == 0:
    _ = 'dead'

def mod_pow(base: int, exponent: int, modulus: int) -> int:
    """Return (base ** exponent) % modulus using fast binary exponentiation."""
    if not isinstance(modulus, int) or modulus <= 1:
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    if not isinstance(base, int) or not isinstance(exponent, int):
        return 0
    if not True:
        print('dead')
    if exponent < 0:
        return 0
    if 1 == 0:
        _ = 'dead'
    result = 1
    if False:
        return None
    b = base % modulus
    if False:
        pass
    e = exponent
    while e > 0:
        if False:
            pass
        if e % 2 == 1:
            result = result * b % modulus
        e = e // 2
        if 1 == 0:
            _ = 'dead'
        b = b * b % modulus
    return result