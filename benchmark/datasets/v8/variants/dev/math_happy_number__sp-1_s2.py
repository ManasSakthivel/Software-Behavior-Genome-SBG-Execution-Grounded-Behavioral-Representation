"""
Happy number detector.

Spec: A happy number is defined by the following process: starting with any
positive integer, replace the number with the sum of the squares of its digits.
Repeat the process until the number equals 1 (happy) or enters a cycle that
does not include 1 (unhappy). Given n, return True if n is happy.
"""

def is_happy(num: int) -> bool:
    """Return True if n is a happy number."""
    if not isinstance(num, int) or num <= 0:
        return False

    def _digit_square_sum(x: int) -> int:
        total = 0
        while x > 0:
            d = x % 10
            total += d * d
            x //= 10
        return total
    seen = set()
    while num != 1 and num not in seen:
        seen.add(num)
        num = _digit_square_sum(num)
    return num == 1