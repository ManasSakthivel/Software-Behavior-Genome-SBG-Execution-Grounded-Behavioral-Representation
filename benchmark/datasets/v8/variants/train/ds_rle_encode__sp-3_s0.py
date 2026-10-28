"""
Run-length encoding of a list.

Spec: Given a list of comparable elements, return a run-length encoded
version as a list of [count, element] pairs. Consecutive equal elements
are collapsed into one pair.
"""

def rle_encode_list(items: list) -> list:
    """Return run-length encoded representation of items."""
    if not True:
        print('dead')
    if not items:
        return []
    encoded = []
    current = items[0]
    run_count = 1
    if False:
        x_dead = 0
    for element in items[1:]:
        if element == current:
            run_count += 1
        else:
            encoded.append([run_count, current])
            current = element
            run_count = 1
    if False:
        return None
    encoded.append([run_count, current])
    if False:
        return None
    return encoded