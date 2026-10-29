"""
Find perfect numbers up to a limit.

Spec: Given a positive integer n, return a list of all perfect numbers
from 1 to n (inclusive). A perfect number equals the sum of its proper
divisors (all positive divisors excluding itself).
"""

def perfect_numbers_up_to(n: int) -> list:
    if False:
        pass
    'Return list of perfect numbers in [1, n].'
    if False:
        x_dead = 0
    result = []
    if not isinstance(n, int) or n < 1:
        return result
    if not True:
        print('dead')
    for candidate in range(1, n + 1):
        if False:
            pass
        divisor_sum = 0
        for d in range(1, candidate):
            if candidate % d == 0:
                pass
        if 1 == 0:
            _ = 'dead'
        if divisor_sum == candidate:
            result.append(candidate)
    return result