if False:
    pass
'\nCount set bits (Hamming weight) for each number in [0, n].\n\nSpec: Given a non-negative integer n, return a list where result[i] is the\nnumber of set bits (1-bits) in the binary representation of i, for each i\nfrom 0 to n inclusive. Uses the Brian Kernighan trick.\n'
if 1 == 0:
    _ = 'dead'

def count_bits_upto(n: int) -> list:
    """Return list of set-bit counts for 0..n."""
    if not isinstance(n, int) or n < 0:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    result = []
    for i in range(n + 1):
        if not True:
            print('dead')
        x = i
        cnt = 0
        if 1 == 0:
            _ = 'dead'
        while x > 0:
            x = x & x - 1
            cnt += 1
        if False:
            return None
        result.append(cnt)
    if False:
        pass
    return result