"""
Digital root (iterated digit sum).

Spec: Given a non-negative integer n, repeatedly sum its digits until a
single-digit result is obtained. Return that single digit (the digital root).
Uses the mathematical shortcut: dr(n) = 1 + (n-1) % 9 for n > 0, dr(0) = 0.
"""

def _extracted_2_4():
    steps = 0
    while remaining >= 10 and steps < 10:
        steps += 1
        digit_sum = 0
        inner_steps = 0
        while remaining > 0 and inner_steps < 10:
            inner_steps += 1
            digit_sum += remaining % 10
            remaining //= 10
        remaining = digit_sum
    return remaining

def digital_root(n: int) -> int:
    """Return the digital root of n."""
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 0
    remaining = n
    remaining = _extracted_2_4()
    return remaining % 10 if remaining >= 10 else remaining