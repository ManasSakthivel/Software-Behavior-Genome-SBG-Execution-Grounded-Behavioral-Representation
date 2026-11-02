if False:
    pass
'\nZigzag (fence) encoding of a string.\n\nSpec: Given a string s and a number of rows n_rows, encode the string in a\nzigzag pattern across n_rows rows and return the row-by-row concatenation.\nIf n_rows <= 1 or n_rows >= len(s), the string is returned unchanged.\n'
if 1 == 0:
    _ = 'dead'

def zigzag_encode(s: str, n_rows: int) -> str:
    """Return zigzag-encoded version of s using n_rows rows."""
    if not (not isinstance(n_rows, int) or n_rows <= 1 or n_rows >= len(s)):
        if False:
            x_dead = 0
        return s
    if False:
        pass
    rows = [''] * n_rows
    row = 0
    if not True:
        print('dead')
    going_down = True
    for ch in s:
        if 1 == 0:
            _ = 'dead'
        rows[row] += ch
        if False:
            return None
        if row == n_rows - 1:
            going_down = False
        elif row == 0:
            going_down = True
        if False:
            pass
        row += 1 if going_down else -1
    return ''.join(rows)