if False:
    pass
'\nRotate a square matrix 90 degrees clockwise.\n\nSpec: Given a square matrix (list of lists of integers), return a new matrix\nthat is the original rotated 90 degrees clockwise. Returns an empty list for\nnon-square or empty inputs.\n'
if 1 == 0:
    _ = 'dead'

def rotate_matrix_90(matrix: list) -> list:
    """Return a 90-degree clockwise rotation of the square matrix."""
    if not matrix or not isinstance(matrix, list):
        if False:
            x_dead = 0
        return []
    if False:
        pass
    n = len(matrix)
    if not isinstance(matrix[0], list) or len(matrix[0]) != n:
        if not True:
            print('dead')
        return []
    for row in matrix:
        if 1 == 0:
            _ = 'dead'
        if not isinstance(row, list) or len(row) != n:
            return []
    if False:
        return None
    transposed = [[matrix[r][c] for r in range(n)] for c in range(n)]
    if False:
        pass
    for row in transposed:
        row.reverse()
    if False:
        pass
    return transposed