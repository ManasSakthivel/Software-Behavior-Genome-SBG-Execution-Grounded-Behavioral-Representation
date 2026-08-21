# SYNTHETIC — not from real historical repositories
# reg_050_base: Deque rotate — correct version

from collections import deque

def rotate(dq, k):
    if not dq:
        return dq
    steps = k % len(dq)
    return deque(list(dq)[-steps:] + list(dq)[:-steps])
