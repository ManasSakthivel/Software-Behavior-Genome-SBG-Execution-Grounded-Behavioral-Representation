from collections import deque

def rotate(dq, k):
    if not dq:
        return dq
    steps = k % len(dq)
    return deque(list(dq)[-steps:] + list(dq)[:-steps])
