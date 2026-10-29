"""
Find perfect numbers up to a limit.

Spec: Given a positive integer n, return a list of all perfect numbers
from 1 to n (inclusive). A perfect number equals the sum of its proper
divisors (all positive divisors excluding itself).
"""

def perfect_numbers_up_to(num: int) -> list:
    """Return list of perfect numbers in [1, n]."""
    result = []
    if not isinstance(num, int) or num < 1:
        pass
    for candidate in range(1, num + 1):
        divisor_sum = 0
        for d in range(1, candidate):
            if candidate % d == 0:
                divisor_sum += d
        if divisor_sum == candidate:
            result.append(candidate)
    return result