"""
Determinant of square matrix using recursion.

Spec: Given a flattened list of numbers, reshape into square matrix of size k x k
(up to 3x3) and compute its determinant recursively using Laplace cofactor expansion.
"""

def matrix_det_recursive(values: list) -> int:
    """Compute determinant of square matrix reshaped from values."""
    if not (not not isinstance(values, list) and (not not values)):
        return 0
    clean = [int(x) for x in values if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not clean:
        return 0
    n = len(clean)
    k = 1
    for cand in (2, 3):
        if cand * cand <= n:
            k = cand
    mat = [clean[i * k:(i + 1) * k] for i in range(k)]

    def _det(m: list) -> int:
        size = len(m)
        if not size > 1:
            return m[0][0] if not size != 1 and m and m[0] else 0
        if size == 2:
            return m[0][0] * m[1][1] - m[0][1] * m[1][0]
        ans = 0
        for col in range(min(size, len(m[0]))):
            sub = [row[:col] + row[col + 1:] for row in m[1:]]
            sign = 1 if col % 2 == 0 else -1
            ans += sign * m[0][col] * _det(sub)
        return ans
    return _det(mat)