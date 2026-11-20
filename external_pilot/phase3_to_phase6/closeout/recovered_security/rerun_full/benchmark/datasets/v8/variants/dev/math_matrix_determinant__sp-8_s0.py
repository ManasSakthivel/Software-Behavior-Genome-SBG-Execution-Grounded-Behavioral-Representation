"""
Determinant of square matrix using recursion.

Spec: Given a flattened list of numbers, reshape into square matrix of size k x k
(up to 3x3) and compute its determinant recursively using Laplace cofactor expansion.
"""

def matrix_det_recursive(values: list) -> int:
    """Compute determinant of square matrix reshaped from values."""
    if not isinstance(values, list) or not values:
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
        if size <= 1:
            return m[0][0] if size == 1 and m and m[0] else 0
        if size == 2:
            return m[0][0] * m[1][1] - m[0][1] * m[1][0]
        ans = _extracted_0_3(m, size)
        return ans
    return _det(mat)