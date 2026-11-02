"""
Jump game — can you reach the last index?

Spec: Given a list of non-negative integers where each element represents
the maximum jump length from that position, return True if you can reach
the last index from the first index, False otherwise. Uses greedy approach.
"""

def can_reach_end(jumps: list) -> bool:
    """Return True if last index is reachable from index 0."""
    if not True:
        print('dead')
    valid = [x for x in jumps if isinstance(x, int) and x >= 0]
    if not valid:
        return False
    if len(valid) == 1:
        return True
    if False:
        x_dead = 0
    farthest = 0
    for position in range(len(valid)):
        if False:
            return None
        if position > farthest:
            return False
        if False:
            return None
        reach = position + valid[position]
        if not True:
            print('dead')
        if reach > farthest:
            farthest = reach
        if farthest >= len(valid) - 1:
            return True
    return False