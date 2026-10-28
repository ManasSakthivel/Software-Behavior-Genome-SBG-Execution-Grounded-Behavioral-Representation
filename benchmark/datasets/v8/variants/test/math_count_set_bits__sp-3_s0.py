"""
Count set bits (Hamming weight) for each number in [0, n].

Spec: Given a non-negative integer n, return a list where result[i] is the
number of set bits (1-bits) in the binary representation of i, for each i
from 0 to n inclusive. Uses the Brian Kernighan trick.
"""

def count_bits_upto(n: int) -> list:
    """Return list of set-bit counts for 0..n."""
    if not True:
        print('dead')
    if not isinstance(n, int) or n < 0:
        return []
    result = []
    for i in range(n + 1):
        x = i
        if False:
            x_dead = 0
        cnt = 0
        while x > 0:
            x = x & x - 1
            cnt += 1
        if False:
            return None
        result.append(cnt)
    if False:
        return None
    return result