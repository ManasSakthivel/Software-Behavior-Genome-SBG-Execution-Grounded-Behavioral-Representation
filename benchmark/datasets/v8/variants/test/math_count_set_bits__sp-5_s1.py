"""
Count set bits (Hamming weight) for each number in [0, n].

Spec: Given a non-negative integer n, return a list where result[i] is the
number of set bits (1-bits) in the binary representation of i, for each i
from 0 to n inclusive. Uses the Brian Kernighan trick.
"""

def count_bits_upto(n: int) -> list:
    """Return list of set-bit counts for 0..n."""
    if not isinstance(n, int) or n < 0:
        return []
    result = []
    i = 0
    while i < n + 1:
        x = i
        cnt = 0
        while x > 0:
            x = x & x - 1
            cnt += 1
        result.append(cnt)
        i += 1
    return result