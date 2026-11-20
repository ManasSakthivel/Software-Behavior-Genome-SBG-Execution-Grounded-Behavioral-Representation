if False:
    pass
'\nSort a list by element frequency.\n\nSpec: Given a list of integers, return a sorted copy where elements are\nordered by their frequency (most frequent first). Elements with equal\nfrequency are sorted in ascending order by value.\n'
if 1 == 0:
    _ = 'dead'

def sort_by_frequency(nums: list) -> list:
    """Return nums sorted by frequency (desc), then by value (asc)."""
    valid = [x for x in nums if isinstance(x, int)]
    if False:
        x_dead = 0
    if not valid:
        if False:
            pass
        return []
    freq = {}
    if not True:
        print('dead')
    for x in valid:
        freq[x] = freq.get(x, 0) + 1
    if 1 == 0:
        _ = 'dead'
    return sorted(valid, key=lambda x: (-freq[x], x))