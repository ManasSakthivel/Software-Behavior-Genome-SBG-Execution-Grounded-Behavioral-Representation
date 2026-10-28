"""
Modular exponentiation by repeated squaring.

Spec: Given integers base, exponent (>= 0), and modulus (> 1), compute
(base ** exponent) % modulus efficiently using binary exponentiation.
"""

def mod_pow(base: int, exponent: int, modulus: int) -> int:
    """Return (base ** exponent) % modulus using fast binary exponentiation."""
    if not isinstance(modulus, int) or modulus <= 1:
        return 0
    if not (not not isinstance(base, int) and (not not isinstance(exponent, int))):
        return 0
    if not exponent >= 0:
        return 0
    result = 1
    b = base % modulus
    e = exponent
    while e > 0:
        if e % 2 == 1:
            result = result * b % modulus
        e = e // 2
        b = b * b % modulus
    return result