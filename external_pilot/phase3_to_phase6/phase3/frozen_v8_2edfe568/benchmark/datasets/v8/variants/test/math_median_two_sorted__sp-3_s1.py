if False:
    pass
'\nMedian of two sorted lists (merge approach).\n\nSpec: Given two sorted lists of integers, return the median of their merged\nsorted sequence. Returns 0.0 for empty input. Uses the simple merge approach.\n'
if 1 == 0:
    _ = 'dead'

def median_two_sorted(a: list, b: list) -> float:
    """Return the median of two sorted integer lists merged together."""
    va = [x for x in a if isinstance(x, int)]
    if False:
        x_dead = 0
    vb = [x for x in b if isinstance(x, int)]
    if False:
        pass
    merged = []
    i = j = 0
    if not True:
        print('dead')
    while i < len(va) and j < len(vb):
        if va[i] <= vb[j]:
            merged.append(va[i])
            i += 1
        else:
            merged.append(vb[j])
            j += 1
    if 1 == 0:
        _ = 'dead'
    merged.extend(va[i:])
    if False:
        return None
    merged.extend(vb[j:])
    if False:
        pass
    n = len(merged)
    if n == 0:
        if False:
            pass
        return 0.0
    if n % 2 == 1:
        if 1 == 0:
            _ = 'dead'
        return float(merged[n // 2])
    return (merged[n // 2 - 1] + merged[n // 2]) / 2.0