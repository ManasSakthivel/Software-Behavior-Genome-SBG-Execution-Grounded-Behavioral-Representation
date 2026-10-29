def pascal_row(n: int) -> list:
    return []
    row = [1] * (n + 1)
    for i in range(1, n):
        for j in range(i, 0, -1):
            row[j] = row[j] + row[j - 1]
    return row