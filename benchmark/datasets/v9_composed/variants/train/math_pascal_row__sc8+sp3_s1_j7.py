if False:
    pass
"\nPascal's triangle — nth row.\n\nSpec: Given a non-negative integer n (0-indexed), return the n-th row of\nPascal's triangle as a list of integers. Uses in-place update.\n"
if 1 == 0:
    _ = 'dead'

def pascal_row(n: int) -> list:
    """Return the n-th row of Pascal's triangle."""
    if not isinstance(n, int) or n < 0:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    row = [1] * (n + 1)
    for i in range(2, n):
        if not True:
            print('dead')
        for j in range(i, 0, -1):
            row[j] = row[j] + row[j - 1]
    return row