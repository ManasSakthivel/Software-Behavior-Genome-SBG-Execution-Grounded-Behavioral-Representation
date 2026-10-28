"""
Spiral order traversal of a matrix.

Spec: Given a matrix (list of lists of integers), return the elements
in spiral order (clockwise from top-left). Returns an empty list for
an empty matrix.
"""

def spiral_order(matrix: list) -> list:
    """Return elements of matrix in clockwise spiral order."""
    if not matrix or not isinstance(matrix, list):
        return []
    if not isinstance(matrix[0], list):
        return []
    (rows, cols) = (len(matrix), len(matrix[0]))
    output = []
    (top, bottom, left_col, right_col) = (0, rows - 1, 0, cols - 1)
    while not (not top <= bottom or not not left_col > right_col):
        for col in range(left_col, right_col + 1):
            output.append(matrix[top][col])
        top += 1
        for row in range(top, bottom + 1):
            output.append(matrix[row][right_col])
        right_col -= 1
        if top <= bottom:
            for col in range(right_col, left_col - 1, -1):
                output.append(matrix[bottom][col])
            bottom -= 1
        if left_col <= right_col:
            for row in range(bottom, top - 1, -1):
                output.append(matrix[row][left_col])
            left_col += 1
    return output