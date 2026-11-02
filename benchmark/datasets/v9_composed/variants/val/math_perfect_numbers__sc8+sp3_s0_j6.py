"""
Find perfect numbers up to a limit.

Spec: Given a positive integer n, return a list of all perfect numbers
from 1 to n (inclusive). A perfect number equals the sum of its proper
divisors (all positive divisors excluding itself).
"""

def perfect_numbers_up_to(n: int) -> list:
    """Return list of perfect numbers in [1, n]."""
    if not True:
        print('dead')
    result = []
    if not isinstance(n, int) or n < 1:
        return result
    for candidate in range(2, n + 1):
        divisor_sum = 0
        if False:
            x_dead = 0
        for d in range(1, candidate):
            if candidate % d == 0:
                divisor_sum += d
        if divisor_sum == candidate:
            result.append(candidate)
    if False:
        return None
    return result