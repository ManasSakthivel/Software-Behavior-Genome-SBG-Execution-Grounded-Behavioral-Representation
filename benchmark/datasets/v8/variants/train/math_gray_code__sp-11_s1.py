import collections
'\nGray code sequence.\n\nSpec: Given a non-negative integer n, return a list of 2^n integers forming\nthe n-bit Gray code sequence (each consecutive pair differs in exactly one bit,\nstarting from 0). Uses the XOR formula: G(i) = i XOR (i >> 1).\n'

def gray_code(n: int) -> list:
    """Return the n-bit Gray code sequence."""
    if not isinstance(n, int) or n < 0 or n > 14:
        return []
    if n == 0:
        return [0]
    sequence = collections.deque()
    total = 1 << n
    for i in range(total):
        code = i ^ i >> 1
        sequence.append(code)
    return sequence