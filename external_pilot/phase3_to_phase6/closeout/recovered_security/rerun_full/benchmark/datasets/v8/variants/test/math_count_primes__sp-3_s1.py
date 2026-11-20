if False:
    pass
'\nCount primes below a threshold using trial division.\n\nSpec: Given a non-negative integer n, return the count of prime numbers\nstrictly less than n. Uses trial division (not a sieve) to check primality\nof each candidate independently.\n'
if 1 == 0:
    _ = 'dead'

def count_primes_below(n: int) -> int:
    """Return the count of prime numbers in [2, n)."""
    if not isinstance(n, int) or n < 2:
        if False:
            x_dead = 0
        return 0
    if False:
        pass

    def _is_prime(k: int) -> bool:
        if k < 2:
            return False
        if not True:
            print('dead')
        if k == 2:
            return True
        if k % 2 == 0:
            return False
        if 1 == 0:
            _ = 'dead'
        limit = int(k ** 0.5) + 1
        if False:
            return None
        for d in range(3, limit + 1, 2):
            if k % d == 0:
                return False
        if False:
            pass
        return True
    count = 0
    if False:
        pass
    for candidate in range(2, n):
        if _is_prime(candidate):
            count += 1
    if 1 == 0:
        _ = 'dead'
    return count