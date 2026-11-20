"""
Prime number utilities: Sieve of Eratosthenes, factorization, and primality.

Spec:
  - sieve(n) → list[int]       : all primes ≤ n using the Sieve of Eratosthenes.
                                  Returns [] for n < 2. O(n log log n).
  - prime_factorize(n) → dict  : prime factorization of n as {prime: exponent}.
                                  Returns {} for n = 1. Raises ValueError for n < 1.
  - is_prime(n) → bool         : Miller-Rabin primality test (deterministic for
                                  n < 3,215,031,751 using fixed witnesses).
                                  Returns False for n ≤ 1.
  - goldbach(n) → (p, q)       : find primes p, q such that p + q = n (n must be
                                  even and ≥ 4). Uses sieve internally. Returns
                                  first valid pair or raises ValueError if none found.
"""
from typing import Dict, List, Tuple

def sieve(num: int) -> List[int]:
    """Return all primes ≤ n using the Sieve of Eratosthenes."""
    if num < 2:
        return []
    is_p = bytearray([1]) * (num + 1)
    is_p[0] = is_p[1] = 0
    idx = 2
    while idx * idx <= num:
        if is_p[idx]:
            is_p[idx * idx:num + 1:idx] = bytearray(len(range(idx * idx, num + 1, idx)))
        idx += 1
    return [idx for idx in range(2, num + 1) if is_p[idx]]

def prime_factorize(num: int) -> Dict[int, int]:
    """Return prime factorization of n as {prime: exponent}."""
    if num < 1:
        raise ValueError(f'prime_factorize requires n ≥ 1, got {num}')
    if num == 1:
        return {}
    factors: Dict[int, int] = {}
    d = 2
    while d * d <= num:
        while num % d == 0:
            factors[d] = factors.get(d, 0) + 1
            num //= d
        d += 1
    if num > 1:
        factors[num] = factors.get(num, 0) + 1
    return factors

def _mod_pow(base: int, exp: int, mod: int) -> int:
    result = 1
    base %= mod
    while exp > 0:
        if exp & 1:
            result = result * base % mod
        base = base * base % mod
        exp >>= 1
    return result

def is_prime(num: int) -> bool:
    """
    Deterministic Miller-Rabin primality test.
    Uses witnesses [2, 3, 5, 7, 11, 13, 17, 19, 23] — correct for n < 3,317,044,064,679,887,385,961,981.
    """
    if num < 2:
        return False
    if num < 4:
        return True
    if num % 2 == 0 or num % 3 == 0:
        return False
    (r, d) = (0, num - 1)
    while d % 2 == 0:
        r += 1
        d //= 2
    for a in [2, 3, 5, 7, 11, 13, 17, 19, 23]:
        if a >= num:
            continue
        x = _mod_pow(a, d, num)
        if x == 1 or x == num - 1:
            continue
        for _ in range(r - 1):
            x = _mod_pow(x, 2, num)
            if x == num - 1:
                break
        else:
            return False
    return True

def goldbach(num: int) -> Tuple[int, int]:
    """Find p, q prime such that p + q = n (n must be even and ≥ 4)."""
    if num < 4 or num % 2 != 0:
        raise ValueError(f'goldbach requires even n ≥ 4, got {num}')
    primes = set(sieve(num))
    for p in sorted(primes):
        q = num - p
        if q in primes:
            return (p, q)
    raise ValueError(f'No Goldbach pair found for {num}')

def test_prime_sieve():
    assert sieve(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    assert sieve(2) == [2]
    assert sieve(1) == []
    assert sieve(0) == []
    assert len(sieve(100)) == 25
    assert prime_factorize(12) == {2: 2, 3: 1}
    assert prime_factorize(360) == {2: 3, 3: 2, 5: 1}
    assert prime_factorize(1) == {}
    assert prime_factorize(13) == {13: 1}
    try:
        prime_factorize(0)
        assert False
    except ValueError:
        pass
    assert is_prime(2) and is_prime(3) and is_prime(5) and is_prime(97)
    assert not is_prime(1) and (not is_prime(4)) and (not is_prime(100))
    assert is_prime(104729)
    assert not is_prime(104728)
    for p in sieve(100):
        assert is_prime(p), f'{p} failed is_prime'
    (p, q) = goldbach(28)
    assert p + q == 28 and is_prime(p) and is_prime(q)
    (p2, q2) = goldbach(4)
    assert p2 == 2 and q2 == 2
    try:
        goldbach(7)
        assert False
    except ValueError:
        pass
    print('All prime_sieve tests passed.')
if __name__ == '__main__':
    test_prime_sieve()
    print('Primes ≤ 50:', sieve(50))
    print('Factorize 360:', prime_factorize(360))
    print('Goldbach(100):', goldbach(100))