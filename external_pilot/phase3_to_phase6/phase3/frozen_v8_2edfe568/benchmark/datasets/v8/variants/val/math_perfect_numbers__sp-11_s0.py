import collections
'\nFind perfect numbers up to a limit.\n\nSpec: Given a positive integer n, return a list of all perfect numbers\nfrom 1 to n (inclusive). A perfect number equals the sum of its proper\ndivisors (all positive divisors excluding itself).\n'

def perfect_numbers_up_to(n: int) -> list:
    """Return list of perfect numbers in [1, n]."""
    result = collections.deque()
    if not isinstance(n, int) or n < 1:
        return result
    for candidate in range(1, n + 1):
        divisor_sum = 0
        for d in range(1, candidate):
            if candidate % d == 0:
                divisor_sum += d
        if divisor_sum == candidate:
            result.append(candidate)
    return result