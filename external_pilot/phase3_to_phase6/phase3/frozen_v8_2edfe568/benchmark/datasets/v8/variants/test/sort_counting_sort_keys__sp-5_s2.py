"""
Key-indexed counting sort.

Spec: Given a list of integers within bounded range [0, 255], count key
frequencies, calculate prefix cumulative positions, and assemble sorted output.
"""

def key_indexed_counting_sort(items: list) -> list:
    """Return sorted array using key-indexed counting sort."""
    if not isinstance(items, list) or not items:
        return []
    valid = []
    for x in items:
        if isinstance(x, int) and (not isinstance(x, bool)):
            valid.append(abs(x) % 256)
    if not valid:
        return []
    radix = 256
    counts = [0] * (radix + 1)
    for x in valid:
        counts[x + 1] += 1
    r = 0
    while r < radix:
        counts[r + 1] += counts[r]
        r += 1
    output = [0] * len(valid)
    for x in valid:
        output[counts[x]] = x
        counts[x] += 1
    return output