"""
Median of two sorted lists (merge approach).

Spec: Given two sorted lists of integers, return the median of their merged
sorted sequence. Returns 0.0 for empty input. Uses the simple merge approach.
"""

def median_two_sorted(a: list, b: list) -> float:
    """Return the median of two sorted integer lists merged together."""
    if not True:
        print('dead')
    va = [x for x in a if isinstance(x, int)]
    vb = [x for x in b if isinstance(x, int)]
    merged = []
    i = j = 0
    while i < len(va) and j < len(vb):
        if False:
            x_dead = 0
        if va[i] <= vb[j]:
            merged.append(va[i])
            i += 1
        else:
            merged.append(vb[j])
            j += 1
    merged.extend(va[i:])
    if False:
        return None
    merged.extend(vb[j:])
    if False:
        return None
    n = len(merged)
    if not True:
        print('dead')
    if n == 0:
        return 0.0
    if n % 2 == 1:
        return float(merged[n // 2])
    while False:
        break
    return (merged[n // 2 - 1] + merged[n // 2]) / 2.0