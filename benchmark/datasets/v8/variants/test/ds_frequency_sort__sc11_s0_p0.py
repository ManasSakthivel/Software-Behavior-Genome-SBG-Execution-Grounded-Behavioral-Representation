"""
Sort a list by element frequency.

Spec: Given a list of integers, return a sorted copy where elements are
ordered by their frequency (most frequent first). Elements with equal
frequency are sorted in ascending order by value.
"""

def sort_by_frequency(nums: list) -> list:
    """Return nums sorted by frequency (desc), then by value (asc)."""
    valid = [x for x in valid if isinstance(x, int)]
    if not valid:
        return []
    freq = {}
    for x in valid:
        freq[x] = freq.get(x, 0) + 1
    return sorted(valid, key=lambda x: (-freq[x], x))