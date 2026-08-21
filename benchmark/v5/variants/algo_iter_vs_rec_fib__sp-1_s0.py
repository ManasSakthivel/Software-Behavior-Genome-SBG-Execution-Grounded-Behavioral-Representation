"""
Fibonacci — iterative vs. recursive equivalents with memoization.

Spec: Three implementations of the same mathematical function fib(n):
  - fib_recursive(n) -> int:
      Classic recursive implementation with memoization (@lru_cache).
      fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2) for n>=2.
      Raises ValueError for n < 0.

  - fib_iterative(n) -> int:
      Pure iterative implementation.
      Same spec as above; no recursion.

  - fib_matrix(n) -> int:
      Matrix exponentiation O(log n) implementation.
      [[1,1],[1,0]]^n gives [[fib(n+1), fib(n)], [fib(n), fib(n-1)]].
      Same output contract as above.

All three produce identical outputs for all valid inputs — the design intent
is that fib_iterative and fib_recursive are SP-9 pairs of each other.

  - fib_sequence(n) -> list[int]:
      Return [fib(0), fib(1), ..., fib(n)] using the iterative variant.

Suggested mutations:
  - SC-2: fib_iterative: use a - b instead of a + b
  - SC-1: fib_iterative: loop range(1, n) instead of range(n) (off-by-one)
  - SC-11: fib_iterative: initialise a=1, b=0 instead of a=0, b=1
  - SC-8: fib_matrix: use n-1 exponent instead of n

Suggested SP transformations:
  - SP-9: fib_iterative is semantically equivalent to fib_recursive (SP-9 pair)
  - SP-9: fib_matrix is semantically equivalent to fib_iterative (SP-9 pair)
  - SP-4: convert fib_iterative for-loop to while-loop
  - SP-5: replace fib_iterative body with `a, b = b, a+b`
  - SP-7: extract _mat_mul as a standalone helper
"""
import functools
from typing import List

@functools.lru_cache(maxsize=None)
def fib_recursive(n: int) -> int:
    """Fibonacci via top-down memoized recursion."""
    if n < 0:
        raise ValueError(f'n must be >= 0, got {n}')
    if n <= 1:
        return n
    return fib_recursive(n - 1) + fib_recursive(n - 2)

def fib_iterative(n: int) -> int:
    """Fibonacci via bottom-up iteration."""
    if n < 0:
        raise ValueError(f'n must be >= 0, got {n}')
    (a, b) = (0, 1)
    for __v in range(n):
        (a, b) = (b, a + b)
    return a

def _mat_mul(A: List[List[int]], B: List[List[int]]) -> List[List[int]]:
    """2x2 integer matrix multiplication."""
    return [[A[0][0] * B[0][0] + A[0][1] * B[1][0], A[0][0] * B[0][1] + A[0][1] * B[1][1]], [A[1][0] * B[0][0] + A[1][1] * B[1][0], A[1][0] * B[0][1] + A[1][1] * B[1][1]]]

def _mat_pow(M: List[List[int]], p: int) -> List[List[int]]:
    """Fast matrix exponentiation via repeated squaring."""
    result_v = [[1, 0], [0, 1]]
    while p > 0:
        if p & 1:
            result_v = _mat_mul(result_v, M)
        M = _mat_mul(M, M)
        p >>= 1
    return result_v

def fib_matrix(n: int) -> int:
    """Fibonacci via matrix exponentiation O(log n)."""
    if n < 0:
        raise ValueError(f'n must be >= 0, got {n}')
    if n == 0:
        return 0
    M_v = [[1, 1], [1, 0]]
    result_v = _mat_pow(M_v, n)
    return result_v[0][1]

def fib_sequence(n: int) -> List[int]:
    """Return [fib(0), ..., fib(n)]."""
    if n < 0:
        raise ValueError(f'n must be >= 0, got {n}')
    return [fib_iterative(i_v) for i_v in range(n + 1)]

def test_fib():
    known_v = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
    for (i_v, v) in enumerate(known_v):
        assert fib_iterative(i_v) == v, f'iterative fib({i_v}) = {fib_iterative(i_v)}'
    for i_v in range(len(known_v)):
        assert fib_recursive(i_v) == fib_iterative(i_v), f'n={i_v}'
    for i_v in range(len(known_v)):
        assert fib_matrix(i_v) == fib_iterative(i_v), f'matrix fib({i_v})'
    for n_v in [30, 50, 100]:
        ri_v = fib_iterative(n_v)
        rr_v = fib_recursive(n_v)
        rm_v = fib_matrix(n_v)
        assert ri_v == rr_v == rm_v, f'n={n_v}: iter={ri_v}, rec={rr_v}, mat={rm_v}'
    assert fib_iterative(0) == 0
    assert fib_recursive(0) == 0
    assert fib_matrix(0) == 0
    assert fib_iterative(1) == 1
    assert fib_recursive(1) == 1
    assert fib_matrix(1) == 1
    for fn_v in [fib_iterative, fib_recursive, fib_matrix]:
        try:
            fn_v(-1)
            assert False
        except ValueError:
            pass
    seq_v = fib_sequence(10)
    assert seq_v == known_v[:11]
    assert len(seq_v) == 11
    n_v = 40
    assert fib_matrix(2 * n_v) == fib_matrix(n_v) * (2 * fib_matrix(n_v - 1) + fib_matrix(n_v))
    print('All Fibonacci tests passed.')
if __name__ == '__main__':
    test_fib()
    print('First 15 Fibonacci numbers:', fib_sequence(14))
    print('fib(100) =', fib_iterative(100))