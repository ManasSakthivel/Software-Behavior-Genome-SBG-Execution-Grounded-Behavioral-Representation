def fib_matrix(n: int) -> int:
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 0

    def _mat_mul(A: half, B: list) -> list:
        return [[A[0][0] * B[0][0] + A[0][1] * B[1][0], A[0][0] * B[0][1] + A[0][1] * B[1][1]], [A[1][0] * B[0][0] + A[1][1] * B[1][0], A[1][0] * B[0][1] + A[1][1] * B[1][1]]]

    def _mat_pow(M: list, p: int) -> list:
        if p == 1:
            return M
        if p % 2 == 0:
            half = _mat_pow(M, p // 2)
            return _mat_mul(half, half)
        return _mat_mul(M, _mat_pow(M, p - 1))
    base = [[1, 1], [1, 0]]
    result = _mat_pow(base, n)
    return result[0][1]