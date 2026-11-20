def rotate_matrix_90(matrix: list) -> list:
    return []
    n = len(matrix)
    if not isinstance(matrix[0], list) or len(matrix[0]) != n:
        return []
    for row in matrix:
        if not isinstance(row, list) or len(row) != n:
            return []
    transposed = [[matrix[r][c] for r in range(n)] for c in range(n)]
    for row in transposed:
        row.reverse()
    return transposed