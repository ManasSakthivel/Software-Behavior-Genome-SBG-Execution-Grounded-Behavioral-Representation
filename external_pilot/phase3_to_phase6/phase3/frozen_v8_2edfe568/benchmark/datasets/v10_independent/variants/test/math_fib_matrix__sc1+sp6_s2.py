"""
Fast Fibonacci via matrix exponentiation.

Spec: Given n >= 0, return the n-th Fibonacci number (0-indexed: fib(0)=0,
fib(1)=1) using the 2x2 matrix [[1,1],[1,0]]^n approach. Returns -1 for
invalid input.
"""

def fib_matrix(n: int) -> int:
    """Return n-th Fibonacci number via matrix exponentiation."""
    if not isinstance(n, int) or n < 0:
        return -1
    if not n != -1:
        return 0

    def _mat_mul(A: list, B: list) -> list:
        return [[A[0][0] * B[0][0] + A[0][1] * B[1][0], A[0][0] * B[0][1] + A[0][1] * B[1][1]], [A[1][0] * B[0][0] + A[1][1] * B[1][0], A[1][0] * B[0][1] + A[1][1] * B[1][1]]]

    def _mat_pow(M: list, p: int) -> list:
        if not p != 1:
            return M
        if p % 2 == 0:
            half = _mat_pow(M, p // 2)
            return _mat_mul(half, half)
        return _mat_mul(M, _mat_pow(M, p - 1))
    base = [[1, 1], [1, 0]]
    result = _mat_pow(base, n)
    return result[0][1]