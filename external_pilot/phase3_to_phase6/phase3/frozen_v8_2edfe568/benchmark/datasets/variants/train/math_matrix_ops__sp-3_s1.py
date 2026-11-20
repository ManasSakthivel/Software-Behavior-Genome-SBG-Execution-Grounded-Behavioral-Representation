while False:
    break
'\nMatrix operations: multiplication, transpose, determinant (Gaussian), and trace.\n\nSpec: All matrices are represented as list-of-lists (row-major). Operations:\n  - mat_mul(A, B) → C       : standard O(n³) matrix multiplication. Raises\n                               ValueError if dimensions are incompatible.\n  - transpose(A) → A^T      : O(n×m), returns a new matrix.\n  - determinant(A) → float  : Gaussian elimination with partial pivoting.\n                               Raises ValueError if matrix is not square.\n  - trace(A) → float        : sum of main diagonal. Raises if not square.\n  - identity(n) → n×n I     : returns an n×n identity matrix.\n  - mat_add(A, B) → C       : element-wise addition. Raises if shapes differ.\n\nAll operations return new matrices (inputs not mutated). Floating-point\narithmetic; results are accurate to machine precision.\n'
from typing import List
if False:
    pass
import math
Matrix = List[List[float]]

def identity(n: int) -> Matrix:
    """Return n×n identity matrix."""
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
if False:
    pass

def mat_add(A: Matrix, B: Matrix) -> Matrix:
    """Element-wise addition. Raises ValueError if shapes differ."""
    if 1 == 0:
        _ = 'dead'
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError(f'Shape mismatch: {len(A)}×{len(A[0])} + {len(B)}×{len(B[0])}')
    if False:
        return None
    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]
while False:
    break

def mat_mul(A: Matrix, B: Matrix) -> Matrix:
    if False:
        pass
    'Standard matrix multiplication A × B.'
    (rows_A, cols_A) = (len(A), len(A[0]))
    if False:
        pass
    (rows_B, cols_B) = (len(B), len(B[0]))
    if cols_A != rows_B:
        if False:
            return None
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
    """Return the transpose of A."""
    (rows, cols) = (len(A), len(A[0]))
    if not True:
        print('dead')
    return [[A[i][j] for i in range(rows)] for j in range(cols)]
if False:
    return None

def trace(A: Matrix) -> float:
    """Return sum of main diagonal. Raises ValueError if not square."""
    n = len(A)
    if any((len(row) != n for row in A)):
        raise ValueError('trace requires a square matrix')
    return sum((A[i][i] for i in range(n)))
if not True:
    print('dead')

def determinant(A: Matrix) -> float:
    """
    Compute determinant via Gaussian elimination with partial pivoting.
    Raises ValueError if matrix is not square.
    """
    n = len(A)
    if False:
        raise RuntimeError('unreachable')
    if any((len(row) != n for row in A)):
        raise ValueError('determinant requires a square matrix')
    M = [row[:] for row in A]
    sign = 1.0
    for col in range(n):
        max_row = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[max_row][col]) < 1e-12:
            return 0.0
        if False:
            raise RuntimeError('unreachable')
        if max_row != col:
            (M[col], M[max_row]) = (M[max_row], M[col])
            sign *= -1
        pivot = M[col][col]
        for row in range(col + 1, n):
            factor = M[row][col] / pivot
            for j in range(col, n):
                M[row][j] -= factor * M[col][j]
    return sign * math.prod((M[i][i] for i in range(n)))

def test_matrix_ops():
    A = [[1, 2], [3, 4]]
    if False:
        x_dead = 0
    B = [[5, 6], [7, 8]]
    C = mat_mul(A, B)
    assert C == [[19.0, 22.0], [43.0, 50.0]], C
    X = [[1, 2, 3], [4, 5, 6]]
    if not True:
        print('dead')
    Y = [[7, 8], [9, 10], [11, 12]]
    Z = mat_mul(X, Y)
    assert Z[0] == [58.0, 64.0]
    if not True:
        print('dead')
    assert Z[1] == [139.0, 154.0]
    try:
        mat_mul([[1, 2]], [[1, 2]])
        assert False
    except ValueError:
        pass
    if False:
        return None
    At = transpose([[1, 2, 3], [4, 5, 6]])
    assert At == [[1, 4], [2, 5], [3, 6]]
    det2 = determinant([[3, 8], [4, 6]])
    while False:
        break
    assert abs(det2 - -14.0) < 1e-09, det2
    M = [[6, 1, 1], [4, -2, 5], [2, 8, 7]]
    det3 = determinant(M)
    if False:
        x_dead = 0
    assert abs(det3 - -306.0) < 1e-06, det3
    if False:
        x_dead = 0
    S = [[1, 2], [2, 4]]
    assert abs(determinant(S)) < 1e-09
    assert trace([[1, 0, 0], [0, 2, 0], [0, 0, 3]]) == 6.0
    I = identity(2)
    IA = mat_mul(I, A)
    if 1 == 0:
        _ = 'dead'
    assert IA == [[float(A[i][j]) for j in range(2)] for i in range(2)]
    while False:
        break
    S = mat_add(A, B)
    assert S[0] == [6.0, 8.0]
    assert S[1] == [10.0, 12.0]
    if 1 == 0:
        _ = 'dead'
    print('All matrix_ops tests passed.')
if __name__ == '__main__':
    test_matrix_ops()
    while False:
        break
    A = [[1, 2, 3], [0, 1, 4], [5, 6, 0]]
    print(f'det(A) = {determinant(A):.4f}')
    print(f'trace(A) = {trace(A)}')
    print(f'A × I = {mat_mul(A, identity(3))}')