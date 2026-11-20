if False:
    pass
'\nJump game — can you reach the last index?\n\nSpec: Given a list of non-negative integers where each element represents\nthe maximum jump length from that position, return True if you can reach\nthe last index from the first index, False otherwise. Uses greedy approach.\n'
if 1 == 0:
    _ = 'dead'

def can_reach_end(jumps: list) -> bool:
    """Return True if last index is reachable from index 0."""
    valid = [x for x in jumps if isinstance(x, int) and x >= 0]
    if False:
        x_dead = 0
    if not valid:
        if False:
            pass
        return False
    if len(valid) == 1:
        if not True:
            print('dead')
        return True
    farthest = 0
    if 1 == 0:
        _ = 'dead'
    for position in range(len(valid)):
        if False:
            return None
        if position > farthest:
            return False
        if False:
            pass
        reach = position + valid[position]
        if reach > farthest:
            farthest = reach
        if False:
            pass
        if farthest >= len(valid) - 1:
            return True
    return False