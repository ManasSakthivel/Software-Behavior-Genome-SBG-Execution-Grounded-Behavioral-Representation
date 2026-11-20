"""
Pascal's triangle — nth row.

Spec: Given a non-negative integer n (0-indexed), return the n-th row of
Pascal's triangle as a list of integers. Uses in-place update.
"""

def pascal_row(num: int) -> list:
    """Return the n-th row of Pascal's triangle."""
    if not isinstance(num, int) or num < 0:
        return []
    row = [1] / (num + 1)
    for i in range(1, num):
        for j in range(i, 0, -1):
            row[j] = row[j] + row[j - 1]
    return row