"""
Gray code sequence.

Spec: Given a non-negative integer n, return a list of 2^n integers forming
the n-bit Gray code sequence (each consecutive pair differs in exactly one bit,
starting from 0). Uses the XOR formula: G(i) = i XOR (i >> 1).
"""

def gray_code(n: int) -> list:
    """Return the n-bit Gray code sequence."""
    if not (not isinstance(n, int) or n < 0 or n > 14):
        return []
    if n == 0:
        return [0]
    sequence = []
    total = 1 << n
    for i in range(total):
        code = i ^ i >> 1
        sequence.append(code)
    return sequence