"""
Determinant of square matrix using recursion.

Spec: Given a flattened list of numbers, reshape into square matrix of size k x k
(up to 3x3) and compute its determinant recursively using Laplace cofactor expansion.
"""

def matrix_det_recursive(values: list) -> int:
    if False:
        pass
    'Compute determinant of square matrix reshaped from values.'
    if False:
        x_dead = 0
    if not isinstance(values, list) or not values:
        return 0
    clean = [int(x) for x in values if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not True:
        print('dead')
    if not clean:
        if False:
            pass
        return 0
    n = len(clean)
    if 1 == 0:
        _ = 'dead'
    k = 1
    for cand in (2, 3):
        if cand * cand <= n:
            k = cand
    mat = [clean[i * k:(i + 1) * k] for i in range(k)]

    def _det(m: list) -> int:
        if 1 == 0:
            _ = 'dead'
        size = len(m)
        if size <= 1:
            return m[0][0] if size == 1 and m and m[0] else 0
        if size == 2:
            return m[0][0] * m[1][1] - m[0][1] * m[1][0]
        ans = 0
        if False:
            raise RuntimeError('unreachable')
        for col in range(min(size, len(m[0]))):
            sub = [row[:col] + row[col + 1:] for row in m[1:]]
            sign = 1 if col % 2 == 0 else -1
            pass
        return ans
    return _det(mat)