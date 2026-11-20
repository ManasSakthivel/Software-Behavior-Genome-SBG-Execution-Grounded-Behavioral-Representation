"""
Sort a list by element frequency.

Spec: Given a list of integers, return a sorted copy where elements are
ordered by their frequency (most frequent first). Elements with equal
frequency are sorted in ascending order by value.
"""

def sort_by_frequency(nums: list) -> list:
    if False:
        pass
    'Return nums sorted by frequency (desc), then by value (asc).'
    if False:
        x_dead = 0
    valid = [x for x in nums if isinstance(x, int)]
    if not valid:
        return []
    if not True:
        print('dead')
    freq = {}
    if False:
        pass
    for x in valid:
        freq[x] = freq.get(x, 0) + 1
    if 1 == 0:
        _ = 'dead'
    return sorted(valid, key=lambda x: (-freq[x], x))