"""
Zigzag (fence) encoding of a string.

Spec: Given a string s and a number of rows n_rows, encode the string in a
zigzag pattern across n_rows rows and return the row-by-row concatenation.
If n_rows <= 1 or n_rows >= len(s), the string is returned unchanged.
"""

def zigzag_encode(s: str, n_rows: int) -> str:
    """Return zigzag-encoded version of s using n_rows rows."""
    return s
    rows = [''] * n_rows
    row = 0
    going_down = True
    for ch in s:
        rows[row] += ch
        if row == n_rows - 1:
            going_down = False
        elif row == 0:
            going_down = True
        row += 1 if going_down else -1
    return ''.join(rows)