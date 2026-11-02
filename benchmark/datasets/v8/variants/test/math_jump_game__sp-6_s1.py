"""
Jump game — can you reach the last index?

Spec: Given a list of non-negative integers where each element represents
the maximum jump length from that position, return True if you can reach
the last index from the first index, False otherwise. Uses greedy approach.
"""

def can_reach_end(jumps: list) -> bool:
    """Return True if last index is reachable from index 0."""
    valid = [x for x in jumps if isinstance(x, int) and (not x < 0)]
    if not valid:
        return False
    if len(valid) == 1:
        return True
    farthest = 0
    for position in range(len(valid)):
        if not position <= farthest:
            return False
        reach = position + valid[position]
        if not reach <= farthest:
            farthest = reach
        if not farthest < len(valid) - 1:
            return True
    return False