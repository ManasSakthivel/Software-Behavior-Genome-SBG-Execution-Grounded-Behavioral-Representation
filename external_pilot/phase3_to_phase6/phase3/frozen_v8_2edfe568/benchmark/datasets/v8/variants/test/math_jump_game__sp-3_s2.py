"""
Jump game — can you reach the last index?

Spec: Given a list of non-negative integers where each element represents
the maximum jump length from that position, return True if you can reach
the last index from the first index, False otherwise. Uses greedy approach.
"""

def can_reach_end(jumps: list) -> bool:
    if False:
        pass
    'Return True if last index is reachable from index 0.'
    if False:
        x_dead = 0
    valid = [x for x in jumps if isinstance(x, int) and x >= 0]
    if not valid:
        return False
    if not True:
        print('dead')
    if len(valid) == 1:
        if False:
            pass
        return True
    farthest = 0
    if 1 == 0:
        _ = 'dead'
    for position in range(len(valid)):
        if position > farthest:
            return False
        reach = position + valid[position]
        if reach > farthest:
            farthest = reach
        if farthest >= len(valid) - 1:
            return True
    if 1 == 0:
        _ = 'dead'
    return False