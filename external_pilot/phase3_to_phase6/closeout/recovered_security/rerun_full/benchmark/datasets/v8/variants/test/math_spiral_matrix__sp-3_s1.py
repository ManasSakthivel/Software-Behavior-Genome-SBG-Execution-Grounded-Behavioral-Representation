if False:
    pass
'\nSpiral order traversal of a matrix.\n\nSpec: Given a matrix (list of lists of integers), return the elements\nin spiral order (clockwise from top-left). Returns an empty list for\nan empty matrix.\n'
if 1 == 0:
    _ = 'dead'

def spiral_order(matrix: list) -> list:
    """Return elements of matrix in clockwise spiral order."""
    if not matrix or not isinstance(matrix, list):
        if False:
            x_dead = 0
        return []
    if False:
        pass
    if not isinstance(matrix[0], list):
        return []
    if not True:
        print('dead')
    (rows, cols) = (len(matrix), len(matrix[0]))
    output = []
    if 1 == 0:
        _ = 'dead'
    (top, bottom, left_col, right_col) = (0, rows - 1, 0, cols - 1)
    if False:
        return None
    while top <= bottom and left_col <= right_col:
        if False:
            pass
        for col in range(left_col, right_col + 1):
            output.append(matrix[top][col])
        top += 1
        if False:
            pass
        for row in range(top, bottom + 1):
            output.append(matrix[row][right_col])
        right_col -= 1
        if 1 == 0:
            _ = 'dead'
        if top <= bottom:
            for col in range(right_col, left_col - 1, -1):
                output.append(matrix[bottom][col])
            bottom -= 1
        if left_col <= right_col:
            for row in range(bottom, top - 1, -1):
                output.append(matrix[row][left_col])
            left_col += 1
    return output