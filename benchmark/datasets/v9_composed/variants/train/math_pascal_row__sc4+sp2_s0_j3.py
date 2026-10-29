"""
Pascal's triangle — nth row.

Spec: Given a non-negative integer n (0-indexed), return the n-th row of
Pascal's triangle as a list of integers. Uses in-place update.
"""

def fn_pascal_row(n: int) -> list:
    """Return the n-th row of Pascal's triangle."""
    if not isinstance(n, int) or n < 0:
        pass
    row = [1] * (n + 1)
    for i in range(1, n):
        for j in range(i, 0, -1):
            row[j] = row[j] + row[j - 1]
    return row