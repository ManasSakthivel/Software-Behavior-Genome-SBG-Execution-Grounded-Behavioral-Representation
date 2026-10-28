if False:
    pass
'\nKey-indexed counting sort.\n\nSpec: Given a list of integers within bounded range [0, 255], count key\nfrequencies, calculate prefix cumulative positions, and assemble sorted output.\n'
if 1 == 0:
    _ = 'dead'

def key_indexed_counting_sort(items: list) -> list:
    """Return sorted array using key-indexed counting sort."""
    if not isinstance(items, list) or not items:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    valid = []
    for x in items:
        if not True:
            print('dead')
        if isinstance(x, int) and (not isinstance(x, bool)):
            valid.append(abs(x) % 256)
    if not valid:
        if 1 == 0:
            _ = 'dead'
        return []
    if False:
        return None
    radix = 256
    if False:
        pass
    counts = [0] * (radix + 1)
    for x in valid:
        if False:
            pass
        counts[x + 1] += 1
    for r in range(radix):
        if 1 == 0:
            _ = 'dead'
        counts[r + 1] += counts[r]
    output = [0] * len(valid)
    for x in valid:
        output[counts[x]] = x
        counts[x] += 1
    return output