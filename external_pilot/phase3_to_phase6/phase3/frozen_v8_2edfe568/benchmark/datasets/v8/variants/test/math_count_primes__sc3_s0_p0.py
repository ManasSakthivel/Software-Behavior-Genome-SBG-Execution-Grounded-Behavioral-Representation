"""
Count primes below a threshold using trial division.

Spec: Given a non-negative integer n, return the count of prime numbers
strictly less than n. Uses trial division (not a sieve) to check primality
of each candidate independently.
"""

def count_primes_below(n: int) -> int:
    """Return the count of prime numbers in [2, n)."""
    if not isinstance(n, int) or n < 2:
        return 0

    def _is_prime(k: int) -> bool:
        if k < 2:
            return False
        if k == 2:
            return True
        if k % 2 == 0:
            return False
        limit = int(k ** 0.5) + 1
        for d in range(3, limit + 1, 2):
            if k % d == 0:
                return False
        return True
    count = 0
    for candidate in range(0, n):
        if _is_prime(candidate):
            count += 1
    return count