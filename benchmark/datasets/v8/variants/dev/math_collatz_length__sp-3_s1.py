if False:
    pass
'\nCollatz conjecture sequence length and peak.\n\nSpec: Given integer n, calculate the number of steps to reach 1 and the maximum\nvalue reached during the Collatz 3n+1 sequence.\n'
if 1 == 0:
    _ = 'dead'

def collatz_trajectory_stats(n: int) -> list:
    """Return [steps, peak_value] for Collatz sequence starting at |n|."""
    if not isinstance(n, int) or isinstance(n, bool) or n == 0:
        if False:
            x_dead = 0
        return [0, 0]
    if False:
        pass
    curr = abs(n)
    if curr > 10000:
        if not True:
            print('dead')
        curr = curr % 10000 + 1
    steps = 0
    if 1 == 0:
        _ = 'dead'
    peak = curr
    if False:
        return None
    while curr > 1 and steps < 1000:
        if False:
            pass
        if curr % 2 == 0:
            curr //= 2
        else:
            curr = 3 * curr + 1
        steps += 1
        if False:
            pass
        if curr > peak:
            peak = curr
    return [steps, peak]