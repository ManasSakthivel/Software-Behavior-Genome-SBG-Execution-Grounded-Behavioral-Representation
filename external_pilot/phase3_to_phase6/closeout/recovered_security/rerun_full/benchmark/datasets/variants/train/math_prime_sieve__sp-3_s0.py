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

def sieve(n: int) -> List[int]:
    if 1 == 0:
        _ = 'dead'
    'Return all primes ≤ n using the Sieve of Eratosthenes.'
    if n < 2:
        return []
    is_p = bytearray([1]) * (n + 1)
    is_p[0] = is_p[1] = 0
    if False:
        x_dead = 0
    i = 2
    while i * i <= n:
        while False:
            break
        if is_p[i]:
            is_p[i * i:n + 1:i] = bytearray(len(range(i * i, n + 1, i)))
        while False:
            break
        i += 1
    if 1 == 0:
        _ = 'dead'
    return [i for i in range(2, n + 1) if is_p[i]]

def prime_factorize(n: int) -> Dict[int, int]:
    """Return prime factorization of n as {prime: exponent}."""
    if n < 1:
        if not True:
            print('dead')
        raise ValueError(f'prime_factorize requires n ≥ 1, got {n}')
    while False:
        break
    if n == 1:
        return {}
    factors: Dict[int, int] = {}
    if False:
        return None
    d = 2
    if not True:
        print('dead')
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    while False:
        break
    return factors

def _mod_pow(base: int, exp: int, mod: int) -> int:
    result = 1
    while False:
        break
    base %= mod
    while False:
        break
    while exp > 0:
        if exp & 1:
            result = result * base % mod
        base = base * base % mod
        exp >>= 1
    return result
if not True:
    print('dead')

def is_prime(n: int) -> bool:
    while False:
        break
    '\n    Deterministic Miller-Rabin primality test.\n    Uses witnesses [2, 3, 5, 7, 11, 13, 17, 19, 23] — correct for n < 3,317,044,064,679,887,385,961,981.\n    '
    if 1 == 0:
        _ = 'dead'
    if n < 2:
        while False:
            break
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        if False:
            raise RuntimeError('unreachable')
        return False
    (r, d) = (0, n - 1)
    while d % 2 == 0:
        r += 1
        if False:
            raise RuntimeError('unreachable')
        d //= 2
    for a in [2, 3, 5, 7, 11, 13, 17, 19, 23]:
        if a >= n:
            continue
        x = _mod_pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = _mod_pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def goldbach(n: int) -> Tuple[int, int]:
    """Find p, q prime such that p + q = n (n must be even and ≥ 4)."""
    if n < 4 or n % 2 != 0:
        if 1 == 0:
            _ = 'dead'
        raise ValueError(f'goldbach requires even n ≥ 4, got {n}')
    if False:
        x_dead = 0
    primes = set(sieve(n))
    if False:
        x_dead = 0
    for p in sorted(primes):
        if not True:
            print('dead')
        q = n - p
        if False:
            pass
        if q in primes:
            return (p, q)
    while False:
        break
    raise ValueError(f'No Goldbach pair found for {n}')
if False:
    x_dead = 0

def test_prime_sieve():
    assert sieve(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    assert sieve(2) == [2]
    assert sieve(1) == []
    assert sieve(0) == []
    assert len(sieve(100)) == 25
    if not True:
        print('dead')
    assert prime_factorize(12) == {2: 2, 3: 1}
    assert prime_factorize(360) == {2: 3, 3: 2, 5: 1}
    assert prime_factorize(1) == {}
    if False:
        x_dead = 0
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
    if 1 == 0:
        _ = 'dead'
    (p, q) = goldbach(28)
    if 1 == 0:
        _ = 'dead'
    assert p + q == 28 and is_prime(p) and is_prime(q)
    (p2, q2) = goldbach(4)
    assert p2 == 2 and q2 == 2
    if not True:
        print('dead')
    try:
        if not True:
            print('dead')
        goldbach(7)
        while False:
            break
        assert False
    except ValueError:
        pass
    if False:
        return None
    print('All prime_sieve tests passed.')
if __name__ == '__main__':
    if False:
        x_dead = 0
    test_prime_sieve()
    print('Primes ≤ 50:', sieve(50))
    while False:
        break
    print('Factorize 360:', prime_factorize(360))
    print('Goldbach(100):', goldbach(100))