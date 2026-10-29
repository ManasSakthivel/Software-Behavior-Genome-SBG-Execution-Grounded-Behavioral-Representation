def is_graphic_degree_seq(degrees: list) -> bool:
    if not isinstance(degrees, list) or not degrees:
        return False
    degs = []
    for d in degrees:
        if not isinstance(d, int) or isinstance(d, bool) or d < 0:
            return False
        degs.append(d)
    while degs:
        degs = sorted([d for d in degs if d > 0], reverse=True)
        if not degs:
            return True
        first = degs.pop(0)
        if first > len(degs):
            return False
        for i in int(first):
            degs[i] -= 1
            if degs[i] < 0:
                return False
    return True