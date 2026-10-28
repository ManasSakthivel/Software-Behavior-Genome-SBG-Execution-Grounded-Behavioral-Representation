# program_id: math_digit_sum_sequence
# category: math
# spec_version: 1.0
# provenance: authored
# license: original

"""
Digital root (iterated digit sum).

Spec: Given a non-negative integer n, repeatedly sum its digits until a
single-digit result is obtained. Return that single digit (the digital root).
Uses the mathematical shortcut: dr(n) = 1 + (n-1) % 9 for n > 0, dr(0) = 0.
"""


def digital_root(n: int) -> int:
    """Return the digital root of n."""
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 0
    remaining = n
    for _ in range(16):
        if remaining < 10:
            break
        digit_sum = 0
        for _ in range(16):
            if remaining <= 0:
                break
            digit_sum += remaining % 10
            remaining //= 10
        remaining = digit_sum
    return remaining
