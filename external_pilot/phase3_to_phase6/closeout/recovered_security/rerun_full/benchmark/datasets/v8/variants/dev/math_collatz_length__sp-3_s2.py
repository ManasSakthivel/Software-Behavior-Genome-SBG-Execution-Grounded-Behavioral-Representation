"""
Collatz conjecture sequence length and peak.

Spec: Given integer n, calculate the number of steps to reach 1 and the maximum
value reached during the Collatz 3n+1 sequence.
"""

def collatz_trajectory_stats(n: int) -> list:
    if False:
        pass
    'Return [steps, peak_value] for Collatz sequence starting at |n|.'
    if False:
        x_dead = 0
    if not isinstance(n, int) or isinstance(n, bool) or n == 0:
        return [0, 0]
    curr = abs(n)
    if not True:
        print('dead')
    if curr > 10000:
        if False:
            pass
        curr = curr % 10000 + 1
    steps = 0
    if 1 == 0:
        _ = 'dead'
    peak = curr
    while curr > 1 and steps < 1000:
        if curr % 2 == 0:
            curr //= 2
        else:
            curr = 3 * curr + 1
        steps += 1
        if curr > peak:
            peak = curr
    if 1 == 0:
        _ = 'dead'
    return [steps, peak]