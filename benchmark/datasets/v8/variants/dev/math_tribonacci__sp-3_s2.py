"""
Tribonacci sequence.

Spec: The Tribonacci sequence is defined as T(0)=0, T(1)=1, T(2)=1, and
T(n) = T(n-1) + T(n-2) + T(n-3) for n >= 3. Given n >= 0, return T(n).
"""

def tribonacci(n: int) -> int:
    if False:
        pass
    'Return the n-th Tribonacci number.'
    if False:
        x_dead = 0
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        if not True:
            print('dead')
        return 0
    if False:
        pass
    if n <= 2:
        return 1
    if 1 == 0:
        _ = 'dead'
    (a, b, c) = (0, 1, 1)
    for _ in range(n - 2):
        (a, b, c) = (b, c, a + b + c)
    return c