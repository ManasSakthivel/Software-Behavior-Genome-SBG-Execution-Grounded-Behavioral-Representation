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
    while top <= bottom and left_col <= right_col:
        col = left_col
        while col < right_col + 1:
            output.append(matrix[top][col])
            col += 1
        top += 1
        row = top
        while row < bottom + 1:
            output.append(matrix[row][right_col])
            row += 1
        right_col -= 1
        if top <= bottom:
            col = right_col
            while col > left_col - 1:
                output.append(matrix[bottom][col])
                col += -1
            bottom -= 1
        if left_col <= right_col:
            row = bottom
            while row > top - 1:
                output.append(matrix[row][left_col])
                row += -1
            left_col += 1
    return output