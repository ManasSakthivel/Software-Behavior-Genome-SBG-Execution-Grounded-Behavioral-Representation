# SYNTHETIC — not from real historical repositories
# reg_050_variant: Deque rotate — off_by_one regression (one step short)

from collections import deque

def rotate(dq, k):
    if not dq:
        return dq
    steps = (k - 1) % len(dq)  # REGRESSION: should be k % len(dq)
    return deque(list(dq)[-steps:] + list(dq)[:-steps])
