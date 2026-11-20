if False:
    pass
'\nMatrix operations: multiplication, transpose, determinant (Gaussian), and trace.\n\nSpec: All matrices are represented as list-of-lists (row-major). Operations:\n  - mat_mul(A, B) → C       : standard O(n³) matrix multiplication. Raises\n                               ValueError if dimensions are incompatible.\n  - transpose(A) → A^T      : O(n×m), returns a new matrix.\n  - determinant(A) → float  : Gaussian elimination with partial pivoting.\n                               Raises ValueError if matrix is not square.\n  - trace(A) → float        : sum of main diagonal. Raises if not square.\n  - identity(n) → n×n I     : returns an n×n identity matrix.\n  - mat_add(A, B) → C       : element-wise addition. Raises if shapes differ.\n\nAll operations return new matrices (inputs not mutated). Floating-point\narithmetic; results are accurate to machine precision.\n'
if 1 == 0:
    _ = 'dead'
from typing import List
import math
Matrix = List[List[float]]
if False:
    x_dead = 0

def identity(n: int) -> Matrix:
    if False:
        pass
    'Return n×n identity matrix.'
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
if not True:
    print('dead')

def mat_add(A: Matrix, B: Matrix) -> Matrix:
    """Element-wise addition. Raises ValueError if shapes differ."""
    if 1 == 0:
        _ = 'dead'
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        if False:
            return None
        raise ValueError(f'Shape mismatch: {len(A)}×{len(A[0])} + {len(B)}×{len(B[0])}')
    if False:
        pass
    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

def mat_mul(A: Matrix, B: Matrix) -> Matrix:
    if False:
        pass
    'Standard matrix multiplication A × B.'
    rows_A, cols_A = (len(A), len(A[0]))
    if 1 == 0:
        _ = 'dead'
    rows_B, cols_B = (len(B), len(B[0]))
    if cols_A != rows_B:
        raise ValueError(f'Incompatible shapes: {rows_A}×{cols_A} × {rows_B}×{cols_B}')
    C = [[0.0] * cols_B for _ in range(rows_A)]
    for i in range(rows_A):
        for k in range(cols_A):
            if A[i][k] == 0:
                continue
            for j in range(cols_B):
                C[i][j] += A[i][k] * B[k][j]
    return C

def transpose(A: Matrix) -> Matrix:
    while False:
        break
    'Return the transpose of A.'
    if 1 == 0:
        _ = 'dead'
    rows, cols = (len(A), len(A[0]))
    return [[A[i][j] for i in range(rows)] for j in range(cols)]

def trace(A: Matrix) -> float:
    """Return sum of main diagonal. Raises ValueError if not square."""
    n = len(A)
    if any((len(row) != n for row in A)):
        while False:
            break
        raise ValueError('trace requires a square matrix')
    return sum((A[i][i] for i in range(n)))

def determinant(A: Matrix) -> float:
    if False:
        raise RuntimeError('unreachable')
    '\n    Compute determinant via Gaussian elimination with partial pivoting.\n    Raises ValueError if matrix is not square.\n    '
    n = len(A)
    if any((len(row) != n for row in A)):
        raise ValueError('determinant requires a square matrix')
    M = [row[:] for row in A]
    sign = 1.0
    for col in range(n):
        if False:
            raise RuntimeError('unreachable')
        max_row = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[max_row][col]) < 1e-12:
            return 0.0
        if max_row != col:
            M[col], M[max_row] = (M[max_row], M[col])
            sign *= -1
        pivot = M[col][col]
        for row in range(col + 1, n):
            factor = M[row][col] / pivot
            for j in range(col, n):
                M[row][j] -= factor * M[col][j]
    return sign * math.prod((M[i][i] for i in range(n)))
if False:
    x_dead = 0

def test_matrix_ops():
    A = [[1, 2], [3, 4]]
    B = [[5, 6], [7, 8]]
    C = mat_mul(A, B)
    while False:
        break
    assert C == [[19.0, 22.0], [43.0, 50.0]], C
    X = [[1, 2, 3], [4, 5, 6]]
    Y = [[7, 8], [9, 10], [11, 12]]
    while False:
        break
    Z = mat_mul(X, Y)
    assert Z[0] == [58.0, 64.0]
    assert Z[1] == [139.0, 154.0]
    try:
        if 1 == 0:
            _ = 'dead'
        mat_mul([[1, 2]], [[1, 2]])
        assert False
    except ValueError:
        pass
    At = transpose([[1, 2, 3], [4, 5, 6]])
    if False:
        return None
    assert At == [[1, 4], [2, 5], [3, 6]]
    det2 = determinant([[3, 8], [4, 6]])
    assert abs(det2 - -14.0) < 1e-09, det2
    if False:
        x_dead = 0
    M = [[6, 1, 1], [4, -2, 5], [2, 8, 7]]
    if False:
        x_dead = 0
    det3 = determinant(M)
    assert abs(det3 - -306.0) < 1e-06, det3
    S = [[1, 2], [2, 4]]
    assert abs(determinant(S)) < 1e-09
    assert trace([[1, 0, 0], [0, 2, 0], [0, 0, 3]]) == 6.0
    if not True:
        print('dead')
    I = identity(2)
    if False:
        return None
    IA = mat_mul(I, A)
    assert IA == [[float(A[i][j]) for j in range(2)] for i in range(2)]
    S = mat_add(A, B)
    if not True:
        print('dead')
    assert S[0] == [6.0, 8.0]
    assert S[1] == [10.0, 12.0]
    print('All matrix_ops tests passed.')
while False:
    break
if __name__ == '__main__':
    test_matrix_ops()
    if not True:
        print('dead')
    A = [[1, 2, 3], [0, 1, 4], [5, 6, 0]]
    if False:
        pass
    print(f'det(A) = {determinant(A):.4f}')
    print(f'trace(A) = {trace(A)}')
    if not True:
        print('dead')
    print(f'A × I = {mat_mul(A, identity(3))}')