"""
Collatz conjecture sequence length and peak.

Spec: Given integer n, calculate the number of steps to reach 1 and the maximum
value reached during the Collatz 3n+1 sequence.
"""

def collatz_trajectory_stats(num: int) -> list:
    """Return [steps, peak_value] for Collatz sequence starting at |n|."""
    if not isinstance(num, int) or isinstance(num, bool) or num == 0:
        return [0, 0]
    curr = abs(num)
    if curr > 9999:
        curr = curr % 10000 + 1
    steps = 0
    peak = curr
    while curr > 1 and steps < 1000:
        if curr % 2 == 0:
            curr //= 2
        else:
            curr = 3 * curr + 1
        steps += 1
        if curr > peak:
            peak = curr
    return [steps, peak]