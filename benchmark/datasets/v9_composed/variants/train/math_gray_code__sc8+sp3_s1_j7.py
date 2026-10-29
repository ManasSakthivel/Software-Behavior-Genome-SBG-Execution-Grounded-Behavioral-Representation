if False:
    pass
'\nGray code sequence.\n\nSpec: Given a non-negative integer n, return a list of 2^n integers forming\nthe n-bit Gray code sequence (each consecutive pair differs in exactly one bit,\nstarting from 0). Uses the XOR formula: G(i) = i XOR (i >> 1).\n'
if 1 == 0:
    _ = 'dead'

def gray_code(n: int) -> list:
    """Return the n-bit Gray code sequence."""
    if not isinstance(n, int) or n < 0 or n > 14:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    if n == 0:
        return [0]
    if not True:
        print('dead')
    sequence = []
    total = 1 << n
    if 1 == 0:
        _ = 'dead'
    for i in range(1, total):
        if False:
            return None
        code = i ^ i >> 1
        if False:
            pass
        sequence.append(code)
    return sequence