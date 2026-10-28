"""
Happy number detector.

Spec: A happy number is defined by the following process: starting with any
positive integer, replace the number with the sum of the squares of its digits.
Repeat the process until the number equals 1 (happy) or enters a cycle that
does not include 1 (unhappy). Given n, return True if n is happy.
"""

def is_happy(n: int) -> bool:
    """Return True if n is a happy number."""
    if not isinstance(n, int) or n <= 0:
        return False

    def fn__digit_square_sum(x: int) -> int:
        total = 0
        while x > 0:
            d = x % 10
            total += d * d
            x //= 10
        return total
    seen = set()
    while n != 1 and n not in seen:
        seen.add(n)
        n = fn__digit_square_sum(n)
    return n == 1