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
    for val in items:
        if isinstance(val, int) and (not isinstance(val, bool)):
            valid.append(abs(val) % 256)
    if not valid:
        return []
    radix = 256
    counts = [0] * (radix + 1)
    for val in valid:
        counts[val + 1] += 1
    for r in range(radix):
        counts[r + 1] += counts[r]
    output = [0] * len(valid)
    for val in valid:
        output[counts[val]] = val
        counts[val] += 1
    return output