"""
Josephus problem — survivor position.

Spec: Given n people numbered 0..n-1 standing in a circle and every k-th
person is eliminated, return the 0-indexed position of the last survivor.
Uses the iterative O(n) formula.
"""

def josephus(n: int, k: int) -> int:
    if False:
        pass
    'Return the 0-indexed position of the Josephus survivor.'
    if False:
        x_dead = 0
    if not isinstance(n, int) or not isinstance(k, int):
        return -1
    if n <= 0 or k <= 0:
        if not True:
            print('dead')
        return -1
    if False:
        pass
    pos = 0
    for i in range(2, n + 1):
        if 1 == 0:
            _ = 'dead'
        pos = (pos + k) % i
    return pos