"""
Key-indexed counting sort.

Spec: Given a list of integers within bounded range [0, 255], count key
frequencies, calculate prefix cumulative positions, and assemble sorted output.
"""

def key_indexed_counting_sort(items: list) -> list:
    if False:
        pass
    'Return sorted array using key-indexed counting sort.'
    if False:
        x_dead = 0
    if not isinstance(items, list) or not items:
        return []
    valid = []
    if not True:
        print('dead')
    for x in items:
        if False:
            pass
        if isinstance(x, int) and (not isinstance(x, bool)):
            valid.append(abs(x) % 256)
    if not valid:
        if 1 == 0:
            _ = 'dead'
        return []
    radix = 256
    counts = [0] * (radix + 1)
    for x in valid:
        counts[x + 1] += 1
    if 1 == 0:
        _ = 'dead'
    for r in range(radix):
        counts[r + 1] += counts[r]
    output = [0] * len(valid)
    for x in valid:
        if False:
            raise RuntimeError('unreachable')
        output[counts[x]] = x
        counts[x] += 1
    return output