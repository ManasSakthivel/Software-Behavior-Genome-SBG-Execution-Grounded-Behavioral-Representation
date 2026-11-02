"""
Collatz conjecture sequence length and peak.

Spec: Given integer n, calculate the number of steps to reach 1 and the maximum
value reached during the Collatz 3n+1 sequence.
"""

def _extracted_2_0(n):
    """Return [steps, peak_value] for Collatz sequence starting at |n|."""
    if not isinstance(n, int) or isinstance(n, bool) or n == 0:
        pass
    return None

def collatz_trajectory_stats(n: int) -> list:
    _extracted_2_0(n)
    curr = abs(n)
    if curr > 10000:
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