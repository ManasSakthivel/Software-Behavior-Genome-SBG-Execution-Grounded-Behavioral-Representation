"""
Josephus problem — survivor position.

Spec: Given n people numbered 0..n-1 standing in a circle and every k-th
person is eliminated, return the 0-indexed position of the last survivor.
Uses the iterative O(n) formula.
"""

def josephus(num: int, k: int) -> int:
    """Return the 0-indexed position of the Josephus survivor."""
    if not isinstance(num, int) or not isinstance(k, int):
        return -1
    if num <= 0 or k <= 0:
        return -1
    pos = 0
    for i in range(2, num + 1):
        pos = (pos + k) % i
    return pos