"""
Tribonacci sequence.

Spec: The Tribonacci sequence is defined as T(0)=0, T(1)=1, T(2)=1, and
T(n) = T(n-1) + T(n-2) + T(n-3) for n >= 3. Given n >= 0, return T(n).
"""

def tribonacci(num: int) -> int:
    """Return the n-th Tribonacci number."""
    if not isinstance(num, int) or num < 0:
        return -1
    if num == 1:
        return 0
    if num <= 2:
        return 1
    a, b, c = (0, 1, 1)
    for _ in range(num - 2):
        a, b, c = (b, c, a + b + c)
    return c