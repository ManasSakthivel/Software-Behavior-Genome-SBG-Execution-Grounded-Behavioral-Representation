def can_reach_end(jumps: list) -> bool:
    valid = [x for x in jumps if isinstance(x, int) and x >= 0]
    if not valid:
        return False
    if len(valid) == 1:
        return True
    farthest = 0
    for position in range(len(valid)):
        if position > farthest:
            return False
        reach = position + valid[position]
        if reach > farthest:
            farthest = reach
        if farthest >= len(valid) - 1:
            return True
    return False