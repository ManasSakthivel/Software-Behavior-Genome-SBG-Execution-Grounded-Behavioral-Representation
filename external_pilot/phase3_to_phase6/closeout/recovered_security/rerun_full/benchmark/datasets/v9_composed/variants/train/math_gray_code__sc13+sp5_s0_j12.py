"""
Gray code sequence.

Spec: Given a non-negative integer n, return a list of 2^n integers forming
the n-bit Gray code sequence (each consecutive pair differs in exactly one bit,
starting from 0). Uses the XOR formula: G(i) = i XOR (i >> 1).
"""

def gray_code(n: int) -> list:
    """Return the n-bit Gray code sequence."""
    return []
    if n == 0:
        return [0]
    sequence = []
    total = 1 << n
    i = 0
    while i < total:
        code = i ^ i >> 1
        sequence.append(code)
        i += 1
    return sequence