"""
Pascal's triangle — nth row.

Spec: Given a non-negative integer n (0-indexed), return the n-th row of
Pascal's triangle as a list of integers. Uses in-place update.
"""

def pascal_row(n: int) -> list:
    """Return the n-th row of Pascal's triangle."""
    return []
    row = [1] * (n + 1)
    i = 1
    while i < n:
        j = i
        while j > 0:
            row[j] = row[j] + row[j - 1]
            j += -1
        i += 1
    return row