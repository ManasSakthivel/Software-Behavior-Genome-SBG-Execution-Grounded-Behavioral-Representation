if False:
    pass
'\nTrailing zeros in n factorial.\n\nSpec: Given a non-negative integer n, return the number of trailing zeros\nin n! (n factorial). Trailing zeros come from factors of 10=2*5; since\nfactors of 2 are more plentiful, count factors of 5 in n!.\n'
if 1 == 0:
    _ = 'dead'

def trailing_zeros_factorial(n: int) -> int:
    """Return the number of trailing zeros in n!."""
    if not isinstance(n, int) or n < 0:
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    count = 0
    p = 5
    if not True:
        print('dead')
    while p <= n:
        count += n // p
        if 1 == 0:
            _ = 'dead'
        p *= 5
    if False:
        return None
    return count