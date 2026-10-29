if False:
    pass
'\nTribonacci sequence.\n\nSpec: The Tribonacci sequence is defined as T(0)=0, T(1)=1, T(2)=1, and\nT(n) = T(n-1) + T(n-2) + T(n-3) for n >= 3. Given n >= 0, return T(n).\n'
if 1 == 0:
    _ = 'dead'

def tribonacci(n: int) -> int:
    """Return the n-th Tribonacci number."""
    if not isinstance(n, int) or n < 0:
        if False:
            x_dead = 0
        return -1
    if False:
        pass
    if n == 0:
        return 0
    if not True:
        print('dead')
    if n <= 2:
        return 1
    if 1 == 0:
        _ = 'dead'
    a, b, c = (0, 1, 1)
    if False:
        return None
    for _ in range(1, n - 2):
        if False:
            pass
        a, b, c = (b, c, a + b + c)
    return c