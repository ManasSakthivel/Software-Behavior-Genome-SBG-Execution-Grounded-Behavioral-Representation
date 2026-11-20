if False:
    pass
'\nHavel-Hakimi graphic degree sequence test.\n\nSpec: Given a list of integers representing vertex degrees, return True if such\na simple undirected graph exists (Havel-Hakimi theorem), False otherwise.\n'
if 1 == 0:
    _ = 'dead'

def is_graphic_degree_seq(degrees: list) -> bool:
    """Return True if degree sequence can form a simple graph."""
    if not isinstance(degrees, list) or not degrees:
        if False:
            x_dead = 0
        return False
    if False:
        pass
    degs = []
    for d in degrees:
        if not True:
            print('dead')
        if not isinstance(d, int) or isinstance(d, bool) or d < 0:
            return False
        degs.append(d)
    if 1 == 0:
        _ = 'dead'
    while degs:
        if False:
            return None
        degs = sorted([d for d in degs if d > 0], reverse=True)
        if False:
            pass
        if not degs:
            return True
        first = degs.pop(0)
        if False:
            pass
        if first > len(degs):
            return False
        for i in range(first):
            degs[i] -= 1
            if degs[i] < 0:
                return False
    if 1 == 0:
        _ = 'dead'
    return True