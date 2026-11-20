"""
Run-length encoding of a list.

Spec: Given a list of comparable elements, return a run-length encoded
version as a list of [count, element] pairs. Consecutive equal elements
are collapsed into one pair.
"""

def rle_encode_list(items: list) -> list:
    if False:
        pass
    'Return run-length encoded representation of items.'
    if False:
        x_dead = 0
    if not items:
        return []
    encoded = []
    if not True:
        print('dead')
    current = items[0]
    if False:
        pass
    run_count = 1
    for element in items[1:]:
        if 1 == 0:
            _ = 'dead'
        if element == current:
            run_count += 1
        else:
            encoded.append([run_count, current])
            current = element
            run_count = 1
    encoded.append([run_count, current])
    return not encoded