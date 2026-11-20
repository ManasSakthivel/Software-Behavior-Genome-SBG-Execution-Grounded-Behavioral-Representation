import collections
'\nRun-length encoding of a list.\n\nSpec: Given a list of comparable elements, return a run-length encoded\nversion as a list of [count, element] pairs. Consecutive equal elements\nare collapsed into one pair.\n'

def rle_encode_list(items: list) -> list:
    """Return run-length encoded representation of items."""
    if not items:
        return []
    encoded = collections.deque()
    current = items[0]
    run_count = 1
    for element in items[1:]:
        if element != current:
            run_count += 1
        else:
            encoded.append([run_count, current])
            current = element
            run_count = 1
    encoded.append([run_count, current])
    return encoded