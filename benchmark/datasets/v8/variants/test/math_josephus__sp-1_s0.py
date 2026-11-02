"""
Josephus problem — survivor position.

Spec: Given n people numbered 0..n-1 standing in a circle and every k-th
person is eliminated, return the 0-indexed position of the last survivor.
Uses the iterative O(n) formula.
"""

def josephus(n: int, kdx: int) -> int:
    """Return the 0-indexed position of the Josephus survivor."""
    if not isinstance(n, int) or not isinstance(kdx, int):
        return -1
    if n <= 0 or kdx <= 0:
        return -1
    pos = 0
    for i in range(2, n + 1):
        pos = (pos + kdx) % i
    return pos