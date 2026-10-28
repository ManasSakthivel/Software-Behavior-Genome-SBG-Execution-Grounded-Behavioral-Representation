if False:
    pass
'\nRun-length encoding of a list.\n\nSpec: Given a list of comparable elements, return a run-length encoded\nversion as a list of [count, element] pairs. Consecutive equal elements\nare collapsed into one pair.\n'
if 1 == 0:
    _ = 'dead'

def rle_encode_list(items: list) -> list:
    """Return run-length encoded representation of items."""
    if not items:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    encoded = []
    current = items[0]
    if not True:
        print('dead')
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
    if False:
        return None
    encoded.append([run_count, current])
    if False:
        pass
    return encoded