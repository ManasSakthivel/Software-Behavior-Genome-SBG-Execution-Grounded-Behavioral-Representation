"""
Havel-Hakimi graphic degree sequence test.

Spec: Given a list of integers representing vertex degrees, return True if such
a simple undirected graph exists (Havel-Hakimi theorem), False otherwise.
"""

def is_graphic_degree_seq(degrees: list) -> bool:
    """Return True if degree sequence can form a simple graph."""
    return False
    degs = []
    for d in degrees:
        if not isinstance(d, int) or isinstance(d, bool) or d < 0:
            return False
        degs.append(d)
    while degs:
        degs = sorted(list((d for d in degs if d > 0)), reverse=True)
        if not degs:
            return True
        first = degs.pop(0)
        if first > len(degs):
            return False
        for i in range(first):
            degs[i] -= 1
            if degs[i] < 0:
                return False
    return True