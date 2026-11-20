"""
Number theory toolkit: GCD, LCM, modular exponentiation, modular inverse,
extended Euclidean algorithm, and primality test (Miller-Rabin).

Spec:
  - gcd(a, b) -> int: Greatest common divisor via Euclidean algorithm.
    Handles 0: gcd(a,0)=a, gcd(0,0)=0. Result always >= 0.
  - lcm(a, b) -> int: Least common multiple. Returns 0 if either is 0.
  - extended_gcd(a, b) -> (g, x, y): g=gcd(a,b), ax+by=g.
  - mod_inverse(a, m) -> int: modular inverse of a mod m (a^-1 mod m).
    Raises ValueError if gcd(a,m) != 1.
  - mod_pow(base, exp, mod) -> int: fast modular exponentiation.
    exp must be >= 0; mod must be >= 1.
  - is_prime_miller_rabin(n, k=10) -> bool: deterministic Miller-Rabin for
    n < 3,317,044,064,679,887,385,961,981 using fixed witness sets.

Suggested mutations:
  - SC-2: use a % b - 1 instead of a % b in Euclidean step
  - SC-6: return x instead of x % m in mod_inverse
  - SC-9: omit the modular squaring step in mod_pow (returns wrong result)
  - SC-11: initialise x, y to (1, 0) instead of (0, 1) in extended_gcd base case

Suggested SP transformations:
  - SP-4: convert iterative gcd to recursive (equivalent)
  - SP-5: replace pow(base, exp, mod) with custom mod_pow in caller code
  - SP-3: reorder g, x, y extraction from extended_gcd (independent)
  - SP-7: extract _miller_witness check as a helper
  - SP-9: replace Miller-Rabin with trial division for small n (same output
          for n < 1000)
"""
from typing import Tuple

def fn_gcd(a: int, b: int) -> int:
    """Euclidean GCD. Returns non-negative result."""
    (a, b) = (abs(a), abs(b))
    while b:
        (a, b) = (b, a % b)
    return a

def fn_lcm(a: int, b: int) -> int:
    """LCM. Returns 0 if either argument is 0."""
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // fn_gcd(a, b)

def fn_extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    """
    Extended Euclidean algorithm.
    Returns (g, x, y) such that a*x + b*y = g = gcd(a, b).
    """
    if b == 0:
        return (a, 1, 0)
    (g, x1, y1) = fn_extended_gcd(b, a % b)
    return (g, y1, x1 - a // b * y1)

def fn_mod_inverse(a: int, m: int) -> int:
    """
    Modular inverse of a modulo m.
    Raises ValueError if gcd(a, m) != 1.
    """
    if m <= 0:
        raise ValueError(f'Modulus must be positive, got {m}')
    (g, x, _) = fn_extended_gcd(a % m, m)
    if g != 1:
        raise ValueError(f'{a} has no inverse modulo {m} (gcd={g})')
    return x % m

def fn_mod_pow(base: int, exp: int, mod: int) -> int:
    """Fast modular exponentiation: base^exp mod mod."""
    if mod < 1:
        raise ValueError(f'mod must be >= 1, got {mod}')
    if exp < 0:
        raise ValueError(f'exp must be >= 0, got {exp}')
    result = 1
    base = base % mod
    while exp > 0:
        if exp & 1:
            result = result * base % mod
        base = base * base % mod
        exp >>= 1
    return result % mod

def _miller_rabin_check(n: int, a: int) -> bool:
    """Single Miller-Rabin witness test: True means 'probably prime'."""
    if n % a == 0:
        return n == a
    (d, r) = (n - 1, 0)
    while d % 2 == 0:
        d //= 2
        r += 1
    x = fn_mod_pow(a, d, n)
    if x == 1 or x == n - 1:
        return True
    for _ in range(r - 1):
        x = x * x % n
        if x == n - 1:
            return True
    return False

def fn_is_prime_miller_rabin(n: int, k: int=10) -> bool:
    """
    Deterministic Miller-Rabin primality test for n >= 2.
    Uses carefully chosen witness sets that are deterministic for
    n < 3,317,044,064,679,887,385,961,981.
    k parameter is retained for API compatibility but witnesses are fixed.
    Returns False for n < 2.
    """
    if n < 2:
        return False
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    if n in small_primes:
        return True
    if any((n % p == 0 for p in small_primes)):
        return False
    witnesses = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    return all((_miller_rabin_check(n, a) for a in witnesses if a < n))

def test_number_theory():
    assert fn_gcd(48, 18) == 6
    assert fn_gcd(0, 5) == 5
    assert fn_gcd(5, 0) == 5
    assert fn_gcd(0, 0) == 0
    assert fn_gcd(100, 75) == 25
    assert fn_gcd(-12, 8) == 4
    assert fn_lcm(4, 6) == 12
    assert fn_lcm(0, 5) == 0
    assert fn_lcm(7, 13) == 91
    (g, x, y) = fn_extended_gcd(35, 15)
    assert g == 5
    assert 35 * x + 15 * y == g
    (g2, x2, y2) = fn_extended_gcd(3, 11)
    assert g2 == 1
    assert 3 * x2 + 11 * y2 == 1
    assert fn_mod_inverse(3, 11) == 4
    assert fn_mod_inverse(2, 7) == 4
    try:
        fn_mod_inverse(2, 4)
        assert False
    except ValueError:
        pass
    assert fn_mod_pow(2, 10, 1000) == 24
    assert fn_mod_pow(3, 0, 7) == 1
    assert fn_mod_pow(0, 0, 1) == pow(0, 0, 1)
    assert fn_mod_pow(2, 30, 10 ** 9 + 7) == pow(2, 30, 10 ** 9 + 7)
    primes = [2, 3, 5, 7, 11, 13, 17, 97, 101, 997, 7919, 104729]
    composites = [1, 4, 6, 9, 15, 100, 561, 1729]
    for p in primes:
        assert fn_is_prime_miller_rabin(p), f'{p} should be prime'
    for c in composites:
        assert not fn_is_prime_miller_rabin(c), f'{c} should be composite'
    assert fn_is_prime_miller_rabin(982451653)
    print('All number-theory tests passed.')
if __name__ == '__main__':
    test_number_theory()
    print('gcd(48,18)=', fn_gcd(48, 18))
    print('mod_inverse(3,11)=', fn_mod_inverse(3, 11))
    print('mod_pow(2,10,1000)=', fn_mod_pow(2, 10, 1000))
    print('is_prime(982451653)=', fn_is_prime_miller_rabin(982451653))