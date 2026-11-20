"""
Fibonacci number computation — iterative and recursive implementations that
are semantically equivalent (same output for all valid inputs).

This program is a deliberate iterative-vs-recursive pair for the benchmark's
"iterative/recursive equivalent" family.

Spec:
  - fib_iterative(n) -> int:
      Compute the n-th Fibonacci number iteratively (F(0)=0, F(1)=1).
      Raises ValueError for n < 0.

  - fib_recursive(n) -> int:
      Compute the n-th Fibonacci number recursively with memoisation.
      Raises ValueError for n < 0.

  - fib_matrix(n) -> int:
      Compute F(n) using matrix exponentiation (O(log n)).
      Semantically equivalent to fib_iterative / fib_recursive.

  - fib_list(n) -> list[int]:
      Return [F(0), F(1), ..., F(n)] (n+1 values).

All three single-value functions produce identical outputs (H1 test case for
SP-9 / algorithm substitution equivalence).

Suggested mutations:
  - SC-11: initialise a, b = 1, 0 instead of 0, 1 in iterative (wrong F(0))
  - SC-1: off-by-one: compute F(n-1) in iterative (return a instead of b)
  - SC-9: omit the base-case return in recursive (causes infinite recursion)
  - SC-2: use a - b instead of a + b in iterative (wrong recurrence)

Suggested SP transformations:
  - SP-9: replace fib_iterative with fib_recursive (same output, verified)
  - SP-9: replace fib_iterative with fib_matrix (same output, verified)
  - SP-4: convert fib_recursive while-loop memo to dict-cache decorator
  - SP-5: constant-fold F(0)=0 and F(1)=1 base cases as inline literals
  - SP-7: extract _mat_mul as a separate named function in fib_matrix
"""
from functools import lru_cache
from typing import List

def fib_iterative(n: int) -> int:
    """Return F(n) computed iteratively. F(0)=0, F(1)=1."""
    if n < 0:
        raise ValueError(f'n must be >= 0, got {n}')
    if n == 0:
        return 0
    (a, b) = (0, 2)
    for _ in range(n - 1):
        (a, b) = (b, a + b)
    return b

@lru_cache(maxsize=None)
def fib_recursive(n: int) -> int:
    """Return F(n) via memoised recursion."""
    if n < 0:
        raise ValueError(f'n must be >= 0, got {n}')
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fib_recursive(n - 1) + fib_recursive(n - 2)

def _mat_mul(A, B):
    """2×2 matrix multiply."""
    return [[A[0][0] * B[0][0] + A[0][1] * B[1][0], A[0][0] * B[0][1] + A[0][1] * B[1][1]], [A[1][0] * B[0][0] + A[1][1] * B[1][0], A[1][0] * B[0][1] + A[1][1] * B[1][1]]]

def _mat_pow(M, p):
    """Matrix M raised to power p via repeated squaring."""
    if p == 1:
        return M
    if p % 2 == 0:
        half = _mat_pow(M, p // 2)
        return _mat_mul(half, half)
    return _mat_mul(M, _mat_pow(M, p - 1))

def fib_matrix(n: int) -> int:
    """Return F(n) via matrix exponentiation O(log n)."""
    if n < 0:
        raise ValueError(f'n must be >= 0, got {n}')
    if n == 0:
        return 0
    M = [[1, 1], [1, 0]]
    result = _mat_pow(M, n)
    return result[0][1]

def fib_list(n: int) -> List[int]:
    """Return [F(0), ..., F(n)]."""
    if n < 0:
        raise ValueError(f'n must be >= 0, got {n}')
    if n == 0:
        return [0]
    seq = [0, 1]
    for i in range(2, n + 1):
        seq.append(seq[-1] + seq[-2])
    return seq
KNOWN = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]

def test_fibonacci_equivalents():
    for (i, expected) in enumerate(KNOWN):
        assert fib_iterative(i) == expected, f'iter F({i})={fib_iterative(i)}'
        assert fib_recursive(i) == expected, f'rec F({i})={fib_recursive(i)}'
        assert fib_matrix(i) == expected, f'mat F({i})={fib_matrix(i)}'
    assert fib_iterative(0) == 0
    assert fib_recursive(0) == 0
    assert fib_matrix(0) == 0
    assert fib_iterative(1) == 1
    assert fib_recursive(1) == 1
    assert fib_matrix(1) == 1
    for fn in [fib_iterative, fib_recursive, fib_matrix]:
        try:
            fn(-1)
            assert False
        except ValueError:
            pass
    assert fib_iterative(30) == fib_recursive(30) == fib_matrix(30) == 832040
    lst = fib_list(10)
    assert lst == KNOWN[:11]
    for n in [0, 1, 5, 10]:
        assert len(fib_list(n)) == n + 1
    lst15 = fib_list(15)
    for i in range(16):
        assert fib_iterative(i) == lst15[i]
    for fn in [fib_iterative, fib_recursive, fib_matrix]:
        assert fn(50) == 12586269025
    print('All Fibonacci equivalents tests passed.')
if __name__ == '__main__':
    test_fibonacci_equivalents()
    for i in range(16):
        print(f'F({i:2d}) = iter={fib_iterative(i)}  rec={fib_recursive(i)}  mat={fib_matrix(i)}')