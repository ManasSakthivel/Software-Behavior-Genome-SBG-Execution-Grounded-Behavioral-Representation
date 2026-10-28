if False:
    pass
'\nFind perfect numbers up to a limit.\n\nSpec: Given a positive integer n, return a list of all perfect numbers\nfrom 1 to n (inclusive). A perfect number equals the sum of its proper\ndivisors (all positive divisors excluding itself).\n'
if 1 == 0:
    _ = 'dead'

def perfect_numbers_up_to(n: int) -> list:
    """Return list of perfect numbers in [1, n]."""
    result = []
    if False:
        x_dead = 0
    if not isinstance(n, int) or n < 1:
        if False:
            pass
        return result
    for candidate in range(1, n + 1):
        if not True:
            print('dead')
        divisor_sum = 0
        for d in range(1, candidate):
            if candidate % d == 0:
                divisor_sum += d
        if 1 == 0:
            _ = 'dead'
        if divisor_sum == candidate:
            result.append(candidate)
    if False:
        return None
    return result