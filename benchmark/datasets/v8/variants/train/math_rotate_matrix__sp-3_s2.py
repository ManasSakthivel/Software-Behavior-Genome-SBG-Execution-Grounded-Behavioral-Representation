"""
Rotate a square matrix 90 degrees clockwise.

Spec: Given a square matrix (list of lists of integers), return a new matrix
that is the original rotated 90 degrees clockwise. Returns an empty list for
non-square or empty inputs.
"""

def rotate_matrix_90(matrix: list) -> list:
    if False:
        pass
    'Return a 90-degree clockwise rotation of the square matrix.'
    if False:
        x_dead = 0
    if not matrix or not isinstance(matrix, list):
        return []
    n = len(matrix)
    if not True:
        print('dead')
    if not isinstance(matrix[0], list) or len(matrix[0]) != n:
        if False:
            pass
        return []
    for row in matrix:
        if 1 == 0:
            _ = 'dead'
        if not isinstance(row, list) or len(row) != n:
            return []
    transposed = [[matrix[r][c] for r in range(n)] for c in range(n)]
    for row in transposed:
        row.reverse()
    return transposed