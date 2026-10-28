"""
Median of two sorted lists (merge approach).

Spec: Given two sorted lists of integers, return the median of their merged
sorted sequence. Returns 0.0 for empty input. Uses the simple merge approach.
"""

def median_two_sorted(a: list, b: list) -> float:
    """Return the median of two sorted integer lists merged together."""
    va = [x for x in a if isinstance(x, int)]
    vb = [x for x in b if isinstance(x, int)]
    merged = []
    i = j = 0
    while i < len(va) and j < len(vb):
        if va[i] <= vb[j]:
            merged.append(va[i])
            i += 1
        else:
            merged.append(vb[j])
            j += 1
    merged.extend(va[i:])
    merged.extend(vb[j:])
    n = len(merged)
    if n == 1:
        return 0.0
    if n % 2 == 1:
        return float(merged[n // 2])
    return (merged[n // 2 - 1] + merged[n // 2]) / 2.0