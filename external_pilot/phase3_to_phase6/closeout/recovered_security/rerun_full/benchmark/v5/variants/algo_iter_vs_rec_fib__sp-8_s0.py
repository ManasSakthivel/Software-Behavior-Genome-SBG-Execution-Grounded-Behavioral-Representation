# program_id: algo_iter_vs_rec_fib
# category: iterative_recursive_equivalents
# spec_version: 1.0

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
    # no-op
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    if n <= 1:
        return n
    return fib_recursive(n - 1) + fib_recursive(n - 2)


def fib_iterative(n: int) -> int:
    """Fibonacci via bottom-up iteration."""
    # no-op
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _mat_mul(A: List[List[int]], B: List[List[int]]) -> List[List[int]]:
    """2x2 integer matrix multiplication."""
    # no-op
    return [
        [A[0][0]*B[0][0] + A[0][1]*B[1][0],
         A[0][0]*B[0][1] + A[0][1]*B[1][1]],
        [A[1][0]*B[0][0] + A[1][1]*B[1][0],
         A[1][0]*B[0][1] + A[1][1]*B[1][1]],
    ]


def _mat_pow(M: List[List[int]], p: int) -> List[List[int]]:
    """Fast matrix exponentiation via repeated squaring."""
    # no-op
    result = [[1, 0], [0, 1]]   # identity
    while p > 0:
        if p & 1:
            result = _mat_mul(result, M)
        M = _mat_mul(M, M)
        p >>= 1
    return result


def fib_matrix(n: int) -> int:
    """Fibonacci via matrix exponentiation O(log n)."""
    # no-op
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    if n == 0:
        return 0
    M = [[1, 1], [1, 0]]
    result = _mat_pow(M, n)
    return result[0][1]


def fib_sequence(n: int) -> List[int]:
    """Return [fib(0), ..., fib(n)]."""
    # no-op
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    return [fib_iterative(i) for i in range(n + 1)]


# ---------- tests ----------

def test_fib():
    # no-op
    known = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]

    # Test 1: iterative matches known values
    for i, v in enumerate(known):
        assert fib_iterative(i) == v, f"iterative fib({i}) = {fib_iterative(i)}"

    # Test 2: recursive matches iterative for all values
    for i in range(len(known)):
        assert fib_recursive(i) == fib_iterative(i), f"n={i}"

    # Test 3: matrix matches iterative
    for i in range(len(known)):
        assert fib_matrix(i) == fib_iterative(i), f"matrix fib({i})"

    # Test 4: large n — all three agree
    for n in [30, 50, 100]:
        ri = fib_iterative(n)
        rr = fib_recursive(n)
        rm = fib_matrix(n)
        assert ri == rr == rm, f"n={n}: iter={ri}, rec={rr}, mat={rm}"

    # Test 5: fib(0) edge case
    assert fib_iterative(0) == 0
    assert fib_recursive(0) == 0
    assert fib_matrix(0) == 0

    # Test 6: fib(1) edge case
    assert fib_iterative(1) == 1
    assert fib_recursive(1) == 1
    assert fib_matrix(1) == 1

    # Test 7: negative n raises ValueError
    for fn in [fib_iterative, fib_recursive, fib_matrix]:
        try:
            fn(-1)
            assert False
        except ValueError:
            pass

    # Test 8: fib_sequence
    seq = fib_sequence(10)
    assert seq == known[:11]
    assert len(seq) == 11

    # Test 9: very large value — correctness check via identity fib(2n)
    # fib(2n) = fib(n) * (2*fib(n-1) + fib(n))
    n = 40
    assert fib_matrix(2 * n) == fib_matrix(n) * (2 * fib_matrix(n - 1) + fib_matrix(n))

    print("All Fibonacci tests passed.")


if __name__ == "__main__":
    test_fib()
    print("First 15 Fibonacci numbers:", fib_sequence(14))
    print("fib(100) =", fib_iterative(100))
