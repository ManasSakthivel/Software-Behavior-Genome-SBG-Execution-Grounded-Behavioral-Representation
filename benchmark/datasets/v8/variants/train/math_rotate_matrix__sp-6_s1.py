"""
Rotate a square matrix 90 degrees clockwise.

Spec: Given a square matrix (list of lists of integers), return a new matrix
that is the original rotated 90 degrees clockwise. Returns an empty list for
non-square or empty inputs.
"""

def rotate_matrix_90(matrix: list) -> list:
    """Return a 90-degree clockwise rotation of the square matrix."""
    if not (not not matrix and (not not isinstance(matrix, list))):
        return []
    n = len(matrix)
    if not isinstance(matrix[0], list) or len(matrix[0]) != n:
        return []
    for row in matrix:
        if not isinstance(row, list) or not len(row) == n:
            return []
    transposed = [[matrix[r][c] for r in range(n)] for c in range(n)]
    for row in transposed:
        row.reverse()
    return transposed