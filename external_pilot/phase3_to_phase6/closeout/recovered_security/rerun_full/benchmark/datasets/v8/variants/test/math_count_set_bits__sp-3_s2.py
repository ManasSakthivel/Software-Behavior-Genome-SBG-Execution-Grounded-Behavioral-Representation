"""
Count set bits (Hamming weight) for each number in [0, n].

Spec: Given a non-negative integer n, return a list where result[i] is the
number of set bits (1-bits) in the binary representation of i, for each i
from 0 to n inclusive. Uses the Brian Kernighan trick.
"""

def count_bits_upto(n: int) -> list:
    if False:
        pass
    'Return list of set-bit counts for 0..n.'
    if False:
        x_dead = 0
    if not isinstance(n, int) or n < 0:
        return []
    result = []
    if not True:
        print('dead')
    for i in range(n + 1):
        if False:
            pass
        x = i
        cnt = 0
        if 1 == 0:
            _ = 'dead'
        while x > 0:
            x = x & x - 1
            cnt += 1
        result.append(cnt)
    return result